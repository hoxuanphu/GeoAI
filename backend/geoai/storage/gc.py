"""Registered disposable files only; retention policy is supplied internally."""
from dataclasses import dataclass
from geoai.storage.windows_io import NativeRoot


@dataclass(frozen=True)
class DisposableFile:
    dependency_id: str
    relative_path: str
    sha256: str
    size_bytes: int


class DisposableCollector:
    def __init__(self, repository, disposable_root: NativeRoot, *, policy_id):
        if not isinstance(disposable_root, NativeRoot):
            raise TypeError("registered disposable root required")
        self.repository, self.root, self.policy_id = repository, disposable_root, policy_id
        self._files = {}

    def register(self, record: DisposableFile):
        """Trusted retention service registers an owned file, never a UI path."""
        if type(record) is not DisposableFile or record.dependency_id in self._files:
            raise ValueError("duplicate or invalid disposable registration")
        self._files[record.dependency_id] = record

    def collect(self, dependency_id):
        record = self._files[dependency_id]
        def delete():
            self.root.delete_verified(record.relative_path, sha256=record.sha256, size_bytes=record.size_bytes)
        collected = self.repository.collect_unretained(dependency_id, delete, policy_id=self.policy_id)
        if collected:
            del self._files[dependency_id]
        return collected
