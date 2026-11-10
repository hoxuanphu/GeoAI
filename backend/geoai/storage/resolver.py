"""Launch-scoped, in-memory metadata grants. No OS lock, file I/O or sandbox.

Caller must be the trusted coordinator, not a public request handler. Native
adapters still verify handles, bytes, ownership and transaction-time fencing.
All state transitions must be serialized by the coordinator.
"""
from dataclasses import dataclass
from hashlib import sha256
import re

from pydantic import ValidationError
from geoai.contracts import WorkerAccessContext, StartParams, JobSpec, InputSnapshot, AttemptKey


class GrantError(ValueError):
    """Stable sanitized failure; never interpolate private input values."""
    def __init__(self, code='invalid_input'):
        self.code = code
        super().__init__('Grant metadata rejected: ' + code)


@dataclass
class _Grant:
    context: bytes
    start: bytes
    job: bytes
    snapshot: bytes
    state: str = 'registered'


class GrantRegistry:
    """Private application metadata only; construction does not prove OS ownership."""
    def __init__(self, *, worker_id, launch_nonce, project_id, execution_owner_id, owner_epoch):
        self._identity = (worker_id, launch_nonce, project_id, execution_owner_id, owner_epoch)
        self._grants = {}
        self._candidates = {}
        self._used_attempts = set()
        self._used_tokens = set()
        self._active = None
        self._closed = False

    def register(self, *, context_bytes: bytes, job_bytes: bytes, snapshot_bytes: bytes,
                 expected_start: StartParams, required_ref_ids=()):
        """Snapshot exact coordinator bytes against independently trusted start intent."""
        try:
            if self._closed or self._active is not None:
                raise GrantError('stale_attempt')
            if not all(type(x) is bytes for x in (context_bytes, job_bytes, snapshot_bytes)):
                raise GrantError()
            start = StartParams.model_validate_json(expected_start.model_dump_json())
            c = WorkerAccessContext.model_validate_json(context_bytes)
            j = JobSpec.model_validate_json(job_bytes)
            s = InputSnapshot.model_validate_json(snapshot_bytes)
            attempt_id = (c.attempt.job_id, c.attempt.attempt_id)
            if c.access_context_id in self._grants or attempt_id in self._used_attempts or c.attempt.generation_token in self._used_tokens:
                raise GrantError('stale_attempt')
            if (c.worker_id,c.launch_nonce,c.project_id,c.execution_owner_id,c.owner_epoch) != self._identity:
                raise GrantError('stale_attempt')
            expected = StartParams(attempt=c.attempt,job_spec_id=c.job_spec_id,input_snapshot_id=c.input_snapshot_id,
                                   access_context_id=c.access_context_id,access_context_sha256=sha256(context_bytes).hexdigest(),resource_budget=c.resource_budget)
            if expected != start:
                raise GrantError()
            if (sha256(job_bytes).hexdigest(),sha256(snapshot_bytes).hexdigest()) != (c.job_spec_sha256,c.input_snapshot_sha256):
                raise GrantError()
            if (j.job_id,j.input_snapshot_id,j.project_id,j.grid_id,j.resource_budget) != (c.job_spec_id,c.input_snapshot_id,c.project_id,s.grid_id,c.resource_budget):
                raise GrantError()
            if (s.snapshot_id,s.project_id) != (c.input_snapshot_id,c.project_id):
                raise GrantError()
            refs = {e.ref_id:e for e in c.read_entries}
            for ref, data in ((j.job_id,job_bytes),(s.snapshot_id,snapshot_bytes)):
                if refs[ref].size_bytes != len(data):
                    raise GrantError()
            required = {j.job_id,s.snapshot_id,j.workflow_id,j.grid_id,s.qa_policy_id,*j.model_ids,*j.physical_model_ids,
                        *j.parameter_snapshot_ids,*s.asset_ids,*s.transform_ids,*s.dependency_ids,*required_ref_ids}
            if s.mosaic_recipe_id:
                required.add(s.mosaic_recipe_id)
            if not required.issubset(refs):
                raise GrantError('missing_resource')
            self._grants[c.access_context_id] = _Grant(context_bytes,start.model_dump_json().encode(),job_bytes,snapshot_bytes)
            self._active = c.access_context_id
            self._used_attempts.add(attempt_id)
            self._used_tokens.add(c.attempt.generation_token)
            return sha256(context_bytes).hexdigest()
        except (ValidationError,TypeError,AttributeError,KeyError):
            raise GrantError() from None

    def accept(self, start: StartParams):
        """Consume start exactly once; returns no filesystem authority."""
        try:
            start = StartParams.model_validate_json(start.model_dump_json())
            grant = self._grants.get(start.access_context_id)
            if self._closed or grant is None or self._active != start.access_context_id or grant.state != 'registered':
                raise GrantError('stale_attempt')
            if StartParams.model_validate_json(grant.start) != start:
                raise GrantError()
            grant.state = 'accepted'
        except (ValidationError,TypeError,AttributeError):
            raise GrantError() from None

    def _current(self, access_context_id, attempt):
        grant = self._grants.get(access_context_id)
        if self._closed or grant is None or self._active != access_context_id or grant.state != 'accepted':
            raise GrantError('stale_attempt')
        c = WorkerAccessContext.model_validate_json(grant.context)
        if c.attempt != attempt:
            raise GrantError('stale_attempt')
        return c

    def resolve(self, access_context_id: str, attempt: AttemptKey, ref_id: str):
        """Return a fresh allowlisted read entry, never open or concatenate paths."""
        c = self._current(access_context_id,attempt)
        for entry in c.read_entries:
            if entry.ref_id == ref_id:
                return entry
        raise GrantError('missing_resource')

    def revoke(self, access_context_id: str):
        grant = self._grants.get(access_context_id)
        if grant is None:
            raise GrantError('missing_resource')
        grant.state = 'revoked'
        if self._active == access_context_id:
            self._active = None

    def close(self):
        """End launch lifetime. Never deletes shared dependencies or any file bytes."""
        self._closed = True
        for grant in self._grants.values():
            grant.state = 'revoked'
        self._active = None

    def register_candidate(self, candidate_id, access_context_id, *, project_id, attempt, staging_id):
        """Coordinator-issued IDs only; worker event paths are never accepted."""
        c = self._current(access_context_id,attempt)
        if not isinstance(candidate_id,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,255}',candidate_id):
            raise GrantError()
        if candidate_id in self._candidates or (project_id,staging_id) != (c.project_id,c.staging_id):
            raise GrantError()
        self._candidates[candidate_id] = (access_context_id,project_id,c.attempt.model_dump_json(),staging_id)

    def check_candidate(self, candidate_id, access_context_id, *, project_id, attempt):
        c = self._current(access_context_id,attempt)
        expected = (access_context_id,project_id,c.attempt.model_dump_json(),c.staging_id)
        if project_id != c.project_id or self._candidates.get(candidate_id) != expected:
            raise GrantError()
        return c.staging_id
