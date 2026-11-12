from geoai.jobs.native_process import WindowsProcessFactory
"""Full synthetic process/files/SQLite composition; requires optional DB extra."""
import importlib.util
import json
import hashlib
import os
from pathlib import Path
import sys
import unittest
import uuid

DB_AVAILABLE = all(importlib.util.find_spec(name) for name in ('sqlalchemy', 'alembic'))


@unittest.skipUnless(DB_AVAILABLE and os.name == 'nt', 'SQLAlchemy/Alembic and Windows required')
class JobRecoveryTests(unittest.TestCase):
    def setUp(self):
        from tests.integration import test_worker_transport as fixture_module
        from geoai.storage.windows_owner import ExecutionOwner
        from geoai.storage.repository import migrate_project, ProjectRepository
        from geoai.jobs.coordinator import RetryPolicy
        from geoai.contracts import JobSpec, WorkerLaunchPacket
        self.fixture = fixture_module.WorkerTransportTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.owner = ExecutionOwner._acquire_for_test('test-' + uuid.uuid4().hex)
        self.addCleanup(self.owner.close)
        self.writer = self.owner.acquire_writer('project:1', self.fixture.root)
        self.addCleanup(self.writer.close)
        database = self.fixture.root / 'project.sqlite'
        migrate_project(database, 'project:1', self.writer)
        self.repo = ProjectRepository.open(database, 'project:1', self.writer, RetryPolicy(2, 0))
        self.addCleanup(self.repo.close)
        self.repo.enqueue(JobSpec.model_validate_json(self.fixture.payload['job_json']))
        self.key = self.repo.claim('job:1')
        context = json.loads(self.fixture.payload['context_json'])
        context.update(execution_owner_id=self.owner.owner_id, owner_epoch=self.owner.owner_epoch,
                       attempt=self.key.model_dump(mode='json'))
        context_json = fixture_module.compact(context)
        start = dict(self.fixture.payload['start'], attempt=self.key.model_dump(mode='json'),
                     access_context_sha256=hashlib.sha256(context_json.encode()).hexdigest())
        output = dict(self.fixture.payload['fixture_output'])
        output['manifest'] = dict(output['manifest'], attempt=self.key.model_dump(mode='json'))
        self.packet = WorkerLaunchPacket.model_validate(dict(self.fixture.payload,
            execution_owner_id=self.owner.owner_id, owner_epoch=self.owner.owner_epoch,
            context_json=context_json, start=start, fixture_output=output, fixture_mode='complete'))

    def run_worker(self):
        from geoai.jobs.transport import WorkerTransport
        self.transport = WorkerTransport.launch(Path(sys.executable), self.packet, owner=self.owner, process_factory=WindowsProcessFactory())
        self.addCleanup(self.transport.shutdown, .2, 5)
        self.transport.request('capabilities', {'protocol_version': '0.1.0', 'schema_version': '0.1.0'}, 5)
        accepted = self.transport.request('start', self.packet.start, 5)
        self.assertTrue(accepted.result['accepted'])
        for _ in range(256):
            if self.transport.next_event(5).method == 'completed':
                break
        else:
            self.fail('fixture did not complete')
        self.assertTrue(self.transport.shutdown(.2, 5))

    def publisher(self):
        from geoai.jobs.publisher import Publisher
        from geoai.storage.resolver import GrantRegistry
        from geoai.storage.io_resolver import WorkerIOResolver, ExternalRegistration
        from geoai.storage.windows_io import WindowsIOFactory, NativeIdentity
        p = self.packet
        grants = GrantRegistry(worker_id=p.bootstrap.worker_id, launch_nonce=p.bootstrap.launch_nonce,
            project_id=p.project_id, execution_owner_id=p.execution_owner_id, owner_epoch=p.owner_epoch)
        self.addCleanup(grants.close)
        grants.register(context_bytes=p.context_json.encode(), job_bytes=p.job_json.encode(),
            snapshot_bytes=p.snapshot_json.encode(), expected_start=p.start)
        grants.accept(p.start)
        io_factory = WindowsIOFactory()
        roots = {r.root_id: io_factory.open_registered_root(r.root_id, Path(r.absolute_path), purpose="read") for r in p.managed_roots}
        external = {r.registration_id: ExternalRegistration(Path(r.absolute_path),
            NativeIdentity(r.file_identity.volume_id, r.file_identity.file_id)) for r in p.external_registrations}
        staging = io_factory.open_registered_root("staging", Path(p.fixture_output.absolute_path), purpose="staging")
        destination = Path(self.fixture.temp.name) / 'published'
        destination.mkdir()
        output = io_factory.open_registered_root("output", destination, purpose="publication")
        for root in (*roots.values(), staging, output):
            self.addCleanup(root.close)
        publisher = Publisher(self.repo, grants, WorkerIOResolver(grants, roots, external, io_factory=io_factory),
            {p.fixture_output.staging_id: staging}, output, self.writer,
            validator=lambda job, manifest: True, io_factory=io_factory)  # Synthetic profile only.
        publisher.register_candidate(candidate_id=p.candidate_manifest_id,
            context_id=p.start.access_context_id, project_id=p.project_id, attempt=p.start.attempt,
            staging_id=p.fixture_output.staging_id,
            manifest_bytes=p.fixture_output.manifest.model_dump_json().encode(),
            artifact_paths={p.fixture_output.manifest.artifacts[0].asset_id: p.fixture_output.artifact_relative_path})
        return publisher

    def test_worker_file_publish_commit_and_late_cancel(self):
        self.run_worker()
        publisher = self.publisher()
        view = publisher.publish(self.packet.candidate_manifest_id, self.packet.start.access_context_id,
                                 self.key, 'publication:1')
        self.assertEqual(view.state, 'succeeded')
        self.assertTrue(self.repo.get_publication('job:1').available)
        self.assertEqual(self.repo.cancel('job:1').state, 'succeeded')
        self.repo.confirm_stopped('job:1', self.key)

    def test_cancel_after_rename_before_commit_retains_unserved_orphan(self):
        from geoai.jobs.publisher import PublicationError
        self.run_worker()
        publisher = self.publisher()
        commit = self.repo.publish
        def cancelled_commit(job_id, key, publication_id, artifacts):
            self.repo.cancel(job_id)
            return commit(job_id, key, publication_id, artifacts)
        self.repo.publish = cancelled_commit
        with self.assertRaises(PublicationError):
            publisher.publish(self.packet.candidate_manifest_id, self.packet.start.access_context_id,
                              self.key, 'publication:cancel')
        self.assertIsNone(self.repo.get_publication('job:1'))
        self.assertTrue(any(publisher.output.path.rglob('*.bin')))
        self.repo.confirm_stopped('job:1', self.key)
