"""Pure coordinator metadata transitions; no process, filesystem or DB authority.

The future repository must serialize each transition and recheck publication
conditions in a transaction. confirm_stopped is for a trusted native observer.
"""
from __future__ import annotations

import math
import secrets
from dataclasses import dataclass

from pydantic import TypeAdapter

from geoai.contracts import AttemptKey, JobSpec
from geoai.contracts.common import Identifier, PositiveInt
from geoai.storage.intents import INTENT_DIGEST_PROFILE, canonical_intent


_identifier = TypeAdapter(Identifier)
_epoch = TypeAdapter(PositiveInt)


class JobConflict(ValueError):
    pass


class JobStateError(ValueError):
    pass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    backoff_seconds: float

    def __post_init__(self):
        if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 100:
            raise ValueError("max_attempts must be in [1, 100]")
        if type(self.backoff_seconds) not in (int, float) or not math.isfinite(self.backoff_seconds) or not 0 <= self.backoff_seconds <= 86400:
            raise ValueError("invalid backoff_seconds")


@dataclass(frozen=True)
class CheckpointIdentity:
    input_sha256: str
    model_sha256: str
    config_sha256: str
    runtime_id: str
    grid_id: str

    def compatible_with(self, current: "CheckpointIdentity") -> bool:
        return type(current) is CheckpointIdentity and self == current


@dataclass(frozen=True)
class JobView:
    project_id: str
    job_id: str
    state: str
    intent_digest: str
    intent_bytes: bytes
    attempt: AttemptKey | None
    attempts_started: int
    compute_allocated: bool
    publication_id: str | None
    progress_units: int | None
    retained_dependencies: frozenset[str]
    candidate_manifest_id: str | None

    @property
    def job_spec(self) -> JobSpec:
        return JobSpec.model_validate_json(self.intent_bytes)


@dataclass
class _Job:
    intent: bytes
    digest: str
    idempotency_key: str
    state: str = "queued"
    attempt: AttemptKey | None = None
    attempts_started: int = 0
    owner_id: str | None = None
    owner_epoch: int | None = None
    compute_allocated: bool = False
    stop_confirmed: bool = True
    retry_pending: bool = False
    backoff_required: bool = False
    publication_id: str | None = None
    progress_units: int | None = None
    retained_dependencies: frozenset[str] = frozenset()
    candidate_manifest_id: str | None = None


