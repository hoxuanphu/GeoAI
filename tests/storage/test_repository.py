"""Real SQLite repository tests; only the optional DB extra may skip them."""
import importlib.util
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from geoai.contracts import JobSpec

DB_AVAILABLE = all(importlib.util.find_spec(name) for name in ("sqlalchemy", "alembic"))
if DB_AVAILABLE:
    from geoai.storage.repository import ProjectRepository, migrate_project, restore_project
    from geoai.jobs.coordinator import RetryPolicy
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError


class FixtureLease:
    def __init__(self, guard):
        self.guard = guard
        self.closed = False

    def assert_held(self, project_id):
        if self.closed:
            raise RuntimeError("closed lease")
        self.guard.assert_held(project_id)

    def close(self):
        if not self.closed:
            self.closed = True
            self.guard.leases -= 1


class FixtureGuard:
    owner_id = "owner:fixture"
    owner_epoch = 1

    def __init__(self, project_id):
        self.project_id = project_id
        self.closed = False
        self.leases = 0

    def assert_held(self, project_id):
        if self.closed or project_id != self.project_id:
            raise RuntimeError("writer unavailable")

    def retain(self, project_id):
        self.assert_held(project_id)
        self.leases += 1
        return FixtureLease(self)

    def close(self):
        if self.leases:
            raise RuntimeError("live leases")
        self.closed = True


class FixtureStopEvidence:
    def __init__(self, project_id, owner_id, owner_epoch):
        self.expected = (project_id, owner_id, owner_epoch)

    def assert_stopped(self, project_id, owner_id, owner_epoch):
        if (project_id, owner_id, owner_epoch) != self.expected:
            raise RuntimeError("stop provenance mismatch")


def spec(job_id="job:1", key="key:1"):
    return JobSpec(created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                   job_id=job_id, project_id="project:one", workflow_id="workflow:1",
                   workflow_version="v1", input_snapshot_id="input:1", grid_id="grid:1",
                   execution_kind="gis", parameters={}, compute_policy="cpu",
                   resource_budget={"cpu_threads": 1, "ram_bytes": 1024,
                                    "temporary_bytes": 0}, idempotency_key=key)


