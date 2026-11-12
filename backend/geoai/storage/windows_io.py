"""Narrow Windows file I/O through pinned ancestor and file handles.

Trusted composition supplies local roots and immutable reference metadata. This
adapter never loads a GIS driver, follows sidecars, activates a pack or grants
an OS sandbox. A returned reader holds deny-write/delete sharing until closed.
"""
from __future__ import annotations

from contextlib import contextmanager, ExitStack
import ctypes
from ctypes import wintypes
import hashlib
import math
import uuid
import os
from pathlib import Path
import re
import threading
import time

from geoai.storage.importer import ImportRejected, _name


from geoai.storage.native_io import ExternalRegistration, NativeIdentity, StorageIOError


if os.name == "nt":
    _kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    _INVALID = ctypes.c_void_p(-1).value
    _READ, _WRITE = 0x80000000, 0x40000000
    _ATTR_READ = 0x80
    _SHARE_READ, _SHARE_WRITE = 1, 2
    _NEW, _EXISTING = 1, 3
    _DIRECTORY, _REPARSE = 0x10, 0x400
    _BACKUP, _OPEN_REPARSE = 0x02000000, 0x00200000

    class _FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class _FileInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("created", _FileTime),
                    ("accessed", _FileTime), ("written", _FileTime),
                    ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
                    ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
                    ("id_high", wintypes.DWORD), ("id_low", wintypes.DWORD)]

    def _api(name, args, result):
        fn = getattr(_kernel, name)
        fn.argtypes, fn.restype = args, result
        return fn

    _CreateFile = _api("CreateFileW", [wintypes.LPCWSTR, wintypes.DWORD,
                        wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                        wintypes.DWORD, wintypes.HANDLE], wintypes.HANDLE)
    _Info = _api("GetFileInformationByHandle", [wintypes.HANDLE, ctypes.POINTER(_FileInfo)], wintypes.BOOL)
    _Close = _api("CloseHandle", [wintypes.HANDLE], wintypes.BOOL)
    _Read = _api("ReadFile", [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p], wintypes.BOOL)
    _Write = _api("WriteFile", [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p], wintypes.BOOL)
    _Flush = _api("FlushFileBuffers", [wintypes.HANDLE], wintypes.BOOL)
    _SetInfo = _api("SetFileInformationByHandle", [wintypes.HANDLE, ctypes.c_int,
                        ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL)
    _Seek = _api("SetFilePointerEx", [wintypes.HANDLE, ctypes.c_longlong,
                    ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD], wintypes.BOOL)
    _FinalPath = _api("GetFinalPathNameByHandleW", [wintypes.HANDLE, wintypes.LPWSTR,
                        wintypes.DWORD, wintypes.DWORD], wintypes.DWORD)
    _DriveType = _api("GetDriveTypeW", [wintypes.LPCWSTR], wintypes.UINT)

    def _open(path, access, share, disposition=_EXISTING, directory=False):
        handle = _CreateFile(str(path), access, share, None, disposition,
                            _OPEN_REPARSE | (_BACKUP if directory else 0), None)
        if handle in (None, _INVALID):
            raise StorageIOError("missing_or_busy_resource")
        return handle

    def _info(handle, *, directory=False):
        info = _FileInfo()
        if not _Info(handle, ctypes.byref(info)):
            raise StorageIOError("identity_unavailable")
        if info.attributes & _REPARSE or bool(info.attributes & _DIRECTORY) != directory:
            raise StorageIOError("unsupported_link_or_type")
        if not directory and info.links != 1:
            raise StorageIOError("unsupported_link_or_type")
        return info

    def _identity(info):
        return NativeIdentity(f"{info.volume:08x}", f"{info.id_high:08x}{info.id_low:08x}")

    def _final_path(handle):
        size = _FinalPath(handle, None, 0, 0)
        if not 0 < size < 32768:
            raise StorageIOError("identity_unavailable")
        buffer = ctypes.create_unicode_buffer(size + 1)
        count = _FinalPath(handle, buffer, len(buffer), 0)
        if not 0 < count < len(buffer):
            raise StorageIOError("identity_unavailable")
        value = buffer.value
        if value.startswith("\\\\?\\"):
            value = value[4:]
        return os.path.normcase(value)


def _local_path(value):
    path = Path(value)
    if os.name != "nt":
        raise StorageIOError("windows_required")
    raw = str(path)
    if (not path.is_absolute() or raw.startswith(("\\\\", "//"))
            or any(part in {".", ".."} for part in path.parts)):
        raise StorageIOError("invalid_local_root")
    # Network drives and unsupported drive types are not local project storage.
    if _DriveType(path.anchor) != 3:  # DRIVE_FIXED
        raise StorageIOError("unsupported_volume")
    return path


def _relative(value):
    try:
        if not isinstance(value, str) or len(value) > 4096:
            raise StorageIOError()
        result, directory = _name(value, 64)
        if directory:
            raise StorageIOError()
        return result
    except ImportRejected:
        raise StorageIOError("invalid_path") from None


class NativeReader:
    def __init__(self, handle, directory_handles, info, release):
        self._handle = handle
        self._directories = directory_handles
        self._release = release
        self.identity = _identity(info)
        self.size_bytes = (info.size_high << 32) | info.size_low
        self._closed = False
        self._lock = threading.RLock()

    def read(self, size=-1):
        with self._lock:
            return self._read_locked(size)

    def _read_locked(self, size):
        if self._closed or type(size) is not int or size < -1:
            raise StorageIOError("reader_closed_or_invalid")
        # Large raster callers should always use window/chunk reads. An explicit
        # read-all is permitted only for a small manifest/fixture, bounded here.
        if size == -1:
            if self.size_bytes > 16 * 1024 * 1024:
                raise StorageIOError("bounded_read_required")
            size = self.size_bytes
        if size > 16 * 1024 * 1024:
            raise StorageIOError("bounded_read_required")
        buffer = ctypes.create_string_buffer(size)
        count = wintypes.DWORD()
        if not _Read(self._handle, buffer, size, ctypes.byref(count), None):
            raise StorageIOError("read_failed")
        return buffer.raw[:count.value]

    def seek(self, offset):
        with self._lock:
            if self._closed or type(offset) is not int or not 0 <= offset <= self.size_bytes:
                raise StorageIOError("invalid_offset")
            if not _Seek(self._handle, offset, None, 0):
                raise StorageIOError("read_failed")

    def close(self):
        with self._lock:
            if not self._closed:
                _Close(self._handle)
                self._handle = None
                for handle in reversed(self._directories):
                    _Close(handle)
                self._directories.clear()
                self._closed = True
                self._release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class NativeRoot:
    """An internally registered local root pinned against ancestor replacement.

    Construction does not authorize a job. The grant registry and current
    attempt must authorize each call before this adapter is used.
    """
    def __init__(self, path):
        self.path = _local_path(path)
        self._mutex = threading.RLock()
        self._closed = False
        self._readers = 0
        self._ancestors = []
        try:
            for ancestor in (*reversed(self.path.parents), self.path):
                handle = _open(ancestor, _ATTR_READ, _SHARE_READ | _SHARE_WRITE, directory=True)
                self._ancestors.append(handle)
                _info(handle, directory=True)
                if _final_path(handle) != os.path.normcase(str(ancestor)):
                    raise StorageIOError("directory_identity_mismatch")
        except BaseException:
            for handle in reversed(self._ancestors):
                _Close(handle)
            raise

    def _assert_open(self):
        if self._closed:
            raise StorageIOError("root_closed")

    @contextmanager
    def _parents(self, relative, *, create=False):
        handles = []
        current = self.path
        try:
            for component in relative.split("/")[:-1]:
                current = current / component
                if create:
                    try:
                        current.mkdir()
                    except FileExistsError:
                        pass
                handle = _open(current, _ATTR_READ, _SHARE_READ | _SHARE_WRITE, directory=True)
                handles.append(handle)
                _info(handle, directory=True)
                if _final_path(handle) != os.path.normcase(str(current)):
                    raise StorageIOError("directory_identity_mismatch")
            yield handles
        finally:
            for handle in reversed(handles):
                _Close(handle)

    def _reader_released(self):
        with self._mutex:
            self._readers -= 1

    def open_read(self, relative_path, *, sha256, size_bytes, expected_identity=None,
                  cancelled=lambda: False, deadline_seconds=60):
        return self._verified_reader(relative_path, sha256=sha256, size_bytes=size_bytes,
                                     expected_identity=expected_identity, cancelled=cancelled,
                                     deadline_seconds=deadline_seconds, for_delete=False)

    def _verified_reader(self, relative_path, *, sha256, size_bytes, expected_identity=None,
                         cancelled=lambda: False, deadline_seconds=60, for_delete=False):
        relative = _relative(relative_path)
        if (not isinstance(sha256, str) or not re.fullmatch("[0-9a-f]{64}", sha256)
                or type(size_bytes) is not int or size_bytes < 0
                or type(deadline_seconds) not in (int, float) or not 0 < deadline_seconds <= 86400):
            raise StorageIOError("invalid_identity")
        with self._mutex:
            self._assert_open()
            with self._parents(relative) as parents:
                handle = _open(self.path / relative, _READ | (0x10000 if for_delete else 0), _SHARE_READ)
                held_parents = []
                try:
                    info = _info(handle)
                    if _final_path(handle) != os.path.normcase(str(self.path / relative)):
                        raise StorageIOError("file_identity_mismatch")
                    identity = _identity(info)
                    if expected_identity is not None and (identity.volume_id, identity.file_id) != expected_identity:
                        raise StorageIOError("file_identity_mismatch")
                    actual_size = (info.size_high << 32) | info.size_low
                    if actual_size != size_bytes:
                        raise StorageIOError("content_mismatch")
                    digest = hashlib.sha256()
                    end = time.monotonic() + deadline_seconds
                    total = 0
                    buffer = ctypes.create_string_buffer(65536)
                    while True:
                        if cancelled() or time.monotonic() >= end:
                            raise StorageIOError("cancelled_or_deadline")
                        count = wintypes.DWORD()
                        if not _Read(handle, buffer, len(buffer), ctypes.byref(count), None):
                            raise StorageIOError("read_failed")
                        if not count.value:
                            break
                        total += count.value
                        if total > size_bytes:
                            raise StorageIOError("content_mismatch")
                        digest.update(buffer.raw[:count.value])
                    if total != size_bytes or digest.hexdigest() != sha256:
                        raise StorageIOError("content_mismatch")
                    if not _Seek(handle, 0, None, 0):
                        raise StorageIOError("read_failed")
                    # Transfer parent handles out of the temporary pin scope.
                    held_parents[:] = parents
                    parents.clear()
                    self._readers += 1
                    return NativeReader(handle, held_parents, info, self._reader_released)
                except BaseException:
                    _Close(handle)
                    raise

    def delete_verified(self, relative_path, *, sha256, size_bytes,
                        cancelled=lambda: False, deadline_seconds=60):
        """Delete the exact verified staging file, by handle; no path reopen."""
        with self._verified_reader(relative_path, sha256=sha256, size_bytes=size_bytes,
                                   for_delete=True, cancelled=cancelled, deadline_seconds=deadline_seconds) as source:
            if cancelled():
                raise StorageIOError("cancelled_or_deadline")
            disposition = wintypes.BOOL(True)
            if not _SetInfo(source._handle, 4, ctypes.byref(disposition), ctypes.sizeof(disposition)):
                raise StorageIOError("delete_failed")

    def move_verified(self, relative_path, destination_root, destination_path, *, sha256, size_bytes,
                      cancelled=lambda: False, deadline_seconds=60):
        """Rename one verified file on its volume without replacing a destination.

        The source handle denies other write/delete access while identity and
        hash are verified. Both ancestor chains stay pinned during the kernel
        rename. A successful rename alone does not register a publication.
        """
        if not isinstance(destination_root, NativeRoot):
            raise StorageIOError("invalid_destination")
        target = _relative(destination_path)
        with ExitStack() as locks:
            for root in sorted({self, destination_root}, key=id):
                locks.enter_context(root._mutex)
                root._assert_open()
            with self._verified_reader(relative_path, sha256=sha256, size_bytes=size_bytes,
                                       for_delete=True, cancelled=cancelled, deadline_seconds=deadline_seconds) as source:
                with destination_root._parents(target, create=True) as parents:
                    destination_handle = parents[-1] if parents else destination_root._ancestors[-1]
                    if _identity(_info(destination_handle, directory=True)).volume_id != source.identity.volume_id:
                        raise StorageIOError("cross_volume_publish_unsupported")
                    # SetFileInformationByHandle requires a NULL RootDirectory
                    # and full destination path. Ancestor pins prevent swapping
                    # any directory during the kernel's destination lookup.
                    target_bytes = str(destination_root.path / target).encode("utf-16-le")

                    class _RenameInfo(ctypes.Structure):
                        _fields_ = [("replace", wintypes.BOOL), ("root", wintypes.HANDLE),
                                    ("length", wintypes.DWORD), ("name", ctypes.c_wchar * (len(target_bytes) // 2 + 1))]

                    info = _RenameInfo()
                    info.replace = False
                    info.root = None
                    info.length = len(target_bytes)
                    ctypes.memmove(ctypes.addressof(info) + _RenameInfo.name.offset, target_bytes, len(target_bytes))
                    if cancelled():
                        raise StorageIOError("cancelled_or_deadline")
                    if not _SetInfo(source._handle, 3, ctypes.byref(info), ctypes.sizeof(info)):
                        raise StorageIOError("rename_failed_or_destination_exists")
                    if _final_path(source._handle) != os.path.normcase(str(destination_root.path / target)):
                        raise StorageIOError("rename_identity_mismatch")

    def create_file(self, relative_path, chunks, *, max_bytes, cancelled=lambda: False,
                    deadline_seconds=60, max_chunk_bytes=1048576):
        relative = _relative(relative_path)
        if (type(max_bytes) is not int or max_bytes < 0
                or type(max_chunk_bytes) is not int or not 1 <= max_chunk_bytes <= 16777216
                or type(deadline_seconds) not in (int, float) or not 0 < deadline_seconds <= 86400):
            raise StorageIOError("invalid_budget")
        with self._mutex:
            self._assert_open()
            with self._parents(relative, create=True):
                destination = self.path / relative
                handle = _open(destination, _READ | _WRITE | 0x10000, 0, _NEW)  # DELETE for rollback by handle
                complete = False
                try:
                    _info(handle)
                    end = time.monotonic() + deadline_seconds
                    total = 0
                    digest = hashlib.sha256()
                    for block in chunks:
                        if cancelled() or time.monotonic() >= end:
                            raise StorageIOError("cancelled_or_deadline")
                        if not isinstance(block, bytes) or len(block) > max_chunk_bytes:
                            raise StorageIOError("invalid_chunk")
                        total += len(block)
                        if total > max_bytes:
                            raise StorageIOError("resource_exhausted")
                        written = wintypes.DWORD()
                        if not _Write(handle, block, len(block), ctypes.byref(written), None) or written.value != len(block):
                            raise StorageIOError("write_failed")
                        digest.update(block)
                    if cancelled() or time.monotonic() >= end:
                        raise StorageIOError("cancelled_or_deadline")
                    if not _Flush(handle):
                        raise StorageIOError("flush_failed")
                    complete = True
                    return total, digest.hexdigest()
                finally:
                    if not complete:
                        # Mark this exact exclusively created handle for deletion;
                        # never close then reopen/unlink an attacker-swapped path.
                        disposition = wintypes.BOOL(True)
                        _SetInfo(handle, 4, ctypes.byref(disposition), ctypes.sizeof(disposition))
                        # A failed delete disposition leaves unregistered staging
                        # for recovery, without deleting a different file by name.
                    _Close(handle)

    def ensure_directory(self, relative_path):
        """Create only validated directory components under this pinned root."""
        relative = _relative(relative_path)
        with self._mutex:
            self._assert_open()
            with self._parents(relative + "/unused-placeholder", create=True):
                pass

    def close(self):
        with self._mutex:
            if self._closed:
                return
            if self._readers:
                raise StorageIOError("root_has_live_readers")
            for handle in reversed(self._ancestors):
                _Close(handle)
            self._ancestors.clear()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def _native_call(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except OSError:
        raise StorageIOError("native_io_failed") from None


class _ReaderAdapter:
    """Keep a verified legacy reader (and optional external root) alive."""
    def __init__(self, reader, owned_root=None):
        self._reader, self._owned_root = reader, owned_root
        self._closed = False
        self._mutex = threading.RLock()

    @property
    def identity(self):
        return self._reader.identity

    @property
    def size_bytes(self):
        return self._reader.size_bytes

    def read(self, size=-1):
        with self._mutex:
            if self._closed:
                raise StorageIOError("reader_closed_or_invalid")
            return _native_call(self._reader.read, size)

    def seek(self, offset):
        with self._mutex:
            if self._closed:
                raise StorageIOError("reader_closed_or_invalid")
            _native_call(self._reader.seek, offset)
            return offset

    def close(self):
        with self._mutex:
            if not self._closed:
                _native_call(self._reader.close)
                if self._owned_root is not None:
                    self._owned_root.close()
                self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def _deadline_options(cancelled, deadline):
    if type(deadline) not in (int, float) or not math.isfinite(deadline) or not callable(cancelled):
        raise StorageIOError("invalid_budget")
    def stop():
        try:
            return bool(cancelled()) or time.monotonic() >= deadline
        except Exception:
            raise StorageIOError("cancellation_unavailable") from None
    remaining = deadline - time.monotonic()
    if remaining <= 0 or stop():
        raise StorageIOError("cancelled_or_deadline")
    # Legacy Win32 accepts durations capped at a day. The callback independently
    # checks the original absolute deadline even after waiting for a native lock.
    return dict(cancelled=stop, deadline_seconds=min(remaining, 86400.0))


class _RegisteredRoot:
    def __init__(self, factory, root_id, legacy, purpose):
        self._factory, self._root_id = factory, root_id
        self._legacy, self._purpose, self._closed = legacy, purpose, False
        self._mutex = threading.RLock()

    @contextmanager
    def _operation(self, cancelled, deadline):
        budget = _deadline_options(cancelled, deadline)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or budget['cancelled']():
                raise StorageIOError("cancelled_or_deadline")
            if self._mutex.acquire(timeout=min(remaining, .05)):
                break
        try:
            _deadline_options(cancelled, deadline)
            yield
        finally:
            self._mutex.release()

    def _authorize(self, *, write=False):
        self._factory._require(self)
        if write and self._purpose == "read":
            raise StorageIOError("root_purpose_mismatch")

    def open_read(self, relative_path, *, sha256, size_bytes, expected_identity=None,
                  cancelled, deadline):
        with self._operation(cancelled, deadline):
            self._authorize()
            if expected_identity is not None:
                if type(expected_identity) is not NativeIdentity:
                    raise StorageIOError("invalid_identity")
                expected_identity = (expected_identity.volume_id, expected_identity.file_id)
            reader = _native_call(self._legacy.open_read, relative_path, sha256=sha256, size_bytes=size_bytes,
                expected_identity=expected_identity, **_deadline_options(cancelled, deadline))
            return _ReaderAdapter(reader)

    def create_file(self, relative_path, chunks, *, max_bytes, cancelled, deadline,
                    max_chunk_bytes=1048576):
        with self._operation(cancelled, deadline):
            self._authorize(write=True)
            return _native_call(self._legacy.create_file, relative_path, chunks, max_bytes=max_bytes,
                max_chunk_bytes=max_chunk_bytes, **_deadline_options(cancelled, deadline))

    def ensure_directory(self, relative_path):
        # This protocol method has no budget parameter; fail busy instead of
        # introducing an unbounded lock wait into a budgeted extraction loop.
        if not self._mutex.acquire(blocking=False):
            raise StorageIOError("native_io_busy")
        try:
            self._authorize(write=True)
            return _native_call(self._legacy.ensure_directory, relative_path)
        finally:
            self._mutex.release()

    def move_verified(self, relative_path, destination_root, destination_path, *,
                      sha256, size_bytes, cancelled, deadline):
        self._factory.require_root(destination_root, purpose="publication")
        with ExitStack() as locks:
            roots = (self,) if self is destination_root else sorted((self, destination_root), key=id)
            for root in roots:
                locks.enter_context(root._operation(cancelled, deadline))
            self._authorize(write=True)
            self._factory.require_root(destination_root, purpose="publication")
            return _native_call(self._legacy.move_verified, relative_path, destination_root._legacy, destination_path,
                sha256=sha256, size_bytes=size_bytes, **_deadline_options(cancelled, deadline))

    def delete_verified(self, relative_path, *, sha256, size_bytes, cancelled, deadline):
        with self._operation(cancelled, deadline):
            self._authorize(write=True)
            return _native_call(self._legacy.delete_verified, relative_path, sha256=sha256, size_bytes=size_bytes,
                **_deadline_options(cancelled, deadline))

    def close(self):
        with self._mutex:
            if not self._closed:
                # A reader still alive makes legacy.close fail: retain registration
                # and pins so a failed close never releases native authority.
                _native_call(self._legacy.close)
                with self._factory._mutex:
                    self._closed = True
                    del self._factory._roots[id(self)]
                    del self._factory._root_ids[self._root_id]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class WindowsIOFactory:
    """Trusted composition only. Registry identity, not protocol shape, grants use."""
    def __init__(self):
        self._roots, self._root_ids = {}, {}
        self._mutex = threading.RLock()

    def _require(self, root):
        with self._mutex:
            if id(root) not in self._roots or self._roots[id(root)] is not root:
                raise StorageIOError("unregistered_root")
            if root._closed:
                raise StorageIOError("root_closed")

    def open_registered_root(self, root_id, absolute_path, *, purpose):
        with self._mutex:
            if (type(root_id) is not str or not root_id or root_id in self._root_ids
                    or purpose not in ("read", "staging", "publication")
                    or not isinstance(absolute_path, Path) or not absolute_path.is_absolute()):
                raise StorageIOError("invalid_root_registration")
            reservation = object()
            self._root_ids[root_id] = reservation
        try:
            legacy = _native_call(NativeRoot, absolute_path)
            root = _RegisteredRoot(self, root_id, legacy, purpose)
        except BaseException:
            with self._mutex:
                if self._root_ids.get(root_id) is reservation:
                    del self._root_ids[root_id]
            raise
        with self._mutex:
            self._roots[id(root)] = root  # Strong reference prevents id reuse.
            self._root_ids[root_id] = root
        return root

    def require_root(self, root, *, purpose):
        with self._mutex:
            self._require(root)
            if root._purpose != purpose:
                raise StorageIOError("root_purpose_mismatch")

    def open_external(self, registration, *, sha256, size_bytes, cancelled, deadline):
        if (type(registration) is not ExternalRegistration
                or not isinstance(registration.path, Path)
                or type(registration.identity) is not NativeIdentity):
            raise StorageIOError("unregistered_external_input")
        _deadline_options(cancelled, deadline)  # Reject expiry before opening native handles.
        root = self.open_registered_root("external:" + uuid.uuid4().hex,
                                         registration.path.parent, purpose="read")
        try:
            reader = root.open_read(registration.path.name, sha256=sha256, size_bytes=size_bytes,
                expected_identity=registration.identity, cancelled=cancelled, deadline=deadline)
            # Transfer the verified legacy reader, so close releases reader before root.
            return _ReaderAdapter(reader._reader, owned_root=root)
        except BaseException:
            root.close()
            raise
