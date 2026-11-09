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
