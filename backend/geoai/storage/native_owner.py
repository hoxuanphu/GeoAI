"""Platform-neutral ownership boundary; metadata is never a native guard."""
from pathlib import Path
from typing import Protocol
from geoai.storage.guards import WriterGuard, OwnerStopEvidence


class OwnershipError(RuntimeError):
    """Ownership is busy, uncertain, or no longer held."""


class ExecutionOwner(Protocol):
    @property
    def owner_id(self) -> str: ...
    @property
    def owner_epoch(self) -> int: ...
    def acquire_project(self, project_id: str, project_root: Path) -> WriterGuard: ...
    def recovery_evidence(self) -> OwnerStopEvidence: ...
    def close(self) -> None: ...
