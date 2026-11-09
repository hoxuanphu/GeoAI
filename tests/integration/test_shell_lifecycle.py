"""Real Python dev sidecar smoke. Does not assert native ownership/Job Objects."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


class DevSidecarTests(unittest.TestCase):
    def start(self):
        process = subprocess.Popen([sys.executable, "-m", "geoai.bootstrap", "--dev-stdio-handoff", "--no-console"], cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "backend")}, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.cleanup, process)
        executor = concurrent.futures.ThreadPoolExecutor()
        try:
            descriptor = executor.submit(process.stdout.readline).result(timeout=15)
        finally:
            executor.shutdown(wait=False)
        self.assertTrue(descriptor, "trusted handoff missing")
        return process, json.loads(descriptor)

    def cleanup(self, process):
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)

    def get(self, descriptor, token=None, path="/v1/health"):
        request = urllib.request.Request(descriptor["base_url"] + path, headers={"Authorization": "Bearer " + (token or descriptor["token"])})
        return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=3)

    def test_trusted_pipe_handoff_authenticated_health_shutdown_and_no_secret_logs(self):
        process, descriptor = self.start()
        self.assertRegex(descriptor["base_url"], r"^http://127\.0\.0\.1:[0-9]+$")
        with self.get(descriptor) as response:
            self.assertEqual(json.load(response)["status"], "ok")
        with self.get(descriptor, path="/v1/capabilities") as response:
            result = json.load(response)
        for key in ("execution_owner_ready", "inference_ready", "project_writer_ready", "native_launcher_ready"):
            self.assertFalse(result[key])
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get(descriptor, token="stale-session")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get(descriptor, path="/v1/health?token=" + descriptor["token"])
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        process.stdin.write(b"shutdown\n"); process.stdin.flush()
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(process.returncode, 0)
        self.assertNotIn(descriptor["token"].encode(), stdout + stderr)
        self.assertNotIn(b"?token=", stdout + stderr)
        with self.assertRaises((urllib.error.URLError, ConnectionError, OSError)):
            self.get(descriptor)

    def test_pipe_eof_stops_process_and_each_launch_uses_a_fresh_token(self):
        first, a = self.start()
        first.stdin.close(); first.stdin = None
        first.communicate(timeout=10)
        self.assertEqual(first.returncode, 0)
        second, b = self.start()
        self.assertNotEqual(a["token"], b["token"])
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get(b, token=a["token"])
        self.assertEqual(error.exception.code, 401)
        error.exception.close()
        second.stdin.write(b"shutdown\n"); second.stdin.flush()
        second.communicate(timeout=10)

    def test_no_production_launcher_or_unrestricted_stdout_mode(self):
        for args in ([], ["--dev-stdio-handoff"], ["--no-console"]):
            result = subprocess.run([sys.executable, "-m", "geoai.bootstrap", *args], capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b"")
