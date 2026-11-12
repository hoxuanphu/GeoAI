"""Platform-neutral value types for native storage adapters."""
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Literal, Protocol


class StorageIOError(ValueError):
    def __init__(self, code="invalid_input"):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class NativeIdentity:
    volume_id: str
    file_id: str


@dataclass(frozen=True)
class ExternalRegistration:
    path: Path
    identity: NativeIdentity


class NativeReader(Protocol):
    identity: NativeIdentity
    size_bytes: int

    def read(self, size: int = -1) -> bytes: ...
    def seek(self, offset: int) -> int: ...
    def close(self) -> None: ...
    def __enter__(self) -> 'NativeReader': ...
    def __exit__(self, *args: object) -> None: ...


class NativeRoot(Protocol):
    def open_read(self, relative_path: str, *, sha256: str, size_bytes: int,
                  expected_identity: NativeIdentity | None = None,
                  cancelled: Callable[[], bool], deadline: float) -> NativeReader: ...
    def create_file(self, relative_path: str, chunks: Iterable[bytes], *, max_bytes: int,
                    cancelled: Callable[[], bool], deadline: float,
                    max_chunk_bytes: int = 1048576) -> tuple[int, str]: ...
    def ensure_directory(self, relative_path: str) -> None: ...
    def move_verified(self, relative_path: str, destination_root: 'NativeRoot',
                      destination_path: str, *, sha256: str, size_bytes: int,
                      cancelled: Callable[[], bool], deadline: float) -> None: ...
    def delete_verified(self, relative_path: str, *, sha256: str, size_bytes: int,
                        cancelled: Callable[[], bool], deadline: float) -> None: ...
    def close(self) -> None: ...


class NativeIOFactory(Protocol):
    def open_registered_root(self, root_id: str, absolute_path: Path, *,
                             purpose: Literal['read', 'staging', 'publication']) -> NativeRoot: ...
    def require_root(self, root: NativeRoot, *, purpose: str) -> None: ...
    def open_external(self, registration: ExternalRegistration, *, sha256: str,
                      size_bytes: int, cancelled: Callable[[], bool],
                      deadline: float) -> NativeReader: ...


def operation_deadline(seconds, *, monotonic=None):
    """Convert a legacy public duration once, before starting an operation."""
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 86400:
        raise StorageIOError("invalid_budget")
    return (time.monotonic() if monotonic is None else monotonic()) + seconds
