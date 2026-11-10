"""Actual Windows Job Object process creation, not a subprocess mock."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from unittest import mock
import unittest

from geoai.jobs.native_process import ManagedProcess, NativeProcessError
from geoai.storage.windows_owner import ExecutionOwner, OwnershipError


@unittest.skipUnless(os.name == "nt", "Windows kernel primitives required")
class NativeProcessTests(unittest.TestCase):
    def test_launch_wait_and_group_stop(self):
        process = ManagedProcess.launch(Path(sys.executable), ["-c", "print('ready')"])
        self.addCleanup(process.terminate_group, 5)
        self.assertEqual(process.stdout.readline().strip(), b"ready")
        self.assertTrue(process.wait(5))
        self.assertTrue(process.group_stopped(5))
        process.close()

    def test_live_child_refuses_close_and_termination_is_bounded(self):
        process = ManagedProcess.launch(Path(sys.executable), ["-c", "import time; time.sleep(30)"])
        self.addCleanup(process.terminate_group, 5)
        with self.assertRaises(NativeProcessError):
            process.close()
        self.assertTrue(process.terminate_group(5))
        process.close()

    def test_executable_must_be_absolute(self):
        with self.assertRaises((ValueError, NativeProcessError)):
            ManagedProcess.launch(Path("python.exe"), ["-V"])

    def test_explicit_handle_list_excludes_inheritable_sentinel(self):
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
        kernel.CreateEventW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        handle = kernel.CreateEventW(None, True, False, None)
        self.assertTrue(handle)
        try:
            kernel.SetHandleInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
            kernel.SetHandleInformation.restype = wintypes.BOOL
            self.assertTrue(kernel.SetHandleInformation(handle, 1, 1))
            code = "import ctypes,sys; k=ctypes.WinDLL('kernel32'); k.SetEvent.argtypes=[ctypes.c_void_p]; k.SetEvent(int(sys.argv[1])); print('checked')"
            process = ManagedProcess.launch(Path(sys.executable), ["-c", code, str(handle)])
            self.addCleanup(process.terminate_group, 5)
            self.assertEqual(process.stdout.readline().strip(), b"checked")
            self.assertTrue(process.wait(5))
            self.assertTrue(process.group_stopped(5))
            self.assertEqual(kernel.WaitForSingleObject(handle, 0), 258)
            process.close()
        finally:
            kernel.CloseHandle(handle)

    def test_unicode_executable_path(self):
        with tempfile.TemporaryDirectory(prefix="GeoAI-ữ-") as directory:
            target = Path(directory) / "cmd.exe"
            import shutil
            shutil.copy2(Path(os.environ["SystemRoot"]) / "System32" / "cmd.exe", target)
            process = ManagedProcess.launch(target, ["/c", "echo unicode"])
            self.addCleanup(process.terminate_group, 5)
            self.assertEqual(process.stdout.readline().strip(), b"unicode")
            self.assertTrue(process.wait(5))
            self.assertTrue(process.group_stopped(5))
            process.close()

    def test_owner_release_waits_for_group(self):
        import uuid
        owner = ExecutionOwner._acquire_for_test("test-" + uuid.uuid4().hex)
        self.addCleanup(owner.close)
        process = ManagedProcess.launch(Path(sys.executable), ["-c", "import time;time.sleep(30)"], owner=owner)
        self.addCleanup(process.terminate_group, 5)
        with self.assertRaises(OwnershipError):
            owner.close()
        self.assertTrue(process.terminate_group(5))
        owner.close()

    def test_launcher_crash_closes_job_and_stops_child(self):
        code = "from geoai.jobs.native_process import ManagedProcess; import os,sys; p=ManagedProcess.launch(sys.executable,['-c','import time;time.sleep(30)']); print(p.pid,flush=True); os._exit(0)"
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "backend")}
        launcher = subprocess.run([sys.executable, "-c", code], env=env, stdout=subprocess.PIPE, timeout=5)
        self.assertEqual(launcher.returncode, 0)
        pid = int(launcher.stdout.strip())
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x101000, False, pid)
        if handle:
            try:
                self.assertEqual(kernel.WaitForSingleObject(handle, 5000), 0)
            finally:
                kernel.CloseHandle(handle)

    def test_atomic_attribute_failure_cleans_owner_intent(self):
        import uuid
        import geoai.jobs.native_process as native
        owner = ExecutionOwner._acquire_for_test("test-" + uuid.uuid4().hex)
        self.addCleanup(owner.close)
        with mock.patch.object(native, "UpdateProcThreadAttribute", return_value=0):
            with self.assertRaises(NativeProcessError):
                ManagedProcess.launch(Path(sys.executable), ["-V"], owner=owner)
        owner.close()

    def test_stderr_drain_does_not_block_or_keep_raw_diagnostics(self):
        process = ManagedProcess.launch(Path(sys.executable), ["-c", "import sys;sys.stderr.buffer.write(b'x'*200000);print('ready')"])
        self.addCleanup(process.terminate_group, 5)
        process.start_stderr_drain(max_count=1024)
        self.assertEqual(process.stdout.readline().strip(), b"ready")
        self.assertTrue(process.wait(5))
        self.assertTrue(process.group_stopped(5))
        process.close()
        self.assertEqual(process.stderr_bytes_seen, 1024)

    def test_concurrent_close_and_terminate_closes_each_native_handle_once(self):
        import geoai.jobs.native_process as native
        process = ManagedProcess.launch(Path(sys.executable), ["-c", "pass"])
        self.assertTrue(process.wait(5))
        self.assertTrue(process.group_stopped(5))
        original = native.CloseHandle
        process_handle = process._process.value if hasattr(process._process, "value") else process._process
        job_handle = process._job.value if hasattr(process._job, "value") else process._job
        counts = {process_handle: 0, job_handle: 0}
        entered, release = threading.Event(), threading.Event()
        gate = threading.Lock()
        failures = []

        def controlled_close(handle):
            raw = handle.value if hasattr(handle, "value") else handle
            with gate:
                counts[raw] = counts.get(raw, 0) + 1
                first = raw == process_handle and counts[raw] == 1
                duplicate = counts[raw] > 1
            if first:
                entered.set()
                release.wait(3)
            return 1 if duplicate else original(handle)

        def run(method):
            try:
                method()
            except BaseException as exc:
                failures.append(exc)

        with mock.patch.object(native, "CloseHandle", side_effect=controlled_close):
            first = threading.Thread(target=run, args=(process.close,))
            first.start()
            self.assertTrue(entered.wait(3))
            second = threading.Thread(target=run, args=(process.terminate_group,))
            second.start()
            time.sleep(0.05)
            release.set()
            first.join(5)
            second.join(5)
        self.assertFalse(first.is_alive() or second.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(counts[process_handle], 1)
        self.assertEqual(counts[job_handle], 1)
        self.assertTrue(process.wait(0))
        self.assertTrue(process.group_stopped(0))

    def test_attribute_list_second_initialization_failure_skips_delete(self):
        import geoai.jobs.native_process as native
        original = native.InitializeProcThreadAttributeList
        calls = 0

        def fail_second(*args):
            nonlocal calls
            calls += 1
            return original(*args) if calls == 1 else 0

        with mock.patch.object(native, "InitializeProcThreadAttributeList", side_effect=fail_second), \
             mock.patch.object(native, "DeleteProcThreadAttributeList") as delete:
            with self.assertRaisesRegex(NativeProcessError, "process_attributes_unavailable"):
                ManagedProcess.launch(Path(sys.executable), ["-V"])
        self.assertEqual(calls, 2)
        delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
