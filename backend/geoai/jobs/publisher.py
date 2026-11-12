"""Coordinator-only candidate validation and immutable local publication.

Filesystem rename precedes the durable repository commit. A failed commit leaves
unregistered files for reconcile; existence never authorizes asset serving.
"""
from dataclasses import dataclass
from contextlib import ExitStack
import hashlib
import time
from types import MappingProxyType

from pydantic import TypeAdapter

from geoai.contracts import AttemptKey, InputSnapshot, RunManifest
from geoai.contracts.common import Identifier
from geoai.storage.native_io import StorageIOError, operation_deadline


_identifier = TypeAdapter(Identifier)


class PublicationError(ValueError):
    pass


@dataclass(frozen=True)
class _Candidate:
    context_id: str
    project_id: str
    attempt_bytes: bytes
    staging_id: str
    manifest_bytes: bytes
    artifact_paths: tuple[tuple[str, str], ...]


class Publisher:
    def __init__(self, repository, grants, read_resolver, staging_roots, output_root,
                 writer_guard, *, validator, io_factory):
        """validator(job, manifest) must explicitly approve profile/grid/coverage.

        The injected validator is trusted application code, never a client flag.
        No default GIS/model validator is implied by checksum verification.
        """
        if not callable(validator):
            raise TypeError("trusted validator and native output root required")
        io_factory.require_root(output_root, purpose="publication")
        self.io_factory = io_factory
        self.repository, self.grants, self.reader = repository, grants, read_resolver
        self._staging = MappingProxyType(dict(staging_roots))
        self.output, self.guard, self.validator = output_root, writer_guard, validator
        self._candidates = {}

    def register_candidate(self, *, candidate_id, context_id, project_id, attempt,
                           staging_id, manifest_bytes, artifact_paths):
        """Trusted coordinator registration; wire events subsequently carry ID only."""
        try:
            _identifier.validate_python(candidate_id)
            if type(manifest_bytes) is not bytes or len(manifest_bytes) > 1048576:
                raise PublicationError("candidate_manifest_invalid")
            manifest = RunManifest.model_validate_json(manifest_bytes)
            key = AttemptKey.model_validate_json(attempt.model_dump_json())
            if (candidate_id in self._candidates or project_id != self.repository.project_id
                    or manifest.attempt != key or manifest.publication_state != "candidate"
                    or not manifest.artifacts or manifest.job_id != key.job_id):
                raise PublicationError("candidate_binding_invalid")
            paths = tuple(sorted(dict(artifact_paths).items()))
            ids = [artifact.asset_id for artifact in manifest.artifacts]
            if (len(set(ids)) != len(ids) or {asset_id for asset_id, _ in paths} != set(ids)
                    or len({path.casefold() for _, path in paths}) != len(paths)
                    or not all(isinstance(path, str) for _, path in paths)):
                raise PublicationError("candidate_inventory_invalid")
            self.guard.assert_held(project_id)
            self.io_factory.require_root(self._staging.get(staging_id), purpose="staging")
            self.grants.register_candidate(candidate_id, context_id, project_id=project_id,
                                           attempt=key, staging_id=staging_id)
            self._candidates[candidate_id] = _Candidate(context_id, project_id,
                key.model_dump_json().encode(), staging_id, manifest_bytes, paths)
        except PublicationError:
            raise
        except Exception:
            raise PublicationError("candidate_registration_rejected") from None

    def publish(self, candidate_id, context_id, attempt, publication_id, *,
                deadline_seconds=60, cancelled=lambda: False):
        deadline = operation_deadline(deadline_seconds)
        options = dict(deadline=deadline, cancelled=cancelled)
        def check_budget():
            if cancelled() or time.monotonic() >= deadline:
                raise PublicationError("cancelled_or_deadline")
        try:
            check_budget()
            self.io_factory.require_root(self.output, purpose="publication")
            _identifier.validate_python(publication_id)
            candidate = self._candidates[candidate_id]
            key = AttemptKey.model_validate_json(attempt.model_dump_json())
            if candidate.context_id != context_id or AttemptKey.model_validate_json(candidate.attempt_bytes) != key:
                raise PublicationError("candidate_binding_invalid")
            self.guard.assert_held(candidate.project_id)
            staging_id = self.grants.check_candidate(candidate_id, context_id,
                project_id=candidate.project_id, attempt=key)
            if staging_id != candidate.staging_id:
                raise PublicationError("candidate_binding_invalid")
            current = self.repository.get(key.job_id)
            if current.state != "running" or current.attempt != key:
                raise PublicationError("stale_attempt")
            job = current.job_spec
            manifest = RunManifest.model_validate_json(candidate.manifest_bytes)
            snapshot_entry = self.grants.resolve(context_id, key, job.input_snapshot_id)
            pipeline_entry = self.grants.resolve(context_id, key, job.workflow_id)
            check_budget()
            with self.reader._open_read_until(context_id, key, job.input_snapshot_id,
                    cancelled=cancelled, deadline=deadline) as source:
                snapshot = InputSnapshot.model_validate_json(source.read())
            if (job.project_id != candidate.project_id or manifest.input_snapshot_id != job.input_snapshot_id
                    or manifest.input_sha256 != snapshot_entry.sha256
                    or manifest.pipeline_sha256 != pipeline_entry.sha256
                    or manifest.grid_id != job.grid_id or snapshot.grid_id != job.grid_id
                    or snapshot.project_id != candidate.project_id
                    or manifest.transform_ids != snapshot.transform_ids
                    or manifest.model_ids != job.model_ids or manifest.physical_model_ids != job.physical_model_ids
                    or self.validator(job, manifest) is not True):
                raise PublicationError("manifest_profile_binding_invalid")
            staging = self._staging[staging_id]
            self.io_factory.require_root(staging, purpose="staging")
            paths = dict(candidate.artifact_paths)
            # Verify every byte before moving any file. The subsequent move
            # uses adapter-specific stable-byte verification and repeats the check.
            for artifact in manifest.artifacts:
                with staging.open_read(paths[artifact.asset_id], sha256=artifact.sha256,
                                       size_bytes=artifact.size_bytes, **options):
                    pass
            namespace = hashlib.sha256((candidate.project_id + "\0" + key.job_id + "\0"
                + key.attempt_id + "\0" + manifest.run_id + "\0" + publication_id).encode()).hexdigest()
            inventory = []
            for index, artifact in enumerate(manifest.artifacts):
                self.guard.assert_held(candidate.project_id)
                destination = f"runs/{namespace}/{index}.bin"
                staging.move_verified(paths[artifact.asset_id], self.output, destination,
                    sha256=artifact.sha256, size_bytes=artifact.size_bytes, **options)
                inventory.append((artifact.asset_id, destination, artifact.sha256, artifact.size_bytes))
            published = RunManifest.model_validate({**manifest.model_dump(), "publication_state": "published"})
            manifest_bytes = published.model_dump_json().encode()
            manifest_path = f"runs/{namespace}/manifest.json"
            size, checksum = self.output.create_file(manifest_path, [manifest_bytes], max_bytes=1048576, **options)
            manifest_id = "manifest:" + hashlib.sha256(manifest.run_id.encode()).hexdigest()
            if manifest_id in {artifact.asset_id for artifact in manifest.artifacts}:
                raise PublicationError("manifest_asset_conflict")
            inventory.append((manifest_id, manifest_path, checksum, size))
            with ExitStack() as held_bytes:
                for _, path, checksum, size in inventory:
                    held_bytes.enter_context(self.output.open_read(path, sha256=checksum, size_bytes=size, **options))
                self.guard.assert_held(candidate.project_id)
                self.grants.check_candidate(candidate_id, context_id, project_id=candidate.project_id, attempt=key)
                # The real repository serializes cancel/publish and rechecks
                # owner/full token/state/uniqueness. Keep adapter-backed verified
                # output readers alive until this commit returns.
                check_budget()
                return self.repository.publish(key.job_id, key, publication_id, artifacts=tuple(inventory))
        except PublicationError:
            raise
        except Exception:
            raise PublicationError("publication_rejected") from None

    def verify_inventory_record(self, record, *, deadline_seconds=60, cancelled=lambda: False):
        """False means rejected bytes, never an aborted/configuration check."""
        deadline = operation_deadline(deadline_seconds)
        self.io_factory.require_root(self.output, purpose="publication")
        if cancelled():
            raise StorageIOError("cancelled_or_deadline")
        try:
            with self.output.open_read(record.relative_path, sha256=record.sha256, size_bytes=record.size_bytes,
                                       cancelled=cancelled, deadline=deadline):
                return True
        except StorageIOError as error:
            if error.code in {"content_mismatch", "file_identity_mismatch", "missing_or_busy_resource",
                              "missing_resource", "unsupported_link_or_type", "directory_identity_mismatch"}:
                return False
            # Reconciliation must roll back instead of demoting valid assets when
            # its budget, root lifetime, or native facility is unavailable.
            raise
