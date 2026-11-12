"""Portable shared-service tests using an explicit memory registry, not OS proof."""
from datetime import datetime, timezone
import hashlib
import io
from pathlib import Path
import unittest
import zipfile
from unittest.mock import patch

from native_fixtures import MemoryFactory, MemoryRoot
from geoai.storage.native_io import StorageIOError, ExternalRegistration, NativeIdentity
from geoai.storage.io_resolver import WorkerIOResolver
from geoai.storage.extraction import extract_zip
from geoai.contracts.imports import ArchivePolicy


class SharedResolverTests(unittest.TestCase):
    def setUp(self):
        import test_grant_registry as fixtures
        self.fixture = fixtures.GrantTests(); self.fixture.setUp()
        self.fixture.register(); self.fixture.registry.accept(self.fixture.start)
        self.factory = MemoryFactory()
        self.root = self.factory.register('read', {
            'manifests/job-1.json': self.fixture.jb,
            'manifests/snapshot-1.json': self.fixture.sb})

    def test_unregistered_root_is_rejected_even_with_protocol_methods(self):
        with self.assertRaisesRegex(StorageIOError, 'unregistered_root'):
            WorkerIOResolver(self.fixture.registry, {'root:1': MemoryRoot({})}, {}, io_factory=self.factory)

    def test_registered_managed_read_and_closed_root(self):
        entry = self.fixture.context['read_entries'][0]
        self.root.files[entry['location']['relative_path']] = self.fixture.jb
        resolver = WorkerIOResolver(self.fixture.registry, {'root:1': self.root}, {}, io_factory=self.factory)
        with resolver.open_read('access:1', self.fixture.start.attempt, 'job:1') as reader:
            self.assertEqual(reader.read(), self.fixture.jb)
        self.root.close()
        with self.assertRaises(StorageIOError): resolver.open_read('access:1', self.fixture.start.attempt, 'job:1')

    def test_external_open_uses_factory_registration(self):
        entry = self.fixture.context['read_entries'][2]
        identity = entry['location']['file_identity']
        registration = ExternalRegistration(Path(entry['location']['absolute_path']),
                                            NativeIdentity(**identity))
        resolver = WorkerIOResolver(self.fixture.registry, {'root:1': self.root},
            {'registration:1': registration}, io_factory=self.factory)
        with resolver.open_read('access:1', self.fixture.start.attempt, 'local:input:1') as reader:
            self.assertEqual(reader.read(), b'external')
        self.assertIs(self.factory.external_calls[0], registration)


