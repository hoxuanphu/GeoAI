"""Windows kernel-backed owner and process containment smoke tests."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

from geoai.storage.windows_owner import ExecutionOwner, OwnershipError


@unittest.skipUnless(os.name == "nt", "Windows kernel primitives required")
class NativeOwnerTests(unittest.TestCase):
    def setUp(self):
        self.namespace = "test-" + uuid.uuid4().hex
        self.owner = ExecutionOwner._acquire_for_test(self.namespace)
        self.addCleanup(self.owner.close)

    def test_owner_contender_and_writer_lifetime(self):
        with self.assertRaises(OwnershipError):
            ExecutionOwner._acquire_for_test(self.namespace)
        code = "from geoai.storage.windows_owner import ExecutionOwner, OwnershipError; import sys;\ntry: ExecutionOwner._acquire_for_test(sys.argv[1]); sys.exit(2)\nexcept OwnershipError: sys.exit(0)"
        contender = subprocess.run([sys.executable, "-c", code, self.namespace], env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "backend")}, timeout=5)
        self.assertEqual(contender.returncode, 0)
        with tempfile.TemporaryDirectory(prefix="GeoAI-unicode-") as root:
            writer = self.owner.acquire_writer("project-1", Path(root))
            writer.assert_held("project-1")
            lease = writer.retain("project-1")
            with self.assertRaises(OwnershipError):
                writer.close()
            lease.close()
            writer.close()
            with self.assertRaises(OwnershipError):
                writer.assert_held("project-1")

    def test_project_identifier_contract_and_guard_identity_read_only(self):
        with tempfile.TemporaryDirectory() as root:
            writer = self.owner.acquire_writer("project:one.v1", Path(root))
            with self.assertRaises(AttributeError):
                self.owner.owner_epoch = 99
            with self.assertRaises(AttributeError):
                self.owner.owner_id = "forged"
            writer.close()

    def test_owner_release_refuses_writer(self):
        with tempfile.TemporaryDirectory() as root:
            writer = self.owner.acquire_writer("project-2", Path(root))
            with self.assertRaises(OwnershipError):
                self.owner.close()
            writer.close()

    def test_process_identity_and_recovery_record(self):
        self.assertGreater(self.owner.owner_epoch, 0)
        self.assertTrue(self.owner.owner_id)
        self.assertGreater(self.owner.process_creation_time, 0)
        self.assertGreaterEqual(self.owner.session_id, 0)

    def test_unclean_owner_without_workload_gets_new_epoch(self):
        namespace = "test-" + uuid.uuid4().hex
        code = "from geoai.storage.windows_owner import ExecutionOwner; import os,sys; ExecutionOwner._acquire_for_test(sys.argv[1]); os._exit(0)"
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "backend")}
        self.assertEqual(subprocess.run([sys.executable, "-c", code, namespace], env=env, timeout=5).returncode, 0)
        recovered = ExecutionOwner._acquire_for_test(namespace)
        self.assertEqual(recovered.owner_epoch, 2)
        recovered.close()

    def test_unclean_group_record_requires_recovery(self):
        namespace = "test-" + uuid.uuid4().hex
        code = "from geoai.storage.windows_owner import ExecutionOwner; import os,sys; o=ExecutionOwner._acquire_for_test(sys.argv[1]); o._record['groups']=['unverified']; from geoai.storage.windows_owner import _write_record; _write_record(o._root/'owner.json',o._record,o._security); os._exit(0)"
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "backend")}
        self.assertEqual(subprocess.run([sys.executable, "-c", code, namespace], env=env, timeout=5).returncode, 0)
        with self.assertRaisesRegex(OwnershipError, "recovery_required"):
            ExecutionOwner._acquire_for_test(namespace)

    def test_valid_but_missing_named_job_is_not_stop_proof(self):
        from geoai.storage.windows_owner import _old_groups_stopped, _sid
        name = f"Global\\GeoAI-{_sid()}-{self.owner.owner_id}-{uuid.uuid4().hex}"
        with self.assertRaisesRegex(OwnershipError, "recovery_required"):
            _old_groups_stopped([name], _sid(), self.owner.owner_id)

    def test_pid_creation_mismatch_does_not_identify_live_process(self):
        from geoai.storage.windows_owner import _old_process_alive
        self.assertFalse(_old_process_alive(os.getpid(), self.owner.process_creation_time + 1))

    def test_crashed_owner_with_missing_named_job_requires_recovery(self):
        namespace = "test-" + uuid.uuid4().hex
        code = "from geoai.storage.windows_owner import ExecutionOwner; from geoai.jobs.native_process import ManagedProcess; import os,sys; o=ExecutionOwner._acquire_for_test(sys.argv[1]); p=ManagedProcess.launch(sys.executable,['-c','import time;time.sleep(30)'],owner=o); print(p.pid,flush=True); os._exit(0)"
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "backend")}
        result = subprocess.run([sys.executable, "-c", code, namespace], env=env, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        with self.assertRaisesRegex(OwnershipError, "recovery_required"):
            ExecutionOwner._acquire_for_test(namespace)

    def test_recovery_evidence_requires_exact_prior_generation_and_live_writer(self):
        namespace = "test-" + uuid.uuid4().hex
        code = "from geoai.storage.windows_owner import ExecutionOwner; import os,sys; o=ExecutionOwner._acquire_for_test(sys.argv[1]); print(o.owner_id,o.owner_epoch,flush=True); os._exit(0)"
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "backend")}
        result = subprocess.run([sys.executable, "-c", code, namespace], env=env, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        old_id, old_epoch_text = result.stdout.decode().split()
        old_epoch = int(old_epoch_text)
        recovered = ExecutionOwner._acquire_for_test(namespace)
        self.addCleanup(recovered.close)
        with tempfile.TemporaryDirectory() as root:
            writer = recovered.acquire_writer("project-1", Path(root))
            self.addCleanup(writer.close)
            evidence = recovered.recovery_evidence(writer)
            self.assertIsNone(evidence.assert_stopped("project-1", old_id, old_epoch))
            for project, owner_id, epoch in (
                ("other-project", old_id, old_epoch),
                ("project-1", "wrong-owner", old_epoch),
                ("project-1", old_id, old_epoch + 1),
                ("project-1", old_id, True),
                ("project-1", recovered.owner_id, recovered.owner_epoch),
            ):
                with self.subTest(project=project, owner_id=owner_id, epoch=epoch):
                    with self.assertRaises(OwnershipError):
                        evidence.assert_stopped(project, owner_id, epoch)
            writer.close()
            with self.assertRaises(OwnershipError):
                evidence.assert_stopped("project-1", old_id, old_epoch)

    def test_no_prior_stop_proof_cannot_create_recovery_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            writer = self.owner.acquire_writer("project-1", Path(root))
            self.addCleanup(writer.close)
            with self.assertRaises(OwnershipError):
                self.owner.recovery_evidence(writer)
            writer.close()


if __name__ == "__main__":
    unittest.main()
