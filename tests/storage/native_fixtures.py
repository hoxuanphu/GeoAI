"""In-memory unit I/O with explicit registration; never native OS evidence."""
import hashlib
import io
from geoai.storage.native_io import StorageIOError, NativeIdentity


class MemoryRoot:
    def __init__(self, files):
        self.files, self.deadlines, self.closed = dict(files), [], False

    def open_read(self, path, *, sha256, size_bytes, cancelled, deadline, **kwargs):
        if cancelled(): raise StorageIOError("cancelled_or_deadline")
        self.deadlines.append(deadline)
        content = self.files[path]
        if len(content) != size_bytes or hashlib.sha256(content).hexdigest() != sha256:
            raise StorageIOError('content_mismatch')
        return io.BytesIO(content)

    def create_file(self, path, chunks, *, max_bytes, max_chunk_bytes=1048576, cancelled, deadline):
        self.deadlines.append(deadline)
        if path in self.files: raise StorageIOError('already_exists')
        content = b''.join(chunks)
        if len(content) > max_bytes: raise StorageIOError('resource_exhausted')
        self.files[path] = content
        return len(content), hashlib.sha256(content).hexdigest()

    def move_verified(self, path, destination, target, *, sha256, size_bytes, cancelled, deadline):
        if cancelled(): raise StorageIOError("cancelled_or_deadline")
        self.deadlines.append(deadline)
        content = self.files[path]
        if len(content) != size_bytes or hashlib.sha256(content).hexdigest() != sha256:
            raise StorageIOError('content_mismatch')
        if target in destination.files: raise StorageIOError('already_exists')
        destination.files[target] = content
        del self.files[path]

    def ensure_directory(self, path): pass

    def delete_verified(self, path, *, sha256, size_bytes, cancelled, deadline):
        if cancelled(): raise StorageIOError("cancelled_or_deadline")
        self.deadlines.append(deadline)
        content = self.files[path]
        if len(content) != size_bytes or hashlib.sha256(content).hexdigest() != sha256:
            raise StorageIOError('content_mismatch')
        del self.files[path]

    def close(self): self.closed = True


class MemoryFactory:
    def __init__(self):
        self.roots, self.external_calls = {}, []

    def register(self, purpose, files=()):
        root = MemoryRoot(files)
        self.roots[id(root)] = (root, purpose)
        return root

    def require_root(self, root, *, purpose):
        found = self.roots.get(id(root))
        if not found or found[0] is not root: raise StorageIOError('unregistered_root')
        if root.closed: raise StorageIOError('root_closed')
        if found[1] != purpose: raise StorageIOError('root_purpose_mismatch')

    def open_external(self, registration, **kwargs):
        self.external_calls.append(registration)
        return io.BytesIO(b'external')
