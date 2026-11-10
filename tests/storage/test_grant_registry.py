"""Metadata grant tests; no native permissions or file reads are asserted."""
from copy import deepcopy
import importlib
import json
from hashlib import sha256
from pathlib import Path
import unittest
from geoai.contracts import WorkerAccessContext, StartParams, JobSpec, InputSnapshot

ROOT = Path(__file__).resolve().parents[2]
F = json.loads((ROOT / 'tests/fixtures/contracts/workflow.json').read_text())
C = json.loads((ROOT / 'tests/fixtures/contracts/worker-access-context.json').read_text())
try:
    resolver = importlib.import_module('geoai.storage.resolver')
except ModuleNotFoundError:
    resolver = None

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

class GrantTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(resolver, 'metadata grant registry is not implemented')
        self.job = deepcopy(F['JobSpec']); self.snapshot = deepcopy(F['InputSnapshot'])
        self.context = deepcopy(C['WorkerAccessContext'])
        self.refresh()
        self.registry = resolver.GrantRegistry(worker_id='worker:1', launch_nonce='launch:1', project_id='project:1', execution_owner_id='owner:1', owner_epoch=1)

    def refresh(self):
        self.jb, self.sb = encoded(self.job), encoded(self.snapshot)
        c = self.context
        c['job_spec_sha256'], c['input_snapshot_sha256'] = sha256(self.jb).hexdigest(), sha256(self.sb).hexdigest()
        refs = {self.job['workflow_id'], self.job['grid_id'], *self.job['model_ids'], *self.job['physical_model_ids'], *self.job['parameter_snapshot_ids'], *self.snapshot['asset_ids'], self.snapshot['qa_policy_id'], *self.snapshot['transform_ids'], *self.snapshot['dependency_ids']}
        if self.snapshot.get('mosaic_recipe_id'): refs.add(self.snapshot['mosaic_recipe_id'])
        c['read_entries'] = c['read_entries'][:3]
        for entry, data in zip(c['read_entries'], (self.jb, self.sb)):
            entry['sha256'] = sha256(data).hexdigest(); entry['size_bytes'] = len(data)
        for ref in sorted(refs - {e['ref_id'] for e in c['read_entries']}):
            entry = deepcopy(c['read_entries'][0]); entry.update(ref_id=ref, kind='profile'); c['read_entries'].append(entry)
        self.cb = encoded(c)
        self.start = StartParams(attempt=c['attempt'], job_spec_id=c['job_spec_id'], input_snapshot_id=c['input_snapshot_id'], access_context_id=c['access_context_id'], access_context_sha256=sha256(self.cb).hexdigest(), resource_budget=c['resource_budget'])

    def register(self, **changes):
        args = dict(context_bytes=self.cb, job_bytes=self.jb, snapshot_bytes=self.sb, expected_start=self.start, required_ref_ids=())
        args.update(changes)
        return self.registry.register(**args)

    def test_managed_and_external_entries_resolve(self):
        self.register(); self.registry.accept(self.start)
        self.assertEqual(self.registry.resolve('access:1', self.start.attempt, 'job:1').location.kind, 'managed-local')
        self.assertEqual(self.registry.resolve('access:1', self.start.attempt, 'local:input:1').location.kind, 'external-registered-local')

    def test_exact_context_and_manifest_bytes_are_hashed(self):
        for field in ('context_bytes', 'job_bytes', 'snapshot_bytes'):
            with self.subTest(field=field), self.assertRaises(resolver.GrantError):
                self.register(**{field: dict(context_bytes=self.cb, job_bytes=self.jb, snapshot_bytes=self.sb)[field] + b' '})

    def test_full_launch_binding_matrix(self):
        for field, value in [('worker_id','worker:bad'),('launch_nonce','nonce:bad'),('project_id','project:bad'),('execution_owner_id','owner:bad'),('owner_epoch',2)]:
            c = deepcopy(self.context); c[field] = value
            with self.subTest(field=field), self.assertRaises(resolver.GrantError): self.register(context_bytes=encoded(c), expected_start=self.start.model_copy(update={'access_context_sha256':sha256(encoded(c)).hexdigest()}))

    def test_start_binding_matrix(self):
        self.register()
        for field, value in [('access_context_id','missing'),('access_context_sha256','b'*64),('input_snapshot_id','other'),('resource_budget',dict(cpu_threads=1,ram_bytes=1,temporary_bytes=0)),('attempt',dict(job_id='job:1',attempt_id='old',generation_token='old'))]:
            payload = self.start.model_dump(); payload[field] = value
            start = StartParams.model_validate(payload)
            with self.subTest(field=field), self.assertRaises(resolver.GrantError): self.registry.accept(start)
        self.registry.accept(self.start)

    def test_missing_explicit_and_manifest_dependencies(self):
        with self.assertRaises(resolver.GrantError): self.register(required_ref_ids=('absent',))
        c = deepcopy(self.context); c['read_entries'] = [e for e in c['read_entries'] if e['ref_id'] != self.job['model_ids'][0]]
        cb = encoded(c); start = self.start.model_copy(update={'access_context_sha256':sha256(cb).hexdigest()})
        with self.assertRaises(resolver.GrantError): self.register(context_bytes=cb, expected_start=start)

    def test_manifest_project_and_grid_must_match(self):
        for field in ('project_id','grid_id'):
            original = self.snapshot[field]; self.snapshot[field]='different'; self.refresh()
            with self.subTest(field=field), self.assertRaises(resolver.GrantError): self.register()
            self.snapshot[field]=original; self.refresh()

    def test_registration_snapshots_nested_mutable_intent(self):
        job = JobSpec.model_validate(self.job); snapshot = InputSnapshot.model_validate(self.snapshot)
        self.register(); job.parameters['evil'] = []; snapshot.band_mapping['evil']='bad'
        self.context['read_entries'][0]['location']['relative_path']='changed'
        self.registry.accept(self.start)
        self.assertNotEqual(self.registry.resolve('access:1', self.start.attempt, 'job:1').location.relative_path, 'changed')

    def test_one_use_revoke_and_duplicate_context(self):
        self.register()
        with self.assertRaises(resolver.GrantError): self.register()
        self.registry.accept(self.start)
        with self.assertRaises(resolver.GrantError): self.registry.accept(self.start)
        self.registry.revoke('access:1')
        for action in (lambda:self.registry.accept(self.start),lambda:self.registry.resolve('access:1',self.start.attempt,'job:1')):
            with self.assertRaises(resolver.GrantError): action()

    def test_next_attempt_requires_close_and_new_ids(self):
        self.register(); self.registry.accept(self.start)
        self.context['access_context_id']='access:2'; self.context['attempt']['attempt_id']='attempt:2'; self.context['attempt']['generation_token']='generation:2'; self.refresh()
        with self.assertRaises(resolver.GrantError): self.register()
        self.registry.revoke('access:1'); self.register(); self.registry.accept(self.start)
        self.assertEqual(self.registry.resolve('access:2',self.start.attempt,'job:1').ref_id,'job:1')
        self.registry.close()
        with self.assertRaises(resolver.GrantError): self.registry.resolve('access:2',self.start.attempt,'job:1')

    def test_unknown_ref_and_stale_attempt(self):
        self.register(); self.registry.accept(self.start)
        for ref in ('unknown','C:\\private\\file'):
            with self.assertRaises(resolver.GrantError) as caught: self.registry.resolve('access:1', self.start.attempt, ref)
            self.assertNotIn(ref,str(caught.exception))
        with self.assertRaises(resolver.GrantError): self.registry.resolve('access:1',self.start.attempt.model_copy(update={'generation_token':'old'}),'job:1')

    def test_candidate_scope_duplicate_and_revocation(self):
        self.register(); self.registry.accept(self.start)
        self.registry.register_candidate('candidate:1', 'access:1', project_id='project:1', attempt=self.start.attempt, staging_id='staging:1')
        self.assertEqual(self.registry.check_candidate('candidate:1', 'access:1', project_id='project:1', attempt=self.start.attempt), 'staging:1')
        for kwargs in [dict(project_id='other'), dict(staging_id='other'), dict(attempt=self.start.attempt.model_copy(update={'attempt_id':'old'})), dict(candidate_id='C:\\file')]:
            args=dict(candidate_id='candidate:2',access_context_id='access:1',project_id='project:1',attempt=self.start.attempt,staging_id='staging:1'); args.update(kwargs)
            with self.assertRaises(resolver.GrantError): self.registry.register_candidate(**args)
        with self.assertRaises(resolver.GrantError): self.registry.register_candidate('candidate:1','access:1',project_id='project:1',attempt=self.start.attempt,staging_id='staging:1')
        self.registry.revoke('access:1')
        with self.assertRaises(resolver.GrantError): self.registry.check_candidate('candidate:1','access:1',project_id='project:1',attempt=self.start.attempt)
    def test_revoked_attempt_cannot_be_regranted_under_new_context(self):
        self.register(); self.registry.revoke('access:1')
        self.context['access_context_id']='access:replay'; self.refresh()
        with self.assertRaises(resolver.GrantError): self.register()

    def test_context_attempt_binding_independent_of_hash(self):
        for field in ('attempt_id','generation_token'):
            c=deepcopy(self.context); c['attempt'][field]='changed'; cb=encoded(c)
            start=self.start.model_copy(update={'access_context_sha256':sha256(cb).hexdigest()})
            with self.subTest(field=field), self.assertRaises(resolver.GrantError): self.register(context_bytes=cb,expected_start=start)
