# Independent review: tasks 3-4

Date: 2026-11-09. Scope: current `backend/geoai/jobs/protocol.py` and
`coordinator.py`, `tests/jobs`, the task briefs, SPEC-004, IPC draft, ADR-009/011,
and RPC/JobSpec contracts. Reviewed whole selected files in the dirty workspace,
not a Git HEAD diff. Initial verdict: **fixes required**. The first two
findings were resolved in the scoped re-review below; finding 3 remains open.

## Findings

1. **P1 - Cancel can lose to an already recorded retryable failure.**
   `backend/geoai/jobs/coordinator.py:186-193`, `:223`, `:226-241`.
   `fail(..., retryable=True)` sets state `failed` and `retry_pending=True` while
   compute remains allocated. `cancel()` handles only `queued` and `running`, so a
   cancel request during the stop-confirmation window is ignored. A subsequent
   trusted `confirm_stopped()` requeues the job; a new attempt can start despite
   the cancellation. Repro using the workflow JobSpec fixture, `RetryPolicy(2, 0)`:
   `enqueue; claim; fail(retryable=True); cancel; confirm_stopped` prints
   `failed failed queued`. Record cancellation while failed/retry-pending and
   prevent requeue after stop confirmation; retain the stop requirement before
   releasing compute. Add the race-order test.

2. **P2 - The encoder can exceed the protocol's hard frame limit.**
   `backend/geoai/jobs/protocol.py:103-113`. `JsonLines` rejects a configured
   bound above 1,048,576 bytes, but `encode` accepts one and compares only with
   that caller-provided bound. Repro:
   `len(encode({'x': 'a' * MAX_FRAME_BYTES}, max_bytes=2_000_000))` returns
   `1,048,585`, which the standard reader must reject. Validate encoder bounds
   against `MAX_FRAME_BYTES` (including LF) and test an oversized override.

3. **P2 - Duplicate publication IDs across jobs in one project.**
   `backend/geoai/jobs/coordinator.py:244-250`. `publish()` checks only the
   current job's publication field. Repro with two fixture JobSpecs in the same
   project and distinct job/idempotency IDs: publish `publication:dup` for job 1,
   confirm its stop, claim job 2, and publish `publication:dup` again. Both calls
   succeed. Reject the second ID in the core to avoid ambiguous metadata; the
   eventual repository must also enforce uniqueness transactionally.

## Scoped re-review, 2026-11-09

Findings 1 and 2 are **approved as fixed**. `cancel()` now handles `failed`
while compute remains allocated, clears retry intent, and waits for trusted
`confirm_stopped()` before terminal cancellation. Direct reproduction now gives
`failed cancel_requested cancelled`; the new regression test also checks that
the job cannot be claimed again. `encode()` clamps the supplied bound to
`MAX_FRAME_BYTES`; the prior oversized frame raises `ValueError`. The updated
`tests/jobs` suite passes 16 tests. This re-review covers these two fixes only;
finding 3 remains pending.

## Final scoped re-review, 2026-11-09

Finding 3 is **approved as fixed** in the pure core. `publish()` now checks a
`(project_id, publication_id)` registry before recording success. The new
`test_publication_id_unique_within_project` confirms that a duplicate within
the project raises `JobConflict` without changing the second job from
`running`, that a distinct ID can publish, and that the same ID can be reused
in another project. `$env:PYTHONPATH='backend'; python -m unittest discover -s
tests/jobs -q` passed 17 tests, exit code 0. All three findings in this review
are now resolved for the in-memory metadata core. Persistent uniqueness and
transactional publish fencing still belong to the repository/publisher tasks.

## Verification and limits

`$env:PYTHONPATH='backend'; python -m unittest discover -s tests/jobs -q`:
15 tests passed before scoped fixes; 16 passed after them. During review the suite initially failed
because a known request with missing `params` returned -32600 instead of
-32602; the implementer corrected it, and the same suite now passes. Direct
reproductions of findings 1 and 2 now show the corrections. No source changes, installs,
commits, or further regression suite were performed by this reviewer.

The review assesses pure Python framing and metadata transitions only. It does
not establish OS pipe/native stdout behavior, trusted process-stop observation,
SQL transactions/unique constraints, candidate byte validation, atomic file
publication, recovery, or G0/G1 acceptance. `publish()` documents a trusted
validated-publication caller; that validation is not present in this core.