class SharedExtractionTests(unittest.TestCase):
    def setUp(self):
        self.factory = MemoryFactory()
        self.root = self.factory.register('staging')
        self.now = datetime(2026,11,11,tzinfo=timezone.utc)
        self.policy = ArchivePolicy(policy_id='policy:unit', created_at=self.now,
            max_archive_bytes=10000, max_entries=8, max_total_bytes=4096, max_entry_bytes=2048,
            max_path_depth=8, max_compression_ratio=100., max_seconds=10., chunk_bytes=64,
            allowed_extensions=('.txt',), nested_archives='reject')

    def source(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            archive.writestr('a.txt', b'a'); archive.writestr('b.txt', b'b')
        return stream.getvalue()

    def test_zip_copy_uses_one_deadline(self):
        inventory = extract_zip(self.source(), self.policy, self.root, io_factory=self.factory,
            inventory_id='inventory:unit', created_at=self.now, monotonic=lambda:100.)
        self.assertEqual(inventory.total_bytes, 2)
        self.assertEqual(self.root.files, {'a.txt':b'a','b.txt':b'b'})
        self.assertEqual(self.root.deadlines, [110.,110.])

    def test_unregistered_staging_cannot_extract(self):
        with self.assertRaisesRegex(StorageIOError,'unregistered_root'):
            extract_zip(self.source(), self.policy, MemoryRoot({}), io_factory=self.factory,
                inventory_id='inventory:unit',created_at=self.now)


class SharedCollectorTests(unittest.TestCase):
    def test_only_registered_staging_is_collectable(self):
        from geoai.storage.gc import DisposableCollector, DisposableFile
        factory = MemoryFactory()
        root = factory.register('staging', {'x':b'owned'})
        class Repository:
            def collect_unretained(self, dependency, delete, *, policy_id):
                delete(); return True
        collector = DisposableCollector(Repository(), root, policy_id='retention:unit', io_factory=factory)
        collector.register(DisposableFile('file:unit','x',hashlib.sha256(b'owned').hexdigest(),5))
        self.assertTrue(collector.collect('file:unit'))
        self.assertEqual(root.files,{})
        with self.assertRaises(StorageIOError):
            DisposableCollector(Repository(), MemoryRoot({}),policy_id='retention:unit',io_factory=factory)


class SharedPublisherTests(unittest.TestCase):
    def setUp(self):
        import json
        import test_grant_registry as fixtures
        from geoai.contracts import JobSpec, RunManifest
        from geoai.jobs.coordinator import JobCoordinator, RetryPolicy
        from geoai.jobs.publisher import Publisher
        from test_publisher_io import MetadataRepository, FixtureGuard
        self.fixture=fixtures.GrantTests(); self.fixture.setUp()
        self.core=JobCoordinator(RetryPolicy(2,0))
        self.core.enqueue(JobSpec.model_validate(self.fixture.job))
        self.attempt=self.core.claim('project:1','job:1',owner_id='owner:1',owner_epoch=1)
        self.fixture.context['attempt']=self.attempt.model_dump()
        self.fixture.refresh(); self.fixture.register(); self.fixture.registry.accept(self.fixture.start)
        self.factory=MemoryFactory()
        self.inputs=self.factory.register('read', {'manifests/snapshot-1.json':self.fixture.sb})
        self.staging=self.factory.register('staging', {'result.bin':b'payload'})
        self.output=self.factory.register('publication')
        self.repo=MetadataRepository(self.core)
        self.reader=WorkerIOResolver(self.fixture.registry,{'root:1':self.inputs},{},io_factory=self.factory)
        self.publisher=Publisher(self.repo,self.fixture.registry,self.reader,
            {'staging:1':self.staging},self.output,FixtureGuard(),validator=lambda job,manifest:True,io_factory=self.factory)
        data=json.loads((Path(__file__).parents[1]/'fixtures/contracts/workflow.json').read_text())['RunManifest']
        data.update(attempt=self.attempt.model_dump(),publication_state='candidate',
            input_sha256=hashlib.sha256(self.fixture.sb).hexdigest(),
            pipeline_sha256=self.fixture.registry.resolve('access:1',self.attempt,'workflow:classify').sha256)
        data['artifacts'][0].update(size_bytes=7,sha256=hashlib.sha256(b'payload').hexdigest())
        manifest=RunManifest.model_validate(data)
        self.publisher.register_candidate(candidate_id='candidate:1',context_id='access:1',project_id='project:1',
            attempt=self.attempt,staging_id='staging:1',manifest_bytes=manifest.model_dump_json().encode(),
            artifact_paths={'local:output:1':'result.bin'})

    def test_scheduling_between_services_never_extends_deadline(self):
        from geoai.jobs import publisher
        readings = iter([100.,100.,100.,104.,108.])
        with patch.object(publisher.time,'monotonic',side_effect=lambda: next(readings,108.)):
            view = self.publisher.publish('candidate:1','access:1',self.attempt,'publication:1',deadline_seconds=10)
        self.assertEqual(view.state,'succeeded')
        self.assertEqual(self.inputs.deadlines,[110.])

    def test_invalid_verification_budget_is_not_missing_bytes(self):
        from types import SimpleNamespace
        record=SimpleNamespace(relative_path='x',sha256='0'*64,size_bytes=1)
        with self.assertRaises(StorageIOError):
            self.publisher.verify_inventory_record(record,deadline_seconds=0)

    def test_one_publication_budget_and_verified_bytes(self):
        from geoai.jobs import publisher
        with patch.object(publisher.time,'monotonic',return_value=100.):
            view=self.publisher.publish('candidate:1','access:1',self.attempt,'publication:1',deadline_seconds=10)
        self.assertEqual(view.state,'succeeded')
        self.assertEqual(len(self.repo.artifacts),2)
        self.assertFalse(self.staging.files)
        self.assertEqual(self.staging.deadlines,[110.,110.])
        self.assertTrue(self.output.deadlines)
        self.assertEqual(set(self.output.deadlines),{110.})

    def test_cancelled_publication_keeps_candidate_unpublished(self):
        from geoai.jobs.publisher import PublicationError
        with self.assertRaises(PublicationError):
            self.publisher.publish('candidate:1','access:1',self.attempt,'publication:1',cancelled=lambda:True)
        self.assertEqual(self.staging.files,{'result.bin':b'payload'})
        self.assertEqual(self.output.files,{})
        self.assertEqual(self.repo.artifacts,())


class ReconciliationAbortTests(unittest.TestCase):
    def test_cancelled_sqlite_reconciliation_rolls_back_prior_demotion(self):
        import test_repository as fixture
        if not fixture.DB_AVAILABLE: self.skipTest('DB extra unavailable')
        from geoai.jobs.publisher import Publisher
        db=fixture.RepositoryTests(); db.setUp(); self.addCleanup(db.tearDown)
        db.repo.enqueue(fixture.spec())
        key=db.repo.claim('job:1')
        digest=hashlib.sha256(b'abc').hexdigest()
        db.repo.publish('job:1',key,'publication:one',
            (('asset:a','a',digest,3),('asset:b','b',digest,3)))
        factory=MemoryFactory()
        output=factory.register('publication',{'a':b'bad','b':b'abc'})
        publisher=Publisher(db.repo,None,None,{},output,db.guard,
                            validator=lambda job,manifest:True,io_factory=factory)
        calls=[]
        def verify(record):
            calls.append(record.asset_id)
            if len(calls)==2:
                raise_cancel=lambda: True
            else:
                raise_cancel=lambda: False
            return publisher.verify_inventory_record(record,cancelled=raise_cancel)
        with self.assertRaises(StorageIOError): db.repo.reconcile_artifacts(verify)
        self.assertEqual(len(calls),2)
        self.assertTrue(db.repo.get_publication('job:1').available)
        self.assertTrue(all(record.available for record in db.repo.artifact_inventory('job:1')))
