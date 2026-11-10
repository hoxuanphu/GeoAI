"""Compose accepted metadata grants with internally registered native roots."""
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from geoai.storage.windows_io import NativeRoot, NativeIdentity, StorageIOError


@dataclass(frozen=True)
class ExternalRegistration:
    path: Path
    identity: NativeIdentity


class _ExternalReader:
    def __init__(self, reader, root):
        self.reader, self.root = reader, root

    @property
    def identity(self):
        return self.reader.identity

    @property
    def size_bytes(self):
        return self.reader.size_bytes

    def read(self, size=-1):
        return self.reader.read(size)

    def seek(self, offset):
        return self.reader.seek(offset)

    def close(self):
        self.reader.close()
        self.root.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class WorkerIOResolver:
    """No free path API: each open first checks the currently accepted grant.

    Managed roots/external registrations come from trusted local composition,
    independently of paths inside a context. The caller still owns worker stop
    and grant revocation: static context bytes do not revoke open file handles.
    """
    def __init__(self, registry, managed_roots, external_registrations):
        self.registry = registry
        self._roots = MappingProxyType(dict(managed_roots))
        self._external = MappingProxyType(dict(external_registrations))

    def open_read(self, context_id, attempt, ref_id, *, cancelled=lambda: False, deadline_seconds=60):
        entry = self.registry.resolve(context_id, attempt, ref_id)
        location = entry.location
        options = dict(sha256=entry.sha256, size_bytes=entry.size_bytes,
                       cancelled=cancelled, deadline_seconds=deadline_seconds)
        if location.kind == "managed-local":
            root = self._roots.get(location.root_id)
            if not isinstance(root, NativeRoot):
                raise StorageIOError("unregistered_root")
            return root.open_read(location.relative_path, **options)
        registration = self._external.get(location.registration_id)
        if not isinstance(registration, ExternalRegistration):
            raise StorageIOError("unregistered_external_input")
        identity = location.file_identity
        if (str(registration.path) != location.absolute_path
                or (registration.identity.volume_id, registration.identity.file_id) != (identity.volume_id, identity.file_id)):
            raise StorageIOError("registration_identity_mismatch")
        root = NativeRoot(registration.path.parent)
        try:
            reader = root.open_read(registration.path.name, expected_identity=(identity.volume_id, identity.file_id), **options)
            return _ExternalReader(reader, root)
        except BaseException:
            root.close()
            raise
