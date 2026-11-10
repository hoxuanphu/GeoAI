"""Windows account-wide execution owner and per-project writer guards.

All paths and lock names are derived locally. The optional namespace is reserved
for isolated integration tests; production callers use the fixed protocol name.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import uuid


class OwnershipError(RuntimeError):
    """Ownership is busy, uncertain, or no longer held."""


if os.name == "nt":
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    ole = ctypes.WinDLL("ole32", use_last_error=True)
    HANDLE = wintypes.HANDLE
    INVALID = ctypes.c_void_p(-1).value
    TOKEN_QUERY = 0x0008
    TOKEN_USER = 1
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_ALWAYS = 4
    CREATE_ALWAYS = 2
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_ATTRIBUTE_NORMAL = 0x80
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    ERROR_ALREADY_EXISTS = 183
    ERROR_FILE_NOT_FOUND = 2
    ERROR_INVALID_PARAMETER = 87
    MOVEFILE_REPLACE_EXISTING = 1
    MOVEFILE_WRITE_THROUGH = 8
    DACL_SECURITY_INFORMATION = 4
    SDDL_REVISION_1 = 1

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("nLength", wintypes.DWORD), ("lpSecurityDescriptor", ctypes.c_void_p), ("bInheritHandle", wintypes.BOOL)]

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("created", FILETIME), ("accessed", FILETIME), ("written", FILETIME), ("volume_serial", wintypes.DWORD), ("size_high", wintypes.DWORD), ("size_low", wintypes.DWORD), ("links", wintypes.DWORD), ("file_index_high", wintypes.DWORD), ("file_index_low", wintypes.DWORD)]

    def _api(dll, name, args, result):
        fn = getattr(dll, name)
        fn.argtypes, fn.restype = args, result
        return fn

    OpenProcessToken = _api(advapi, "OpenProcessToken", [HANDLE, wintypes.DWORD, ctypes.POINTER(HANDLE)], wintypes.BOOL)
    GetTokenInformation = _api(advapi, "GetTokenInformation", [HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL)
    ConvertSidToStringSidW = _api(advapi, "ConvertSidToStringSidW", [ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p)], wintypes.BOOL)
    ConvertStringSecurityDescriptorToSecurityDescriptorW = _api(advapi, "ConvertStringSecurityDescriptorToSecurityDescriptorW", [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL)
    GetFileSecurityW = _api(advapi, "GetFileSecurityW", [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL)
    ConvertSecurityDescriptorToStringSecurityDescriptorW = _api(advapi, "ConvertSecurityDescriptorToStringSecurityDescriptorW", [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL)
    GetCurrentProcess = _api(kernel, "GetCurrentProcess", [], HANDLE)
    GetCurrentProcessId = _api(kernel, "GetCurrentProcessId", [], wintypes.DWORD)
    ProcessIdToSessionId = _api(kernel, "ProcessIdToSessionId", [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL)
    GetProcessTimes = _api(kernel, "GetProcessTimes", [HANDLE, ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME)], wintypes.BOOL)
    OpenProcess = _api(kernel, "OpenProcess", [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], HANDLE)
    GetExitCodeProcess = _api(kernel, "GetExitCodeProcess", [HANDLE, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL)
    WaitForSingleObject = _api(kernel, "WaitForSingleObject", [HANDLE, wintypes.DWORD], wintypes.DWORD)
    CloseHandle = _api(kernel, "CloseHandle", [HANDLE], wintypes.BOOL)
    LocalFree = _api(kernel, "LocalFree", [ctypes.c_void_p], ctypes.c_void_p)
    SHGetKnownFolderPath = _api(shell, "SHGetKnownFolderPath", [ctypes.c_void_p, wintypes.DWORD, HANDLE, ctypes.POINTER(ctypes.c_wchar_p)], ctypes.c_long)
    CoTaskMemFree = _api(ole, "CoTaskMemFree", [ctypes.c_void_p], None)
    CreateDirectoryW = _api(kernel, "CreateDirectoryW", [wintypes.LPCWSTR, ctypes.POINTER(SECURITY_ATTRIBUTES)], wintypes.BOOL)
    GetFileAttributesW = _api(kernel, "GetFileAttributesW", [wintypes.LPCWSTR], wintypes.DWORD)
    CreateFileW = _api(kernel, "CreateFileW", [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(SECURITY_ATTRIBUTES), wintypes.DWORD, wintypes.DWORD, HANDLE], HANDLE)
    GetFileInformationByHandle = _api(kernel, "GetFileInformationByHandle", [HANDLE, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)], wintypes.BOOL)
    OpenJobObjectW = _api(kernel, "OpenJobObjectW", [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR], HANDLE)
    QueryInformationJobObject = _api(kernel, "QueryInformationJobObject", [HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL)
    WriteFile = _api(kernel, "WriteFile", [HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p], wintypes.BOOL)
    FlushFileBuffers = _api(kernel, "FlushFileBuffers", [HANDLE], wintypes.BOOL)
    MoveFileExW = _api(kernel, "MoveFileExW", [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD], wintypes.BOOL)

    # FOLDERID_LocalAppData (fixed Windows KNOWNFOLDERID bytes).
    LOCAL_APP_DATA = uuid.UUID("f1b32785-6fba-4fcf-9d55-7b8e7f157091").bytes_le

    def _check(ok, code="native_operation_failed"):
        if not ok:
            raise OwnershipError(code)

    def _filetime(value):
        return (value.high << 32) | value.low

    def _sid():
        token = HANDLE()
        _check(OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)))
        try:
            size = wintypes.DWORD()
            GetTokenInformation(token, TOKEN_USER, None, 0, ctypes.byref(size))
            if not 0 < size.value <= 4096:
                raise OwnershipError("invalid_account_identity")
            data = ctypes.create_string_buffer(size.value)
            _check(GetTokenInformation(token, TOKEN_USER, data, size, ctypes.byref(size)))
            pointer = ctypes.cast(data, ctypes.POINTER(ctypes.c_void_p))[0]
            result = ctypes.c_wchar_p()
            _check(ConvertSidToStringSidW(pointer, ctypes.byref(result)))
            try:
                return result.value
            finally:
                LocalFree(ctypes.cast(result, ctypes.c_void_p))
        finally:
            CloseHandle(token)

    def _local_app_data():
        folder = ctypes.c_wchar_p()
        raw = ctypes.create_string_buffer(LOCAL_APP_DATA)
        _check(SHGetKnownFolderPath(raw, 0, None, ctypes.byref(folder)) == 0)
        try:
            return Path(folder.value)
        finally:
            CoTaskMemFree(ctypes.cast(folder, ctypes.c_void_p))

    class _Security:
        def __init__(self, sid):
            self.descriptor = ctypes.c_void_p()
            self.sddl = f"D:P(A;;FA;;;{sid})"
            _check(ConvertStringSecurityDescriptorToSecurityDescriptorW(self.sddl, SDDL_REVISION_1, ctypes.byref(self.descriptor), None))
            self.attributes = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), self.descriptor, False)

        def close(self):
            if self.descriptor:
                LocalFree(self.descriptor)
                self.descriptor = None

    def _verify_private(path, sid):
        needed = wintypes.DWORD()
        GetFileSecurityW(str(path), DACL_SECURITY_INFORMATION, None, 0, ctypes.byref(needed))
        if not 0 < needed.value <= 65536:
            raise OwnershipError("private_acl_unknown")
        buffer = ctypes.create_string_buffer(needed.value)
        _check(GetFileSecurityW(str(path), DACL_SECURITY_INFORMATION, buffer, needed, ctypes.byref(needed)), "private_acl_unknown")
        text = ctypes.c_wchar_p()
        _check(ConvertSecurityDescriptorToStringSecurityDescriptorW(buffer, SDDL_REVISION_1, DACL_SECURITY_INFORMATION, ctypes.byref(text), None), "private_acl_unknown")
        try:
            if text.value != f"D:P(A;;FA;;;{sid})":
                raise OwnershipError("private_acl_mismatch")
        finally:
            LocalFree(ctypes.cast(text, ctypes.c_void_p))

    def _private_dir(path, security, sid):
        if not CreateDirectoryW(str(path), ctypes.byref(security.attributes)):
            if ctypes.get_last_error() != ERROR_ALREADY_EXISTS:
                raise OwnershipError("private_directory_failed")
        attributes = GetFileAttributesW(str(path))
        if attributes == 0xFFFFFFFF or attributes & FILE_ATTRIBUTE_REPARSE_POINT or not attributes & 0x10:
            raise OwnershipError("private_directory_invalid")
        _verify_private(path, sid)

    def _open(path, access, share, disposition, security=None, flags=FILE_ATTRIBUTE_NORMAL):
        attrs = ctypes.byref(security.attributes) if security else None
        result = CreateFileW(str(path), access, share, attrs, disposition, flags, None)
        if result in (None, INVALID):
            raise OwnershipError("resource_busy_or_unavailable")
        return result

    def _write_record(path, record, security):
        temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        handle = _open(temp, GENERIC_WRITE, 0, CREATE_ALWAYS, security)
        try:
            data = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
            if len(data) > 8192:
                raise OwnershipError("record_too_large")
            written = wintypes.DWORD()
            _check(WriteFile(handle, data, len(data), ctypes.byref(written), None) and written.value == len(data), "record_write_failed")
            _check(FlushFileBuffers(handle), "record_flush_failed")
        finally:
            CloseHandle(handle)
        _check(MoveFileExW(str(temp), str(path), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH), "record_commit_failed")

    def _process_identity(handle):
        a, b, c, d = FILETIME(), FILETIME(), FILETIME(), FILETIME()
        _check(GetProcessTimes(handle, ctypes.byref(a), ctypes.byref(b), ctypes.byref(c), ctypes.byref(d)), "process_identity_unknown")
        return _filetime(a)

    def _old_process_alive(pid, creation):
        handle = OpenProcess(0x101000, False, pid)  # SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            if ctypes.get_last_error() in (ERROR_FILE_NOT_FOUND, ERROR_INVALID_PARAMETER):
                return False
            raise OwnershipError("recovery_required")
        try:
            if _process_identity(handle) != creation:
                return False
            result = WaitForSingleObject(handle, 0)
            if result not in (0, 258):
                raise OwnershipError("recovery_required")
            return result == 258
        finally:
            CloseHandle(handle)

    def _directory_identity(path):
        handle = _open(path, 0x80, 0x7, OPEN_EXISTING, flags=FILE_FLAG_BACKUP_SEMANTICS)
        try:
            info = BY_HANDLE_FILE_INFORMATION()
            _check(GetFileInformationByHandle(handle, ctypes.byref(info)), "project_identity_unknown")
            if info.attributes & FILE_ATTRIBUTE_REPARSE_POINT:
                raise OwnershipError("project_root_reparse")
            return f"{info.volume_serial:08x}-{info.file_index_high:08x}{info.file_index_low:08x}"
        finally:
            CloseHandle(handle)

    class _BasicAccounting(ctypes.Structure):
        _fields_ = [("user", ctypes.c_longlong), ("kernel", ctypes.c_longlong),
                    ("period_user", ctypes.c_longlong), ("period_kernel", ctypes.c_longlong),
                    ("faults", wintypes.DWORD), ("total", wintypes.DWORD),
                    ("active", wintypes.DWORD), ("terminated", wintypes.DWORD)]

    def _old_groups_stopped(groups, sid, owner_id):
        if not isinstance(groups, list) or len(groups) > 256:
            raise OwnershipError("recovery_required")
        prefix = f"Global\\GeoAI-{sid}-{owner_id}-"
        for name in groups:
            if not isinstance(name, str) or not name.startswith(prefix) or not re.fullmatch(r"[0-9a-f]{32}", name[len(prefix):]):
                raise OwnershipError("recovery_required")
            handle = OpenJobObjectW(0x0004, False, name)  # JOB_OBJECT_QUERY
            if not handle:
                raise OwnershipError("recovery_required")
            try:
                accounting = _BasicAccounting()
                _check(QueryInformationJobObject(handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None), "recovery_required")
                if accounting.active:
                    raise OwnershipError("recovery_required")
            finally:
                CloseHandle(handle)


class GuardLease:
    def __init__(self, writer):
        self._writer = writer
        self._closed = False

    def assert_held(self, project_id):
        if self._closed:
            raise OwnershipError("guard_released")
        self._writer.assert_held(project_id)

    def close(self):
        with self._writer._owner._mutex:
            if not self._closed:
                self._writer._release_lease()
                self._closed = True


class ProjectWriter:
    def __init__(self, owner, project_id, identity, handle):
        self._owner, self._project_id, self._identity, self._handle = owner, project_id, identity, handle
        self._leases = 0
        self._closed = False

    @property
    def owner_id(self):
        return self._owner.owner_id

    @property
    def owner_epoch(self):
        return self._owner.owner_epoch

    def assert_held(self, project_id):
        with self._owner._mutex:
            if self._closed or self._owner._closed or project_id != self._project_id or self._owner._recovery_required:
                raise OwnershipError("guard_not_held")
            if _directory_identity(self._owner._project_roots[self._project_id]) != self._identity:
                raise OwnershipError("project_identity_changed")

    def retain(self, project_id):
        with self._owner._mutex:
            self.assert_held(project_id)
            self._leases += 1
        return GuardLease(self)

    def _release_lease(self):
        with self._owner._mutex:
            self._leases -= 1

    def close(self):
        with self._owner._mutex:
            if self._closed:
                return
            if self._leases:
                raise OwnershipError("writer_has_live_leases")
            CloseHandle(self._handle)
            self._closed = True
            self._owner._writers.pop(self._project_id, None)
            self._owner._project_roots.pop(self._project_id, None)


class _RecoveryEvidence:
    """Proof retained by the current kernel owner, bound to one live writer."""

    def __init__(self, owner, writer, prior_generation):
        self._owner = owner
        self._writer = writer
        self._prior_generation = prior_generation

    def assert_stopped(self, project_id, owner_id, owner_epoch):
        with self._owner._mutex:
            if (type(owner_epoch) is not int or not isinstance(owner_id, str)
                    or not isinstance(project_id, str)
                    or self._owner._closed or self._owner._recovery_required
                    or self._owner._prior_stopped_generation != self._prior_generation
                    or (owner_id, owner_epoch) != self._prior_generation
                    or owner_epoch >= self._owner.owner_epoch
                    or self._owner._writers.get(project_id) is not self._writer):
                raise OwnershipError("old_owner_stop_unproved")
            self._writer.assert_held(project_id)


class ExecutionOwner:
    def __init__(self, root, security, handle, record, prior_stopped_generation=None):
        self._root, self._security, self._handle = root, security, handle
        self._record = record
        self._mutex = threading.RLock()
        self._writers = {}
        self._project_roots = {}
        self._groups = {}
        self._closed = False
        self._recovery_required = False
        self._prior_stopped_generation = prior_stopped_generation
        self._owner_id = record["owner_id"]
        self._owner_epoch = record["epoch"]
        self.process_creation_time = record["creation_time"]
        self.session_id = record["session_id"]

    @property
    def owner_id(self):
        return self._owner_id

    @property
    def owner_epoch(self):
        return self._owner_epoch

    @classmethod
    def acquire(cls):
        return cls._acquire("v1")

    @classmethod
    def _acquire_for_test(cls, namespace):
        if not namespace.startswith("test-"):
            raise ValueError("test_namespace_required")
        return cls._acquire(namespace)

    @classmethod
    def _acquire(cls, namespace):
        if os.name != "nt":
            raise OwnershipError("windows_required")
        if not namespace or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in namespace):
            raise ValueError("invalid_namespace")
        sid = _sid()
        security = _Security(sid)
        try:
            base = _local_app_data()
            root = base / "GeoAI" / "execution-owner-v1" / sid / namespace
            for directory in (base / "GeoAI", base / "GeoAI" / "execution-owner-v1", base / "GeoAI" / "execution-owner-v1" / sid, root):
                _private_dir(directory, security, sid)
            handle = _open(root / "owner.lock", GENERIC_READ | GENERIC_WRITE, 0, OPEN_ALWAYS, security)
            try:
                _verify_private(root / "owner.lock", sid)
                record_path = root / "owner.json"
                prior_stopped_generation = None
                if record_path.exists():
                    _verify_private(record_path, sid)
                    try:
                        previous = json.loads(record_path.read_text(encoding="utf-8"))
                        epoch = previous["epoch"]
                        if not isinstance(epoch, int) or epoch < 1:
                            raise ValueError()
                        old_id = previous["owner_id"]
                        old_groups = previous["groups"]
                        old_pid = previous["pid"]
                        old_creation = previous["creation_time"]
                        if not isinstance(old_id, str) or not re.fullmatch(r"[0-9a-f]{32}", old_id):
                            raise ValueError()
                        if type(old_pid) is not int or old_pid <= 0 or type(old_creation) is not int or old_creation <= 0:
                            raise ValueError()
                        if previous["state"] == "active":
                            if _old_process_alive(old_pid, old_creation):
                                raise OwnershipError("recovery_required")
                            _old_groups_stopped(old_groups, sid, old_id)
                        elif previous["state"] == "closed":
                            if old_groups != []:
                                raise OwnershipError("recovery_required")
                        else:
                            raise ValueError()
                        prior_stopped_generation = (old_id, epoch)
                    except (KeyError, ValueError, TypeError) as exc:
                        raise OwnershipError("recovery_required") from exc
                else:
                    epoch = 0
                session = wintypes.DWORD()
                _check(ProcessIdToSessionId(GetCurrentProcessId(), ctypes.byref(session)))
                record = {"state": "active", "owner_id": uuid.uuid4().hex, "epoch": epoch + 1,
                          "pid": GetCurrentProcessId(), "creation_time": _process_identity(GetCurrentProcess()),
                          "session_id": session.value, "groups": []}
                _write_record(record_path, record, security)
                return cls(root, security, handle, record, prior_stopped_generation)
            except BaseException:
                CloseHandle(handle)
                raise
        except BaseException:
            security.close()
            raise

    def acquire_writer(self, project_id, trusted_project_root):
        if not isinstance(project_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}", project_id):
            raise ValueError("invalid_project_id")
        with self._mutex:
            if self._closed or self._recovery_required or self._writers:
                raise OwnershipError("owner_busy")
            root = Path(trusted_project_root)
            if not root.is_absolute() or not root.is_dir():
                raise OwnershipError("project_root_invalid")
            for ancestor in (root, *root.parents):
                attributes = GetFileAttributesW(str(ancestor))
                if attributes == 0xFFFFFFFF or attributes & FILE_ATTRIBUTE_REPARSE_POINT:
                    raise OwnershipError("project_root_reparse")
            identity = _directory_identity(root)
            digest = hashlib.sha256((project_id + "\0" + identity).encode()).hexdigest()
            handle = _open(self._root / (digest + ".lock"), GENERIC_READ | GENERIC_WRITE, 0, OPEN_ALWAYS, self._security)
            try:
                _verify_private(self._root / (digest + ".lock"), _sid())
                writer = ProjectWriter(self, project_id, identity, handle)
                self._writers[project_id] = writer
                self._project_roots[project_id] = root
                return writer
            except BaseException:
                CloseHandle(handle)
                raise

    def recovery_evidence(self, writer_guard):
        with self._mutex:
            if (self._closed or self._recovery_required or self._prior_stopped_generation is None
                    or not isinstance(writer_guard, ProjectWriter)
                    or writer_guard._owner is not self
                    or self._writers.get(writer_guard._project_id) is not writer_guard):
                raise OwnershipError("old_owner_stop_unproved")
            writer_guard.assert_held(writer_guard._project_id)
            return _RecoveryEvidence(self, writer_guard, self._prior_stopped_generation)

    def register_group(self, group):
        with self._mutex:
            if self._closed or self._recovery_required:
                raise OwnershipError("owner_not_held")
            self._groups[group.name] = group
            self._record["groups"] = list(self._groups)
            _write_record(self._root / "owner.json", self._record, self._security)

    def group_stopped(self, group):
        with self._mutex:
            if not group.group_stopped(0):
                raise OwnershipError("group_still_active")
            self._groups.pop(group.name, None)
            self._record["groups"] = list(self._groups)
            _write_record(self._root / "owner.json", self._record, self._security)

    def close(self):
        if os.name != "nt":
            return
        with self._mutex:
            if self._closed:
                return
            if self._writers or self._groups:
                raise OwnershipError("owner_has_live_resources")
            self._record["state"] = "closed"
            _write_record(self._root / "owner.json", self._record, self._security)
            CloseHandle(self._handle)
            self._security.close()
            self._closed = True
