"""Windows Job Object launcher with atomic job and handle-list assignment."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import threading
import time
import uuid


class NativeProcessError(RuntimeError):
    """A child could not be contained or its stop could not be proved."""


if os.name == "nt":
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    HANDLE = wintypes.HANDLE
    DWORD = wintypes.DWORD
    SIZE_T = ctypes.c_size_t
    LPVOID = ctypes.c_void_p
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
    JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
    PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002
    PROC_THREAD_ATTRIBUTE_JOB_LIST = 0x0002000D
    EXTENDED_STARTUPINFO_PRESENT = 0x00080000
    CREATE_UNICODE_ENVIRONMENT = 0x00000400
    CREATE_NO_WINDOW = 0x08000000
    STARTF_USESTDHANDLES = 0x00000100
    HANDLE_FLAG_INHERIT = 1
    WAIT_OBJECT_0 = 0
    WAIT_TIMEOUT = 258
    ERROR_INSUFFICIENT_BUFFER = 122

    class LARGE_INTEGER(ctypes.Structure):
        _fields_ = [("quad", ctypes.c_longlong)]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [("ReadOperationCount", ctypes.c_ulonglong), ("WriteOperationCount", ctypes.c_ulonglong), ("OtherOperationCount", ctypes.c_ulonglong), ("ReadTransferCount", ctypes.c_ulonglong), ("WriteTransferCount", ctypes.c_ulonglong), ("OtherTransferCount", ctypes.c_ulonglong)]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", LARGE_INTEGER), ("PerJobUserTimeLimit", LARGE_INTEGER), ("LimitFlags", DWORD), ("MinimumWorkingSetSize", SIZE_T), ("MaximumWorkingSetSize", SIZE_T), ("ActiveProcessLimit", DWORD), ("Affinity", SIZE_T), ("PriorityClass", DWORD), ("SchedulingClass", DWORD)]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", IO_COUNTERS), ("ProcessMemoryLimit", SIZE_T), ("JobMemoryLimit", SIZE_T), ("PeakProcessMemoryUsed", SIZE_T), ("PeakJobMemoryUsed", SIZE_T)]

    class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
        _fields_ = [("TotalUserTime", LARGE_INTEGER), ("TotalKernelTime", LARGE_INTEGER), ("ThisPeriodTotalUserTime", LARGE_INTEGER), ("ThisPeriodTotalKernelTime", LARGE_INTEGER), ("TotalPageFaultCount", DWORD), ("TotalProcesses", DWORD), ("ActiveProcesses", DWORD), ("TotalTerminatedProcesses", DWORD)]

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [("cb", DWORD), ("lpReserved", wintypes.LPWSTR), ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR), ("dwX", DWORD), ("dwY", DWORD), ("dwXSize", DWORD), ("dwYSize", DWORD), ("dwXCountChars", DWORD), ("dwYCountChars", DWORD), ("dwFillAttribute", DWORD), ("dwFlags", DWORD), ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD), ("lpReserved2", ctypes.c_void_p), ("hStdInput", HANDLE), ("hStdOutput", HANDLE), ("hStdError", HANDLE)]

    class STARTUPINFOEXW(ctypes.Structure):
        _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", LPVOID)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [("hProcess", HANDLE), ("hThread", HANDLE), ("dwProcessId", DWORD), ("dwThreadId", DWORD)]

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("nLength", DWORD), ("lpSecurityDescriptor", LPVOID), ("bInheritHandle", wintypes.BOOL)]

    def _api(name, args, result):
        fn = getattr(kernel, name)
        fn.argtypes, fn.restype = args, result
        return fn

    CreateJobObjectW = _api("CreateJobObjectW", [ctypes.POINTER(SECURITY_ATTRIBUTES), wintypes.LPCWSTR], HANDLE)
    SetInformationJobObject = _api("SetInformationJobObject", [HANDLE, ctypes.c_int, LPVOID, DWORD], wintypes.BOOL)
    QueryInformationJobObject = _api("QueryInformationJobObject", [HANDLE, ctypes.c_int, LPVOID, DWORD, ctypes.POINTER(DWORD)], wintypes.BOOL)
    TerminateJobObject = _api("TerminateJobObject", [HANDLE, DWORD], wintypes.BOOL)
    CloseHandle = _api("CloseHandle", [HANDLE], wintypes.BOOL)
    CreatePipe = _api("CreatePipe", [ctypes.POINTER(HANDLE), ctypes.POINTER(HANDLE), ctypes.POINTER(SECURITY_ATTRIBUTES), DWORD], wintypes.BOOL)
    SetHandleInformation = _api("SetHandleInformation", [HANDLE, DWORD, DWORD], wintypes.BOOL)
    InitializeProcThreadAttributeList = _api("InitializeProcThreadAttributeList", [LPVOID, DWORD, DWORD, ctypes.POINTER(SIZE_T)], wintypes.BOOL)
    UpdateProcThreadAttribute = _api("UpdateProcThreadAttribute", [LPVOID, DWORD, SIZE_T, LPVOID, SIZE_T, LPVOID, ctypes.POINTER(SIZE_T)], wintypes.BOOL)
    DeleteProcThreadAttributeList = _api("DeleteProcThreadAttributeList", [LPVOID], None)
    CreateProcessW = _api("CreateProcessW", [wintypes.LPCWSTR, wintypes.LPWSTR, LPVOID, LPVOID, wintypes.BOOL, DWORD, LPVOID, wintypes.LPCWSTR, ctypes.POINTER(STARTUPINFOEXW), ctypes.POINTER(PROCESS_INFORMATION)], wintypes.BOOL)
    WaitForSingleObject = _api("WaitForSingleObject", [HANDLE, DWORD], DWORD)

    _spawn_lock = threading.RLock()
    _OS_ENV = ("SystemRoot", "WINDIR", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "PROGRAMDATA")

    def _check(ok, code="native_process_failed"):
        if not ok:
            raise NativeProcessError(code)

    def _pipe():
        read, write = HANDLE(), HANDLE()
        security = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, True)
        _check(CreatePipe(ctypes.byref(read), ctypes.byref(write), ctypes.byref(security), 0), "pipe_creation_failed")
        return read, write

    def _file(handle, mode):
        import msvcrt
        flags = os.O_BINARY | (os.O_RDONLY if mode == "rb" else os.O_WRONLY)
        return os.fdopen(msvcrt.open_osfhandle(handle.value, flags), mode, buffering=0)

    def _environment(extra):
        if extra is None:
            extra = {}
        allowed = {key: os.environ[key] for key in _OS_ENV if key in os.environ}
        for key, value in extra.items():
            if key not in ("GEOAI_RUNTIME_HOME", "GEOAI_CONTEXT_ID") or not isinstance(value, str) or "\x00" in value:
                raise ValueError("unsupported_child_environment")
            allowed[key] = value
        if "SystemRoot" not in allowed:
            raise NativeProcessError("windows_environment_unknown")
        return ctypes.create_unicode_buffer("\x00".join(f"{k}={v}" for k, v in sorted(allowed.items(), key=lambda item: item[0].upper())) + "\x00\x00")


class ManagedProcess:
    def __init__(self, job, process, pid, stdin, stdout, stderr, owner=None):
        self._job, self._process, self.pid = job, process, pid
        self.stdin, self.stdout, self.stderr = stdin, stdout, stderr
        self._owner = owner
        self._closed = False
        self._lifecycle_lock = threading.RLock()
        self._group_confirmed_stopped = False
        self._stderr_thread = None
        self.stderr_bytes_seen = 0
        self.name = uuid.uuid4().hex

    @classmethod
    def launch(cls, executable, argv=(), environment=None, child_handles=(), job=None, owner=None):
        if os.name != "nt":
            raise NativeProcessError("windows_required")
        executable = Path(executable)
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError("trusted_absolute_executable_required")
        if any(not isinstance(arg, str) or "\x00" in arg for arg in argv):
            raise ValueError("invalid_process_argument")
        env = _environment(environment)
        if job is not None:
            raise NativeProcessError("external_job_unverified")
        owned_job = job is None
        if job is None:
            registered_name = None
            security_attrs = None
            if owner is not None:
                from geoai.storage.windows_owner import _sid
                registered_name = f"Global\\GeoAI-{_sid()}-{owner.owner_id}-{uuid.uuid4().hex}"
                security_attrs = ctypes.cast(ctypes.byref(owner._security.attributes), ctypes.POINTER(SECURITY_ATTRIBUTES))
            job = CreateJobObjectW(security_attrs, registered_name)
            _check(job, "job_creation_failed")
            limit = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            limit.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            try:
                _check(SetInformationJobObject(job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, ctypes.byref(limit), ctypes.sizeof(limit)), "job_configuration_failed")
            except BaseException:
                CloseHandle(job)
                raise
        stdin_read = stdin_write = stdout_read = stdout_write = stderr_read = stderr_write = None
        info = PROCESS_INFORMATION()
        attrs = None
        attrs_initialized = False
        registered = None
        try:
            stdin_read, stdin_write = _pipe()
            stdout_read, stdout_write = _pipe()
            stderr_read, stderr_write = _pipe()
            for parent_end in (stdin_write, stdout_read, stderr_read):
                _check(SetHandleInformation(parent_end, HANDLE_FLAG_INHERIT, 0), "pipe_inheritance_failed")
            inherited = [stdin_read, stdout_write, stderr_write]
            for handle in child_handles:
                if not isinstance(handle, int) or not handle:
                    raise ValueError("invalid_child_handle")
                inherited.append(handle)
            if len({h.value if isinstance(h, HANDLE) else h for h in inherited}) != len(inherited):
                raise ValueError("duplicate_child_handle")
            # Record intent before atomic process creation so a crash cannot create
            # an untracked child. The job handle itself is never inheritable.
            registered = cls(job, None, 0, None, None, None, owner)
            if registered_name is not None:
                registered.name = registered_name
            if owner is not None:
                owner.register_group(registered)
            size = SIZE_T()
            InitializeProcThreadAttributeList(None, 2, 0, ctypes.byref(size))
            if ctypes.get_last_error() != ERROR_INSUFFICIENT_BUFFER or not 0 < size.value <= 65536:
                raise NativeProcessError("process_attributes_unavailable")
            attrs = ctypes.create_string_buffer(size.value)
            _check(InitializeProcThreadAttributeList(attrs, 2, 0, ctypes.byref(size)), "process_attributes_unavailable")
            attrs_initialized = True
            handle_array = (HANDLE * len(inherited))(*inherited)
            job_array = (HANDLE * 1)(job)
            _check(UpdateProcThreadAttribute(attrs, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST, handle_array, ctypes.sizeof(handle_array), None, None), "handle_allowlist_unavailable")
            _check(UpdateProcThreadAttribute(attrs, 0, PROC_THREAD_ATTRIBUTE_JOB_LIST, job_array, ctypes.sizeof(job_array), None, None), "atomic_job_assignment_unavailable")
            startup = STARTUPINFOEXW()
            startup.StartupInfo.cb = ctypes.sizeof(startup)
            startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES
            startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = stdin_read, stdout_write, stderr_write
            startup.lpAttributeList = ctypes.cast(attrs, LPVOID)
            command = ctypes.create_unicode_buffer(subprocess.list2cmdline([str(executable), *argv]))
            with _spawn_lock:
                _check(CreateProcessW(str(executable), command, None, None, True,
                                      EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT | CREATE_NO_WINDOW,
                                      env, str(executable.parent), ctypes.byref(startup), ctypes.byref(info)), "contained_process_creation_failed")
            CloseHandle(info.hThread)
            info.hThread = None
            for child_end in (stdin_read, stdout_write, stderr_write):
                CloseHandle(child_end)
            stdin_read = stdout_write = stderr_write = None
            registered._process = info.hProcess
            registered.pid = info.dwProcessId
            registered.stdin = _file(stdin_write, "wb")
            stdin_write = None
            registered.stdout = _file(stdout_read, "rb")
            stdout_read = None
            registered.stderr = _file(stderr_read, "rb")
            stderr_read = None
            return registered
        except BaseException:
            if info.hProcess:
                TerminateJobObject(job, 1)
                WaitForSingleObject(info.hProcess, 5000)
                CloseHandle(info.hProcess)
            if registered is not None and owner is not None:
                try:
                    owner.group_stopped(registered)
                except BaseException:
                    pass  # Preserve the durable recovery-required record.
            if owned_job:
                CloseHandle(job)
            raise
        finally:
            if attrs_initialized:
                DeleteProcThreadAttributeList(attrs)
            for handle in (stdin_read, stdin_write, stdout_read, stdout_write, stderr_read, stderr_write, info.hThread):
                if handle:
                    CloseHandle(handle)

    def wait(self, deadline):
        end = time.monotonic() + max(0, deadline)
        while True:
            with self._lifecycle_lock:
                if self._closed or self._process is None:
                    return True
                remaining = max(0, end - time.monotonic())
                result = WaitForSingleObject(self._process, min(50, int(remaining * 1000)))
                if result == WAIT_OBJECT_0:
                    return True
                if result != WAIT_TIMEOUT:
                    raise NativeProcessError("process_state_unknown")
            if time.monotonic() >= end:
                return False

    def start_stderr_drain(self, max_count=65536):
        """Discard diagnostic bytes continuously; retain only a capped count."""
        if not isinstance(max_count, int) or max_count < 0 or max_count > 1_048_576:
            raise ValueError("invalid_stderr_limit")
        with self._lifecycle_lock:
            if self._closed or self._stderr_thread is not None or self.stderr is None:
                raise NativeProcessError("stderr_already_owned")

            def drain():
                while True:
                    chunk = self.stderr.read(4096)
                    if not chunk:
                        return
                    self.stderr_bytes_seen = min(max_count, self.stderr_bytes_seen + len(chunk))

            self._stderr_thread = threading.Thread(target=drain, daemon=True)
            self._stderr_thread.start()

    def _group_stopped_once_locked(self):
        if self._closed:
            return True
        if self._job is None:
            if self._group_confirmed_stopped:
                return True
            raise NativeProcessError("group_state_unknown")
        accounting = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
        _check(QueryInformationJobObject(self._job, JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION, ctypes.byref(accounting), ctypes.sizeof(accounting), None), "group_state_unknown")
        self._group_confirmed_stopped = accounting.ActiveProcesses == 0
        return self._group_confirmed_stopped

    def group_stopped(self, deadline):
        if os.name != "nt":
            return False
        end = time.monotonic() + max(0, deadline)
        while True:
            with self._lifecycle_lock:
                if self._group_stopped_once_locked():
                    return True
            if time.monotonic() >= end:
                return False
            time.sleep(min(0.025, end - time.monotonic()))

    def terminate_group(self, deadline=5):
        with self._lifecycle_lock:
            if self._closed:
                return True
            if not self._group_stopped_once_locked():
                _check(TerminateJobObject(self._job, 1), "group_termination_failed")
            if not self.group_stopped(deadline):
                return False
            self._close_locked()
            return True

    def close(self):
        with self._lifecycle_lock:
            self._close_locked()

    def _close_locked(self):
        if self._closed:
            return
        if not self._group_stopped_once_locked():
            raise NativeProcessError("group_still_active")
        if self._stderr_thread is not None:
            self._stderr_thread.join(timeout=5)
            if self._stderr_thread.is_alive():
                raise NativeProcessError("stderr_pipe_state_unknown")
        for stream in (self.stdin, self.stdout, self.stderr):
            if stream:
                stream.close()
        if self._owner:
            self._owner.group_stopped(self)
        if self._process:
            _check(CloseHandle(self._process), "process_handle_close_failed")
            self._process = None
        if self._job:
            _check(CloseHandle(self._job), "job_handle_close_failed")
            self._job = None
        self._closed = True
