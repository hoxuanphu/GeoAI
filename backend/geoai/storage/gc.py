"""Registered disposable files only; retention policy is supplied internally."""
from dataclasses import dataclass
from geoai.storage.native_io import NativeRoot, operation_deadline


@dataclass(frozen=True)
class DisposableFile:
    dependency_id: str
    relative_path: str
    sha256: str
    size_bytes: int


class DisposableCollector:
    def __init__(self, repository, disposable_root: NativeRoot, *, policy_id, io_factory):
        io_factory.require_root(disposable_root, purpose="staging")
        self.io_factory = io_factory
        self.repository, self.root, self.policy_id = repository, disposable_root, policy_id
        self._files = {}

    def register(self, record: DisposableFile):
        """Trusted retention service registers an owned file, never a UI path."""
        if type(record) is not DisposableFile or record.dependency_id in self._files:
            raise ValueError("duplicate or invalid disposable registration")
        self._files[record.dependency_id] = record

    def collect(self, dependency_id, *, deadline_seconds=60, cancelled=lambda: False):
        deadline = operation_deadline(deadline_seconds)
        record = self._files[dependency_id]
        def delete():
            self.io_factory.require_root(self.root, purpose="staging")
            self.root.delete_verified(record.relative_path, sha256=record.sha256, size_bytes=record.size_bytes,
                                      cancelled=cancelled, deadline=deadline)
        collected = self.repository.collect_unretained(dependency_id, delete, policy_id=self.policy_id)
        if collected:
            del self._files[dependency_id]
        return collected