class JobCoordinator:
    """Single-threaded metadata core. Caller owns synchronization and persistence."""

    def __init__(self, retry_policy: RetryPolicy):
        if not isinstance(retry_policy, RetryPolicy):
            raise TypeError("explicit RetryPolicy required")
        self.retry_policy = retry_policy
        self._jobs: dict[tuple[str, str], _Job] = {}
        self._requests: dict[tuple[str, str], tuple[str, str]] = {}
        self._publications: dict[tuple[str, str], str] = {}
        self._compute_job: tuple[str, str] | None = None

    def _record(self, project_id: str, job_id: str) -> _Job:
        _identifier.validate_python(project_id)
        _identifier.validate_python(job_id)
        try:
            return self._jobs[(project_id, job_id)]
        except KeyError:
            raise JobStateError("unknown job") from None

    def _view(self, project_id: str, job_id: str, record: _Job) -> JobView:
        return JobView(project_id, job_id, record.state, record.digest, record.intent,
                       AttemptKey.model_validate_json(record.attempt.model_dump_json()) if record.attempt else None,
                       record.attempts_started, record.compute_allocated, record.publication_id, record.progress_units, record.retained_dependencies, record.candidate_manifest_id)

    def get(self, project_id: str, job_id: str) -> JobView:
        return self._view(project_id, job_id, self._record(project_id, job_id))

    def enqueue(self, spec: JobSpec) -> JobView:
        raw, digest = canonical_intent(spec)
        intent = JobSpec.model_validate_json(raw)
        job_key = (intent.project_id, intent.job_id)
        request_key = (intent.project_id, intent.idempotency_key)
        existing_request = self._requests.get(request_key)
        if existing_request is not None:
            old = self._jobs[existing_request]
            if old.digest != digest or old.intent != raw:
                raise JobConflict("idempotency key conflicts with immutable intent")
            return self._view(*existing_request, old)
        if job_key in self._jobs:
            raise JobConflict("job ID already exists")
        record = _Job(raw, digest, intent.idempotency_key)
        self._jobs[job_key] = record
        self._requests[request_key] = job_key
        return self._view(*job_key, record)

    def claim(self, project_id: str, job_id: str, *, owner_id: str, owner_epoch: int,
              elapsed_backoff_seconds: float = 0) -> AttemptKey:
        _identifier.validate_python(owner_id)
        _epoch.validate_python(owner_epoch)
        r = self._record(project_id, job_id)
        if r.state != "queued" or not r.stop_confirmed or self._compute_job is not None or r.attempts_started >= self.retry_policy.max_attempts:
            raise JobStateError("job cannot be claimed")
        if type(elapsed_backoff_seconds) not in (int, float) or not math.isfinite(elapsed_backoff_seconds) or elapsed_backoff_seconds < 0:
            raise ValueError("invalid elapsed_backoff_seconds")
        if r.backoff_required and elapsed_backoff_seconds < self.retry_policy.backoff_seconds:
            raise JobStateError("retry backoff not elapsed")
        r.attempt = AttemptKey(job_id=job_id, attempt_id="attempt:" + secrets.token_hex(16), generation_token="generation:" + secrets.token_hex(32))
        r.attempts_started += 1
        r.owner_id, r.owner_epoch = owner_id, owner_epoch
        r.compute_allocated = True
        r.stop_confirmed = False
        r.backoff_required = False
        r.candidate_manifest_id = None
        r.progress_units = None
        r.state = "running"
        self._compute_job = (project_id, job_id)
        return AttemptKey.model_validate_json(r.attempt.model_dump_json())

    def _current(self, project_id: str, job_id: str, attempt: AttemptKey, owner_id: str, owner_epoch: int) -> _Job | None:
        _identifier.validate_python(owner_id)
        _epoch.validate_python(owner_epoch)
        key = AttemptKey.model_validate_json(attempt.model_dump_json())
        r = self._record(project_id, job_id)
        if key.job_id != job_id or r.attempt != key or r.owner_id != owner_id or r.owner_epoch != owner_epoch:
            return None
        return r

    def cancel(self, project_id: str, job_id: str) -> JobView:
        r = self._record(project_id, job_id)
        if r.state == "queued":
            r.state = "cancelled"
            r.retry_pending = False
        elif r.state in {"running", "failed"} and r.compute_allocated:
            r.state = "cancel_requested"
            r.retry_pending = False
        return self._view(project_id, job_id, r)

    def cancel_ack(self, project_id: str, job_id: str, attempt: AttemptKey, owner_id: str, owner_epoch: int) -> bool:
        r = self._current(project_id, job_id, attempt, owner_id, owner_epoch)
        return r is not None and r.state == "cancel_requested"

    def progress(self, project_id: str, job_id: str, attempt: AttemptKey, owner_id: str, owner_epoch: int, completed_units: int) -> bool:
        r = self._current(project_id, job_id, attempt, owner_id, owner_epoch)
        if r is None or r.state != "running":
            return False
        if type(completed_units) is not int or completed_units < 0:
            raise ValueError("invalid progress")
        r.progress_units = completed_units
        return True

    def candidate(self, project_id: str, job_id: str, attempt: AttemptKey, owner_id: str, owner_epoch: int, candidate_manifest_id: str) -> bool:
        """Record an event reference only; grant registry and publisher validate candidate bytes."""
        _identifier.validate_python(candidate_manifest_id)
        r = self._current(project_id, job_id, attempt, owner_id, owner_epoch)
        if r is None or r.state != "running":
            return False
        r.candidate_manifest_id = candidate_manifest_id
        return True

    def fail(self, project_id: str, job_id: str, attempt: AttemptKey, owner_id: str, owner_epoch: int, *, retryable: bool) -> JobView:
        r = self._current(project_id, job_id, attempt, owner_id, owner_epoch)
        if r is None or r.state not in {"running", "cancel_requested"} or type(retryable) is not bool:
            raise JobStateError("attempt cannot fail")
        cancelling = r.state == "cancel_requested"
        r.state = "cancel_requested" if cancelling else "failed"
        r.retry_pending = not cancelling and retryable and r.attempts_started < self.retry_policy.max_attempts
        return self._view(project_id, job_id, r)

    def confirm_stopped(self, project_id: str, job_id: str, attempt: AttemptKey, owner_id: str, owner_epoch: int) -> JobView:
        """Trusted observer confirmed process/group stopped; an ACK or timeout is insufficient."""
        r = self._current(project_id, job_id, attempt, owner_id, owner_epoch)
        if r is None or not r.compute_allocated:
            raise JobStateError("attempt is not allocated")
        r.compute_allocated = False
        r.stop_confirmed = True
        self._compute_job = None
        if r.state == "cancel_requested":
            r.state = "cancelled"
        elif r.state == "failed" and r.retry_pending:
            r.state = "queued"
            r.backoff_required = True
        elif r.state == "running":
            r.state = "failed"
        r.retry_pending = False
        return self._view(project_id, job_id, r)

    def publish(self, project_id: str, job_id: str, attempt: AttemptKey, owner_id: str, owner_epoch: int, publication_id: str) -> JobView:
        """Register already validated publication metadata; external publisher checks bytes/grid/coverage."""
        _identifier.validate_python(publication_id)
        r = self._current(project_id, job_id, attempt, owner_id, owner_epoch)
        if r is None or r.state != "running" or not r.compute_allocated or r.publication_id is not None:
            raise JobStateError("publication not authorized")
        publication_key = (project_id, publication_id)
        if publication_key in self._publications:
            raise JobConflict("publication ID already exists in project")
        self._publications[publication_key] = job_id
        r.publication_id = publication_id
        r.state = "succeeded"
        return self._view(project_id, job_id, r)

    def retain_dependency(self, project_id: str, job_id: str, dependency_id: str) -> JobView:
        """Trusted metadata pin; independent of the ephemeral compute allocation."""
        _identifier.validate_python(dependency_id)
        r = self._record(project_id, job_id)
        r.retained_dependencies = r.retained_dependencies | {dependency_id}
        return self._view(project_id, job_id, r)

    def release_dependency(self, project_id: str, job_id: str, dependency_id: str) -> JobView:
        _identifier.validate_python(dependency_id)
        r = self._record(project_id, job_id)
        r.retained_dependencies = r.retained_dependencies - {dependency_id}
        return self._view(project_id, job_id, r)
