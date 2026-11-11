"""Platform-neutral value types for native storage adapters."""
from dataclasses import dataclass


class StorageIOError(ValueError):
    def __init__(self, code="invalid_input"):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class NativeIdentity:
    volume_id: str
    file_id: str
