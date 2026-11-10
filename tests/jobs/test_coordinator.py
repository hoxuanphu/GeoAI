import json
import unittest
from pathlib import Path

from geoai.contracts import JobSpec
from geoai.jobs.coordinator import JobCoordinator, JobConflict, JobStateError, RetryPolicy, CheckpointIdentity


FIXTURE = Path(__file__).parents[1] / 'fixtures' / 'contracts' / 'workflow.json'


def spec(**changes):
    data = json.loads(FIXTURE.read_text(encoding='utf-8'))['JobSpec']
    data.update(changes)
    return JobSpec.model_validate(data)


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.core = JobCoordinator(RetryPolicy(max_attempts=2, backoff_seconds=3))

    def test_idempotency_scoped_and_immutable_intent(self):
        original = spec(parameters={'nested': {'value': 1}})
        first = self.core.enqueue(original)
        original.parameters['nested']['value'] = 9
        self.assertEqual(self.core.get('project:1', 'job:1').job_spec.parameters['nested']['value'], 1)
        self.assertEqual(self.core.enqueue(spec(parameters={'nested': {'value': 1}})), first)
        with self.assertRaises(JobConflict): self.core.enqueue(spec(job_id='job:2', parameters={'nested': {'value': 2}}))
        with self.assertRaises(JobConflict): self.core.enqueue(spec(idempotency_key='request:2'))
        self.core.enqueue(spec(job_id='job:1', project_id='project:2'))
        corrupted = spec(job_id='job:3', idempotency_key='request:3')
        corrupted.parameters['bad'] = float('inf')
        with self.assertRaises(ValueError): self.core.enqueue(corrupted)

    def test_claim_cancel_and_confirm_stop(self):
        self.core.enqueue(spec())
        attempt = self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1)
        self.assertEqual(self.core.get('project:1', 'job:1').state, 'running')
        self.core.cancel('project:1', 'job:1')
        self.assertEqual(self.core.get('project:1', 'job:1').state, 'cancel_requested')
        with self.assertRaises(JobStateError): self.core.publish('project:1', 'job:1', attempt, 'owner:1', 1, 'publication:1')
        self.core.cancel_ack('project:1', 'job:1', attempt, 'owner:1', 1)
        self.assertEqual(self.core.get('project:1', 'job:1').state, 'cancel_requested')
        self.assertTrue(self.core.get('project:1', 'job:1').compute_allocated)
        self.core.confirm_stopped('project:1', 'job:1', attempt, 'owner:1', 1)
        self.assertEqual(self.core.get('project:1', 'job:1').state, 'cancelled')
        self.assertFalse(self.core.get('project:1', 'job:1').compute_allocated)

    def test_retry_requires_stop_and_old_token_is_stale(self):
        self.core.enqueue(spec())
        first = self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1)
        self.core.fail('project:1', 'job:1', first, 'owner:1', 1, retryable=True)
        with self.assertRaises(JobStateError): self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1)
        self.assertFalse(self.core.progress('project:1', 'job:1', first, 'owner:1', 1, 2))
        self.core.confirm_stopped('project:1', 'job:1', first, 'owner:1', 1)
        self.assertEqual(self.core.get('project:1', 'job:1').state, 'queued')
        with self.assertRaises(JobStateError): self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1, elapsed_backoff_seconds=2)
        second = self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1, elapsed_backoff_seconds=3)
        self.assertNotEqual(first.generation_token, second.generation_token)
        self.assertFalse(self.core.progress('project:1', 'job:1', first, 'owner:1', 1, 3))
        self.assertFalse(self.core.candidate('project:1', 'job:1', first, 'owner:1', 1, 'candidate:old'))
        self.assertTrue(self.core.candidate('project:1', 'job:1', second, 'owner:1', 1, 'candidate:new'))
        self.assertEqual(self.core.get('project:1', 'job:1').candidate_manifest_id, 'candidate:new')
        with self.assertRaises(JobStateError): self.core.publish('project:1', 'job:1', first, 'owner:1', 1, 'publication:1')
        self.core.fail('project:1', 'job:1', second, 'owner:1', 1, retryable=True)
        self.core.confirm_stopped('project:1', 'job:1', second, 'owner:1', 1)
        self.assertEqual(self.core.get('project:1', 'job:1').state, 'failed')

    def test_cancel_after_retryable_failure_blocks_requeue(self):
        self.core.enqueue(spec())
        key = self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1)
        self.core.fail('project:1', 'job:1', key, 'owner:1', 1, retryable=True)
        self.assertEqual(self.core.cancel('project:1', 'job:1').state, 'cancel_requested')
        self.core.confirm_stopped('project:1', 'job:1', key, 'owner:1', 1)
        self.assertEqual(self.core.get('project:1', 'job:1').state, 'cancelled')
        with self.assertRaises(JobStateError): self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1, elapsed_backoff_seconds=3)

    def test_publish_then_late_cancel_and_queued_cancel(self):
        self.core.enqueue(spec())
        key = self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1)
        self.core.publish('project:1', 'job:1', key, 'owner:1', 1, 'publication:1')
        self.assertEqual(self.core.cancel('project:1', 'job:1').state, 'succeeded')
        with self.assertRaises(JobStateError): self.core.publish('project:1', 'job:1', key, 'owner:1', 1, 'publication:2')
        self.core.enqueue(spec(job_id='job:2', idempotency_key='request:2'))
        self.assertEqual(self.core.cancel('project:1', 'job:2').state, 'cancelled')

    def test_publication_id_unique_within_project(self):
        first = spec()
        second = spec(job_id='job:2', idempotency_key='request:2')
        self.core.enqueue(first)
        self.core.enqueue(second)
        key1 = self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1)
        self.core.publish('project:1', 'job:1', key1, 'owner:1', 1, 'publication:shared')
        self.core.confirm_stopped('project:1', 'job:1', key1, 'owner:1', 1)
        key2 = self.core.claim('project:1', 'job:2', owner_id='owner:1', owner_epoch=1)
        with self.assertRaises(JobConflict):
            self.core.publish('project:1', 'job:2', key2, 'owner:1', 1, 'publication:shared')
        self.assertEqual(self.core.get('project:1', 'job:2').state, 'running')
        self.core.publish('project:1', 'job:2', key2, 'owner:1', 1, 'publication:other')
        self.core.confirm_stopped('project:1', 'job:2', key2, 'owner:1', 1)
        self.core.enqueue(spec(project_id='project:2'))
        key3 = self.core.claim('project:2', 'job:1', owner_id='owner:1', owner_epoch=1)
        self.assertEqual(self.core.publish('project:2', 'job:1', key3, 'owner:1', 1, 'publication:shared').state, 'succeeded')

    def test_checkpoint_checks_every_identity(self):
        identity = CheckpointIdentity('input:a','model:a','config:a','runtime:a','grid:a')
        self.assertTrue(identity.compatible_with(identity))
        for field in ('input_sha256','model_sha256','config_sha256','runtime_id','grid_id'):
            other = {**identity.__dict__, field: 'other'}
            self.assertFalse(identity.compatible_with(CheckpointIdentity(**other)))

    def test_owner_context_and_dependency_retention(self):
        self.core.enqueue(spec())
        self.core.retain_dependency('project:1', 'job:1', 'asset:1')
        key = self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1)
        self.assertFalse(self.core.progress('project:1', 'job:1', key, 'owner:2', 1, 1))
        self.assertFalse(self.core.progress('project:1', 'job:1', key, 'owner:1', 2, 1))
        with self.assertRaises(JobStateError): self.core.publish('project:2', 'job:1', key, 'owner:1', 1, 'publication:1')
        self.core.cancel('project:1', 'job:1')
        self.core.confirm_stopped('project:1', 'job:1', key, 'owner:1', 1)
        self.assertEqual(self.core.get('project:1', 'job:1').retained_dependencies, frozenset({'asset:1'}))
        self.core.release_dependency('project:1', 'job:1', 'asset:1')
        self.assertFalse(self.core.get('project:1', 'job:1').retained_dependencies)

    def test_owner_epoch_is_positive_integer(self):
        self.core.enqueue(spec())
        with self.assertRaises(ValueError): self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch='epoch:1')
        with self.assertRaises(ValueError): self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=0)
        self.assertEqual(self.core.claim('project:1', 'job:1', owner_id='owner:1', owner_epoch=1).job_id, 'job:1')


if __name__ == '__main__': unittest.main()