@unittest.skipUnless(DB_AVAILABLE, "SQLAlchemy and Alembic DB extra unavailable")
class RepositoryTests(unittest.TestCase):
    ARTIFACTS = (("asset:1", "artifacts/asset1.bin", "a" * 64, 3),)
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "project.sqlite"
        self.guard = FixtureGuard("project:one")
        migrate_project(self.db, "project:one", self.guard)
        self.repo = ProjectRepository.open(self.db, "project:one", self.guard, RetryPolicy(2, 0))

    def tearDown(self):
        self.repo.close()
        self.guard.close()
        self.tmp.cleanup()

    def test_idempotency_and_duplicate_ids(self):
        self.repo.enqueue(spec())
        self.assertEqual(self.repo.enqueue(spec()).job_id, "job:1")
        with self.assertRaises(ValueError):
            self.repo.enqueue(spec("job:2", "key:1"))
        with self.assertRaises(ValueError):
            self.repo.enqueue(spec("job:1", "key:2"))

    def test_cancel_after_failure_clears_retry_and_unknown_stop_blocks_claim(self):
        self.repo.enqueue(spec())
        key = self.repo.claim("job:1")
        self.repo.fail("job:1", key, retryable=True)
        self.assertEqual(self.repo.cancel("job:1").state, "cancel_requested")
        with self.assertRaises(ValueError):
            self.repo.claim("job:1")
        self.assertEqual(self.repo.confirm_stopped("job:1", key).state, "cancelled")

    def test_retry_fences_stale_publication_and_project_publication_ids(self):
        self.repo.enqueue(spec())
        old = self.repo.claim("job:1")
        self.repo.fail("job:1", old, retryable=True)
        self.repo.confirm_stopped("job:1", old)
        fresh = self.repo.claim("job:1")
        with self.assertRaises(ValueError):
            self.repo.publish("job:1", old, "publication:one")
        self.repo.publish("job:1", fresh, "publication:one", self.ARTIFACTS)
        self.repo.confirm_stopped("job:1", fresh)
        self.repo.enqueue(spec("job:2", "key:2"))
        other = self.repo.claim("job:2")
        with self.assertRaises(ValueError):
            self.repo.publish("job:2", other, "publication:one", self.ARTIFACTS)

    def test_restart_requires_reconciliation_and_retains_pin(self):
        self.repo.enqueue(spec())
        self.repo.retain_dependency("job:1", "input:1")
        self.repo.claim("job:1")
        self.repo.close()
        self.guard.owner_epoch = 2
        self.repo = ProjectRepository.open(self.db, "project:one", self.guard, RetryPolicy(2, 0))
        self.assertTrue(self.repo.get("job:1").recovery_required)
        self.assertIn("input:1", self.repo.get("job:1").retained_dependencies)
        with self.assertRaises(ValueError):
            self.repo.claim("job:1")

    def test_backup_is_wal_consistent(self):
        self.repo.enqueue(spec())
        backup = Path(self.tmp.name) / "backup.sqlite"
        self.repo.backup(backup)
        engine = create_engine(f"sqlite:///{backup.as_posix()}")
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT job_id FROM jobs")).scalar_one(), "job:1")
        engine.dispose()
        restored = Path(self.tmp.name) / "restored.sqlite"
        restore_project(backup, restored, "project:one", self.guard, RetryPolicy(2, 0))
        copy = ProjectRepository.open(restored, "project:one", self.guard, RetryPolicy(2, 0))
        try:
            self.assertEqual(copy.get("job:1").job_spec.job_id, "job:1")
        finally:
            copy.close()

    def test_restore_rejects_running_attempt_until_reconciled(self):
        self.repo.enqueue(spec())
        key = self.repo.claim("job:1")
        backup = Path(self.tmp.name) / "running-backup.sqlite"
        self.repo.backup(backup)
        restored = Path(self.tmp.name) / "running-restored.sqlite"
        restore_project(backup, restored, "project:one", self.guard, RetryPolicy(2, 0))
        copy = ProjectRepository.open(restored, "project:one", self.guard, RetryPolicy(2, 0))
        try:
            self.assertTrue(copy.get("job:1").recovery_required)
            self.assertTrue(copy.get("job:1").token_revoked)
            with self.assertRaises(ValueError):
                copy.claim("job:1")
            self.assertEqual(copy.reconcile_stopped("job:1", key).state, "failed")
        finally:
            copy.close()

    def test_cancel_wins_before_publish_and_late_cancel_preserves_publication(self):
        self.repo.enqueue(spec())
        key = self.repo.claim("job:1")
        self.repo.cancel("job:1")
        with self.assertRaises(ValueError):
            self.repo.publish("job:1", key, "publication:one", self.ARTIFACTS)
        self.repo.confirm_stopped("job:1", key)
        self.repo.enqueue(spec("job:2", "key:2"))
        second = self.repo.claim("job:2")
        self.repo.publish("job:2", second, "publication:two", self.ARTIFACTS)
        self.assertEqual(self.repo.cancel("job:2").state, "succeeded")

    def test_database_unique_constraints_and_independent_connection(self):
        self.repo.enqueue(spec())
        other = ProjectRepository.open(self.db, "project:one", self.guard, RetryPolicy(2, 0))
        try:
            with self.assertRaises(ValueError):
                other.enqueue(spec("job:2", "key:1"))
            engine = create_engine(f"sqlite:///{self.db.as_posix()}")
            with engine.connect() as conn:
                conn.exec_driver_sql("PRAGMA foreign_keys=ON")
                conn.commit()
                with self.assertRaises(IntegrityError):
                    conn.execute(text("INSERT INTO attempts (project_id,job_id,attempt_id,generation_token,owner_id,owner_epoch,state,token_revoked,stop_confirmed) VALUES ('project:one','missing','a','t','o',1,'running',0,0)"))
                conn.rollback()
            engine.dispose()
        finally:
            other.close()

    def test_pins_and_leases_outlive_failed_attempt(self):
        self.repo.enqueue(spec())
        self.repo.retain_dependency("job:1", "input:1")
        self.repo.acquire_dependency_lease("lease:one", "input:1")
        key = self.repo.claim("job:1")
        self.repo.fail("job:1", key, retryable=False)
        self.repo.confirm_stopped("job:1", key)
        self.repo.release_dependency("job:1", "input:1")
        self.assertTrue(self.repo.dependency_retained("input:1"))
        self.repo.release_dependency_lease("lease:one")
        self.assertFalse(self.repo.dependency_retained("input:1"))

    def test_missing_bytes_mark_publication_unavailable(self):
        self.repo.enqueue(spec())
        key = self.repo.claim("job:1")
        self.repo.publish("job:1", key, "publication:one", self.ARTIFACTS)
        self.assertEqual(self.repo.reconcile_artifacts(lambda record: False),
                         (("publication:one", "asset:1"),))
        self.assertFalse(self.repo.get("job:1").publication_available)
        self.assertFalse(self.repo.get_publication("job:1").available)
        self.assertEqual(self.repo.artifact_inventory("job:1")[0].sha256, "a" * 64)

    def test_second_connection_cannot_reuse_publication_id(self):
        self.repo.enqueue(spec())
        first = self.repo.claim("job:1")
        self.repo.publish("job:1", first, "publication:one", self.ARTIFACTS)
        self.repo.confirm_stopped("job:1", first)
        self.repo.enqueue(spec("job:2", "key:2"))
        second = self.repo.claim("job:2")
        competitor = ProjectRepository.open(self.db, "project:one", self.guard, RetryPolicy(2, 0))
        try:
            with self.assertRaises(ValueError):
                competitor.publish("job:2", second, "publication:one", self.ARTIFACTS)
            self.assertEqual(self.repo.get("job:2").state, "running")
        finally:
            competitor.close()

    def test_recovery_needs_old_stop_before_new_attempt(self):
        self.repo.enqueue(spec())
        old = self.repo.claim("job:1")
        self.repo.close()
        self.guard.owner_epoch = 2
        self.repo = ProjectRepository.open(self.db, "project:one", self.guard, RetryPolicy(2, 0))
        with self.assertRaises(ValueError):
            self.repo.claim("job:1")
        self.assertEqual(self.repo.reconcile_stopped("job:1", old).state, "failed")
        self.assertTrue(self.repo.get("job:1").stop_confirmed)
        engine = create_engine(f"sqlite:///{self.db.as_posix()}")
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT state FROM attempts WHERE job_id='job:1'")).scalar_one(), "failed")
        engine.dispose()

    def test_closed_guard_rejects_mutation(self):
        self.repo.enqueue(spec())
        self.guard.closed = True
        with self.assertRaises(RuntimeError):
            self.repo.cancel("job:1")
        self.guard.closed = False

    def test_old_owner_lease_requires_exact_stop_provenance(self):
        self.repo.enqueue(spec())
        self.repo.retain_dependency("job:1", "input:1")
        self.repo.acquire_dependency_lease("lease:old", "input:1")
        old_owner, old_epoch = self.guard.owner_id, self.guard.owner_epoch
        self.repo.close()
        self.guard.owner_id, self.guard.owner_epoch = "owner:new", 2
        self.repo = ProjectRepository.open(self.db, "project:one", self.guard, RetryPolicy(2, 0))
        with self.assertRaises(ValueError):
            self.repo.release_dependency_lease("lease:old")
        with self.assertRaises(RuntimeError):
            self.repo.reconcile_owner_leases(old_owner, old_epoch,
                FixtureStopEvidence("project:one", old_owner, 99))
        self.assertTrue(self.repo.dependency_retained("input:1"))
        self.assertEqual(self.repo.reconcile_owner_leases(old_owner, old_epoch,
            FixtureStopEvidence("project:one", old_owner, old_epoch)), 1)
        self.assertTrue(self.repo.dependency_retained("input:1"))
        self.repo.release_dependency("job:1", "input:1")
        self.assertFalse(self.repo.dependency_retained("input:1"))

    def test_attempt_state_tracks_publication_cancel_and_stop(self):
        self.repo.enqueue(spec())
        published = self.repo.claim("job:1")
        self.repo.publish("job:1", published, "publication:one", self.ARTIFACTS)
        self.repo.confirm_stopped("job:1", published)
        self.repo.enqueue(spec("job:2", "key:2"))
        cancelled = self.repo.claim("job:2")
        self.repo.cancel("job:2")
        self.repo.confirm_stopped("job:2", cancelled)
        engine = create_engine(f"sqlite:///{self.db.as_posix()}")
        with engine.connect() as conn:
            states = {job_id: state for job_id, state in conn.execute(text("SELECT job_id,state FROM attempts")).all()}
            self.assertEqual(states, {"job:1": "succeeded", "job:2": "cancelled"})
        engine.dispose()

    def test_open_and_restore_reject_semantically_corrupt_job(self):
        self.repo.enqueue(spec())
        self.repo.claim("job:1")
        backup = Path(self.tmp.name) / "corrupt-backup.sqlite"
        self.repo.backup(backup)
        with sqlite3.connect(backup) as conn:
            conn.execute("UPDATE jobs SET current_token='generation:corrupt' WHERE job_id='job:1'")
        with self.assertRaises(ValueError):
            restore_project(backup, Path(self.tmp.name) / "rejected.sqlite",
                            "project:one", self.guard, RetryPolicy(2, 0))
        self.repo.close()
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE jobs SET current_token='generation:corrupt' WHERE job_id='job:1'")
        with self.assertRaises(ValueError):
            ProjectRepository.open(self.db, "project:one", self.guard, RetryPolicy(2, 0))

    def test_db_check_rejects_running_without_compute(self):
        self.repo.enqueue(spec())
        self.repo.claim("job:1")
        engine = create_engine(f"sqlite:///{self.db.as_posix()}")
        with engine.connect() as conn:
            with self.assertRaises(IntegrityError):
                conn.execute(text("UPDATE jobs SET compute_allocated=0, stop_confirmed=1 WHERE job_id='job:1'"))
            conn.rollback()
        engine.dispose()

    def test_gc_holds_transaction_and_respects_compute_pin_and_lease(self):
        self.repo.enqueue(spec())
        called = []
        self.repo.retain_dependency('job:1', 'asset:garbage')
        self.assertFalse(self.repo.collect_unretained('asset:garbage', lambda: called.append('deleted'),
                                                    policy_id='retention:fixture'))
        self.assertEqual(called, [])
        self.repo.release_dependency('job:1', 'asset:garbage')
        self.repo.acquire_dependency_lease('lease:gc', 'asset:garbage')
        self.assertFalse(self.repo.collect_unretained('asset:garbage', lambda: called.append('deleted'),
                                                    policy_id='retention:fixture'))
        self.repo.release_dependency_lease('lease:gc')
        key = self.repo.claim('job:1')
        with self.assertRaises(ValueError):
            self.repo.collect_unretained('asset:garbage', lambda: called.append('deleted'), policy_id='retention:fixture')
        self.repo.fail('job:1', key, retryable=False)
        self.repo.confirm_stopped('job:1', key)
        self.assertTrue(self.repo.collect_unretained('asset:garbage', lambda: called.append('deleted'),
                                                   policy_id='retention:fixture'))
        self.assertEqual(called, ['deleted'])

    def test_close_refuses_inflight_connection_and_backup_acquisition(self):
        import threading
        from unittest.mock import patch
        for method_name, operation in (
                ('connect', lambda: self.repo.get('job:1')),
                ('raw_connection', lambda: self.repo.backup(Path(self.tmp.name) / 'blocked-backup.sqlite'))):
            with self.subTest(operation=method_name):
                if method_name == 'connect':
                    self.repo.enqueue(spec())
                entered, proceed = threading.Event(), threading.Event()
                errors = []
                original = getattr(self.repo.engine, method_name)
                def blocked(*args, **kwargs):
                    entered.set()
                    if not proceed.wait(5):
                        raise RuntimeError('test synchronization timed out')
                    return original(*args, **kwargs)
                def run():
                    try:
                        operation()
                    except BaseException as exc:
                        errors.append(exc)
                with patch.object(self.repo.engine, method_name, side_effect=blocked):
                    worker = threading.Thread(target=run)
                    worker.start()
                    try:
                        self.assertTrue(entered.wait(5))
                        with self.assertRaises(RuntimeError):
                            self.repo.close()
                        self.assertGreater(self.guard.leases, 0)
                    finally:
                        proceed.set()
                        worker.join(5)
                    self.assertFalse(worker.is_alive())
                    self.assertEqual(errors, [])

    def test_closed_repository_cannot_backup(self):
        self.repo.close()
        with self.assertRaises(RuntimeError):
            self.repo.backup(Path(self.tmp.name) / 'closed-backup.sqlite')

