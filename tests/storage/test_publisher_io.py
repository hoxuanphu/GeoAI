"""Real Windows files + pure coordinator; DB transaction tests are separate."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import importlib.util

import test_grant_registry as fixtures
from geoai.contracts import JobSpec, RunManifest
from geoai.jobs.coordinator import JobCoordinator, RetryPolicy
from geoai.jobs.publisher import Publisher, PublicationError
from geoai.storage.io_resolver import WorkerIOResolver
from geoai.storage.windows_io import NativeRoot, WindowsIOFactory


class FixtureGuard:
    owner_id, owner_epoch = "owner:1", 1
    def assert_held(self, project_id):
        if project_id != "project:1":
            raise ValueError("wrong project")


class MetadataRepository:
    """Explicit mechanism fixture, no claim of DB durability or transaction."""
    project_id = "project:1"
    def __init__(self, core):
        self.core = core
        self.artifacts = ()
        self.before_commit = lambda: None
    def get(self, job):
        return self.core.get(self.project_id, job)
    def publish(self, job, attempt, publication_id, artifacts):
        self.before_commit()
        result = self.core.publish(self.project_id, job, attempt, "owner:1", 1, publication_id)
        self.artifacts = artifacts
        return result


@unittest.skipUnless(os.name == "nt", "Windows handle publication required")
class PublisherIOTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.GrantTests()
        self.fixture.setUp()
        self.core = JobCoordinator(RetryPolicy(2, 0))
        self.core.enqueue(JobSpec.model_validate(self.fixture.job))
        self.attempt = self.core.claim("project:1", "job:1", owner_id="owner:1", owner_epoch=1)
        self.fixture.context['attempt'] = self.attempt.model_dump()
        self.fixture.refresh()
        self.fixture.register()
        self.fixture.registry.accept(self.fixture.start)
        self.temps = [tempfile.TemporaryDirectory() for _ in range(3)]
        self.staging, self.output, self.inputs = [NativeRoot(Path(t.name)) for t in self.temps]
        self.inputs.create_file("manifests/snapshot-1.json", [self.fixture.sb], max_bytes=len(self.fixture.sb))
        self.io_factory = WindowsIOFactory()
        self.registered_staging = self.io_factory.open_registered_root("staging", Path(self.temps[0].name), purpose="staging")
        self.registered_output = self.io_factory.open_registered_root("output", Path(self.temps[1].name), purpose="publication")
        self.registered_inputs = self.io_factory.open_registered_root("inputs", Path(self.temps[2].name), purpose="read")
        self.io = WorkerIOResolver(self.fixture.registry, {"root:1": self.registered_inputs}, {}, io_factory=self.io_factory)
        self.repo = MetadataRepository(self.core)
        self.publisher = Publisher(self.repo, self.fixture.registry, self.io,
            {"staging:1": self.registered_staging}, self.registered_output, FixtureGuard(),
            validator=lambda job, manifest: True, io_factory=self.io_factory)
        data = json.loads((Path(__file__).parents[1] / 'fixtures/contracts/workflow.json').read_text())['RunManifest']
        data.update(attempt=self.attempt.model_dump(), publication_state="candidate",
                    input_sha256=hashlib.sha256(self.fixture.sb).hexdigest(),
                    pipeline_sha256=self.fixture.context['read_entries'][3]['sha256'])
        # Select the workflow's independent allowlist binding explicitly.
        data['pipeline_sha256'] = self.fixture.registry.resolve('access:1', self.attempt, 'workflow:classify').sha256
        data['artifacts'][0].update(size_bytes=7, sha256=hashlib.sha256(b'payload').hexdigest())
        self.manifest = RunManifest.model_validate(data)
        self.staging.create_file("result.bin", [b"payload"], max_bytes=7)

    def tearDown(self):
        for root in (self.registered_staging, self.registered_output, self.registered_inputs,
                     self.staging, self.output, self.inputs):
            root.close()
        for temp in self.temps:
            temp.cleanup()

    def register(self, **changes):
        args = dict(candidate_id="candidate:1", context_id="access:1", project_id="project:1",
            attempt=self.attempt, staging_id="staging:1", manifest_bytes=self.manifest.model_dump_json().encode(),
            artifact_paths={"local:output:1": "result.bin"})
        args.update(changes)
        self.publisher.register_candidate(**args)

    def publish(self):
        return self.publisher.publish("candidate:1", "access:1", self.attempt, "publication:1")

    def test_success_moves_bytes_and_records_only_after_validation(self):
        self.register()
        self.assertEqual(self.publish().state, "succeeded")
        self.assertFalse((self.staging.path / "result.bin").exists())
        self.assertEqual(len(self.repo.artifacts), 2)  # output and immutable run manifest
        for _, path, checksum, size in self.repo.artifacts:
            with self.output.open_read(path, sha256=checksum, size_bytes=size):
                pass
        self.assertEqual(self.core.cancel('project:1', 'job:1').state, 'succeeded')

    def test_cancel_commit_race_leaves_unregistered_orphan(self):
        self.register()
        self.repo.before_commit = lambda: self.core.cancel('project:1', 'job:1')
        with self.assertRaises(PublicationError):
            self.publish()
        self.assertEqual(self.repo.artifacts, ())
        self.assertEqual(self.core.get('project:1', 'job:1').state, 'cancel_requested')
        self.assertTrue(any(self.output.path.rglob('*.bin')))

    def test_scope_stale_hash_and_manifest_relationship(self):
        with self.assertRaises(PublicationError):
            self.register(project_id='project:other')
        self.register()
        (self.staging.path / 'result.bin').write_bytes(b'changed')
        with self.assertRaises(PublicationError):
            self.publish()
        self.assertEqual(self.repo.artifacts, ())

    def test_unvalidated_profile_and_revocation_block_publication(self):
        self.publisher.validator = lambda job, manifest: False
        self.register()
        with self.assertRaises(PublicationError):
            self.publish()
        self.assertTrue((self.staging.path / 'result.bin').exists())
        self.publisher.validator = lambda job, manifest: True
        self.fixture.registry.revoke('access:1')
        with self.assertRaises(PublicationError):
            self.publish()

    def test_manifest_bytes_remain_locked_through_repository_commit(self):
        self.register()
        def try_mutation():
            output = next(self.output.path.rglob('*.bin'))
            with self.assertRaises(OSError):
                output.write_bytes(b'changed')
        self.repo.before_commit = try_mutation
        self.assertEqual(self.publish().state, 'succeeded')

    def test_snapshot_and_grid_mismatch_are_rejected_before_moves(self):
        self.manifest = self.manifest.model_copy(update={'grid_id': 'grid:wrong'})
        self.register()
        with self.assertRaises(PublicationError):
            self.publish()
        self.assertEqual(list(self.output.path.iterdir()), [])
        self.assertTrue((self.staging.path / 'result.bin').exists())


DB_AVAILABLE = all(importlib.util.find_spec(name) for name in ('sqlalchemy', 'alembic'))


@unittest.skipUnless(DB_AVAILABLE and os.name == 'nt', 'SQLAlchemy/Alembic and Windows required')
class PublisherDatabaseTests(unittest.TestCase):
    """Actual migrated SQLite plus Windows files when DB dependencies exist."""
    def setUp(self):
        from geoai.storage.repository import ProjectRepository, migrate_project
        from geoai.storage.resolver import GrantRegistry
        import test_repository as db_fixtures
        self.env = PublisherIOTests()
        self.env.setUp()
        self.addCleanup(self.env.tearDown)
        self.db_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.db_temp.cleanup)
        self.guard = db_fixtures.FixtureGuard('project:1')
        self.guard.owner_id = 'owner:1'
        self.addCleanup(self.guard.close)
        path = Path(self.db_temp.name) / 'project.sqlite'
        migrate_project(path, 'project:1', self.guard)
        self.repo = ProjectRepository.open(path, 'project:1', self.guard, RetryPolicy(2, 0))
        self.addCleanup(self.repo.close)
        self.repo.enqueue(JobSpec.model_validate(self.env.fixture.job))
        self.env.attempt = self.repo.claim('job:1')
        f = self.env.fixture
        f.context['attempt'] = self.env.attempt.model_dump()
        f.refresh()
        f.registry = GrantRegistry(worker_id='worker:1', launch_nonce='launch:1', project_id='project:1',
                                  execution_owner_id='owner:1', owner_epoch=1)
        f.register()
        f.registry.accept(f.start)
        self.env.manifest = self.env.manifest.model_copy(update={'attempt': self.env.attempt})
        self.env.publisher = Publisher(self.repo, f.registry,
            WorkerIOResolver(f.registry, {'root:1': self.env.registered_inputs}, {}, io_factory=self.env.io_factory),
            {'staging:1': self.env.registered_staging}, self.env.registered_output, self.guard,
            validator=lambda job, manifest: True, io_factory=self.env.io_factory)

    def test_publication_inventory_and_missing_byte_reconciliation(self):
        self.env.register()
        self.assertEqual(self.env.publish().state, 'succeeded')
        record = self.repo.get_publication('job:1')
        self.assertTrue(record.available)
        self.assertEqual(len(record.artifacts), 2)
        artifact = record.artifacts[0]
        self.env.output.delete_verified(artifact.relative_path, sha256=artifact.sha256, size_bytes=artifact.size_bytes)
        self.repo.reconcile_artifacts(self.env.publisher.verify_inventory_record)
        self.assertFalse(self.repo.get_publication('job:1').available)

    def test_cancel_before_database_commit_rejects_renamed_output(self):
        self.env.register()
        commit = self.repo.publish
        def cancel_then_commit(job, key, publication_id, artifacts):
            self.repo.cancel(job)
            return commit(job, key, publication_id, artifacts)
        self.repo.publish = cancel_then_commit
        with self.assertRaises(PublicationError):
            self.env.publish()
        self.assertIsNone(self.repo.get_publication('job:1'))
        self.assertTrue(any(self.env.output.path.rglob('*.bin')))
