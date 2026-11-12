"""Compose accepted metadata grants with internally registered native roots."""
from types import MappingProxyType
from geoai.storage.native_io import ExternalRegistration, NativeIdentity, StorageIOError, operation_deadline


class WorkerIOResolver:
    """No free path API: each open first checks the currently accepted grant.

    Managed roots/external registrations come from trusted local composition,
    independently of paths inside a context. The caller still owns worker stop
    and grant revocation: static context bytes do not revoke open file handles.
    """
    def __init__(self, registry, managed_roots, external_registrations, *, io_factory):
        self.registry, self.io_factory = registry, io_factory
        for root in managed_roots.values():
            io_factory.require_root(root, purpose="read")
        self._roots = MappingProxyType(dict(managed_roots))
        self._external = MappingProxyType(dict(external_registrations))

    def open_read(self, context_id, attempt, ref_id, *, cancelled=lambda: False, deadline_seconds=60):
        return self._open_read_until(context_id, attempt, ref_id, cancelled=cancelled,
                                     deadline=operation_deadline(deadline_seconds))

    def _open_read_until(self, context_id, attempt, ref_id, *, cancelled, deadline):
        """Internal nesting path: carry a caller's absolute budget unchanged."""
        entry = self.registry.resolve(context_id, attempt, ref_id)
        location = entry.location
        options = dict(sha256=entry.sha256, size_bytes=entry.size_bytes,
                       cancelled=cancelled, deadline=deadline)
        if location.kind == "managed-local":
            root = self._roots.get(location.root_id)
            self.io_factory.require_root(root, purpose="read")
            return root.open_read(location.relative_path, **options)
        registration = self._external.get(location.registration_id)
        if not isinstance(registration, ExternalRegistration):
            raise StorageIOError("unregistered_external_input")
        identity = location.file_identity
        if (str(registration.path) != location.absolute_path
                or (registration.identity.volume_id, registration.identity.file_id) != (identity.volume_id, identity.file_id)):
            raise StorageIOError("registration_identity_mismatch")
        return self.io_factory.open_external(registration, **options)
