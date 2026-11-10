"""Private temporary worker grants; never public RPC input or project exports.

These models validate metadata only. The native resolver must verify actual
Windows paths, handles, file identity, bytes, ownership and attempt liveness.
"""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import (
    AttemptKey, Contract, Identifier, NonNegativeInt, PositiveInt,
    ResourceBudget, Sha256, Text, ValueModel,
)
from .runs import RunManifest

FIXTURE_ARTIFACT_BYTES = b"GeoAI synthetic artifact\n"


class FileIdentity(ValueModel):
    volume_id: Text
    file_id: Text


class ManagedLocalLocation(ValueModel):
    kind: Literal["managed-local"]
    root_id: Identifier
    relative_path: Text


class ExternalRegisteredLocalLocation(ValueModel):
    kind: Literal["external-registered-local"]
    registration_id: Identifier
    absolute_path: Text
    file_identity: FileIdentity


ReadLocation = Annotated[ManagedLocalLocation | ExternalRegisteredLocalLocation, Field(discriminator="kind")]


class WorkerReadEntry(ValueModel):
    ref_id: Identifier
    kind: Literal["manifest", "input", "model", "checkpoint", "profile"]
    sha256: Sha256
    size_bytes: NonNegativeInt
    location: ReadLocation
    permission: Literal["read_only"]


class WorkerAccessContext(Contract):
    access_context_id: Identifier
    project_id: Identifier
    worker_id: Identifier
    launch_nonce: Identifier
    execution_owner_id: Identifier
    owner_epoch: PositiveInt
    attempt: AttemptKey
    job_spec_id: Identifier
    job_spec_sha256: Sha256
    input_snapshot_id: Identifier
    input_snapshot_sha256: Sha256
    read_entries: Annotated[tuple[WorkerReadEntry, ...], Field(min_length=1)]
    staging_id: Identifier
    resource_budget: ResourceBudget

    @model_validator(mode="after")
    def manifest_bindings(self):
        if self.job_spec_id != self.attempt.job_id:
            raise ValueError("context job must match its attempt")
        refs = {entry.ref_id: entry for entry in self.read_entries}
        if len(refs) != len(self.read_entries):
            raise ValueError("read entry references must be unique")
        for ref_id, checksum in ((self.job_spec_id, self.job_spec_sha256), (self.input_snapshot_id, self.input_snapshot_sha256)):
            entry = refs.get(ref_id)
            if entry is None or entry.kind != "manifest" or entry.sha256 != checksum:
                raise ValueError("job and input manifests require matching read entries and hashes")
        return self


class WorkerBootstrap(ValueModel):
    schema_version: Literal["0.1.0"]
    protocol_version: Literal["0.1.0"]
    worker_id: Identifier
    launch_nonce: Identifier
    context_registry_path: Text


class ManagedRootRegistration(ValueModel):
    root_id: Identifier
    absolute_path: Text


class ExternalReadRegistration(ValueModel):
    registration_id: Identifier
    absolute_path: Text
    file_identity: FileIdentity


class FixtureOutput(ValueModel):
    """One synthetic artifact in a trusted, attempt-scoped staging root."""
    staging_id: Identifier
    absolute_path: Text
    artifact_relative_path: Text
    manifest: RunManifest

    @model_validator(mode="after")
    def fixed_artifact(self):
        from hashlib import sha256
        artifacts = self.manifest.artifacts
        if (self.manifest.publication_state != "candidate" or len(artifacts) != 1
                or artifacts[0].size_bytes != len(FIXTURE_ARTIFACT_BYTES)
                or artifacts[0].sha256 != sha256(FIXTURE_ARTIFACT_BYTES).hexdigest()):
            raise ValueError("fixture artifact must match fixed synthetic bytes")
        return self


class WorkerLaunchPacket(ValueModel):
    """Private, one-use snapshot delivered through an inherited handle."""
    bootstrap: WorkerBootstrap
    registry_delivery: Literal["handle-snapshot"]
    project_id: Identifier
    execution_owner_id: Identifier
    owner_epoch: PositiveInt
    context_json: Annotated[str, Field(min_length=2, max_length=1_048_576)]
    job_json: Annotated[str, Field(min_length=2, max_length=1_048_576)]
    snapshot_json: Annotated[str, Field(min_length=2, max_length=1_048_576)]
    start: "StartParams"
    managed_roots: tuple[ManagedRootRegistration, ...]
    external_registrations: tuple[ExternalReadRegistration, ...]
    candidate_manifest_id: Identifier
    fixture_output: FixtureOutput | None = None
    fixture_mode: Literal["complete", "block", "log", "flood_stderr"]
    heartbeat_seconds: Annotated[float, Field(gt=0, le=60)]

    @model_validator(mode="after")
    def unique_registrations(self):
        if len({root.root_id for root in self.managed_roots}) != len(self.managed_roots):
            raise ValueError("duplicate managed root")
        if len({entry.registration_id for entry in self.external_registrations}) != len(self.external_registrations):
            raise ValueError("duplicate external registration")
        if self.fixture_output is not None and (
                self.fixture_output.manifest.attempt != self.start.attempt
                or self.fixture_output.manifest.job_id != self.start.job_spec_id
                or self.fixture_output.manifest.input_snapshot_id != self.start.input_snapshot_id):
            raise ValueError("fixture manifest does not match start")
        return self


from .rpc import StartParams
WorkerLaunchPacket.model_rebuild()
