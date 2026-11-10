# Task 6 repository and Task 9 NativeRoot I/O review

Date: 2026-11-09. Reviewed the current working-tree source, not the HEAD diff.
Scope: `storage/{guards,intents,db_models,repository,windows_io}.py`, initial
Alembic migration/env, and focused storage tests. This is a static review of
DB behavior because SQLAlchemy/Alembic are absent here. I did not install
packages, run integration suites, or change source.

## Findings

1. **P2: Old owner dependency leases cannot be retired after recovery.**
   `repository.py:476-489` permits `release_dependency_lease` only when the
   stored owner ID and epoch equal the current guard, while
   `dependency_retained` counts every active lease. After a process crash and
   new owner epoch, an old active lease remains retained indefinitely; no
   recovery method clears or transfers it after confirmed process stop.
   Repro when the DB extra is available: acquire lease at epoch 1, close,
   reopen at epoch 2, observe `release_dependency_lease` raises and
   `dependency_retained` remains true. This blocks GC for an otherwise
   releasable dependency. Add an owner-recovery lease transition gated by
   native stop observation; preserve pins independently.

2. **P2: Persisted attempt state diverges from job state.** `repository.py:373-406`
   sets `stop_confirmed` and terminal job states without updating
   `Attempt.state`; `repository.py:441` sets a published job to `succeeded`
   while its attempt remains `running`. A normal claim/publish/confirmed-stop
   sequence leaves an attempt row permanently marked running. A cancel then
   confirmed-stop sequence does the same. This weakens durable audit and any
   recovery process that reads attempts. Update attempt state in each terminal
   transition and assert the rows in the DB tests.

3. **P2: Restore accepts inconsistent job/attempt metadata that has valid SQLite
   integrity and foreign keys.** `db_models.py:16-63` has no state/assignment
   consistency constraint or foreign key from a job's current attempt fields
   to its attempt row. `repository.py:580-593` validates SQLite structural
   integrity and marks only `compute_allocated=1` jobs for recovery. For
   example, a backup with a `jobs` row changed to `state='running',
   compute_allocated=0, stop_confirmed=1` passes these checks; restore leaves
   it running without `recovery_required`. `claim` rejects it, while
   `reconcile_stopped` also rejects it, so the job cannot progress. Validate
   state/assignment/current-attempt invariants during restore and opening,
   with DB constraints where feasible.

## Scope and evidence limits

The NativeRoot path uses no-delete-sharing ancestor handles, rejects reparse
and multi-link files, hashes a pinned read handle, and creates files
exclusively with rollback by the same handle. The current `move_verified`
locks both roots in stable order, verifies the source before a same-volume
no-replace rename, and leaves successful rename unregistered until DB commit;
`delete_verified` also acts on the verified handle. I found no further concrete
defect in those reviewed methods. The recorded Task 9 I/O GREEN log reports
seven Windows tests passing; I did not rerun them while the parent/native work
was in flight.

The DB tests use real SQLite and skip explicitly when the optional DB extra is
missing. Task 6's report records 14 DB skips and zero DB behavior tests passed
on this host. The pending publisher, extraction, startup byte reconciliation,
and native process integration remain acceptance work, not findings against
this partial I/O adapter.
