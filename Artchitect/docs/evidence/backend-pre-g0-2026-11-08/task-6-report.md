# Task 6: SQLAlchemy repository and Alembic migration

Date: 2026-11-09. Scope: draft pre-G0 project metadata adapter. No DB packages
were installed, no native writer or publication integration was claimed.

## Source and composition API

- `backend/geoai/storage/guards.py`: internal `WriterGuard` and `GuardLease`
  protocols. The native Task 7 owner supplies the implementation; fixture
  guards in tests are not OS ownership evidence. Repository and migration
  retain leases through their connection lifetimes.
- `backend/geoai/storage/intents.py`: shared canonical `JobSpec` bytes and
  versioned digest profile. The existing coordinator exports the same names by
  import; its public behavior and digest remain unchanged.
- `backend/geoai/storage/db_models.py`: declarative job, attempt, publication,
  artifact, pin, lease and project tables. Composite project keys, foreign keys,
  unique request/token/publication constraints and one active assignment per
  project are in SQLite DDL. Owner generation, token revocation, stop observation
  and recovery state are separate columns.
- `migrations/env.py`, `migrations/versions/0001_initial.py`, `alembic.ini`:
  frozen initial DDL, entered only with a guarded application connection and
  retained lease. Existing DBs receive a SQLite online pre-migration backup.
  Downgrade is deliberately unsupported for this draft.
- `backend/geoai/storage/repository.py`: `migrate_project`,
  `ProjectRepository.open/close`, transactional `enqueue/get/claim/progress/
  candidate/cancel/fail/confirm_stopped/reconcile_stopped/publish`, dependency
  pin and lease methods, immutable publication/inventory/recovery views,
  `reconcile_artifacts(verifier)`, `backup`, and `restore_project`. All lookups
  use project scope. The publisher must validate actual bytes, hash, grid and
  candidate authority before `publish`; its trusted verifier callback may
  demote availability after a missing or mismatched byte check. The repository
  neither opens worker paths nor infers publication from file existence.

`confirm_stopped` and `reconcile_stopped` must be called only after Task 7's
native process-group observer has proved stop. Open with a newer owner epoch
marks old active attempts recovery-required and revoked; restore forces the
same treatment even when the guard generation is unchanged. Unknown stop blocks
claim. Cancel after a retryable failure clears pending retry and waits for stop.
Publish rechecks the complete current key, owner generation, state, revocation
and uniqueness in one SQLite write transaction. Pins and leases survive attempt
failure and cancellation.

## Verification run

Commands used `PYTHONPATH=backend` on Windows PowerShell:

| Command | Exit and observed result |
| --- | --- |
| `python -c "from geoai.storage.repository import ProjectRepository"` | exit 1, `ModuleNotFoundError: No module named 'alembic'`; optional DB extra unavailable |
| `python -m unittest discover -s tests/storage -p 'test_repository.py' -v` (first test run) | exit 0, 5 explicit DB skips; dependency blocker recorded before implementation |
| `python -m unittest discover -s tests/contracts -q` | exit 0, 57 passed |
| `python -m unittest discover -s tests/jobs -q` | exit 0, 17 passed after shared intent factoring |
| `python -m unittest discover -s tests/storage -v` (before concurrent native test appeared) | exit 0, 45 run: 32 passed, 13 DB skips |
| `python -m unittest discover -s tests/storage -q` (while Task 7 added tests) | exit 1, 47 run: 32 passed, 14 DB skips, 1 transient in-flight `test_windows_io` import error |
| `python -m unittest discover -s tests/storage -q` (after native module landed) | exit 0, 50 run: 36 passed, 14 DB skips |
| `python -m compileall -q backend/geoai/storage backend/geoai/jobs/coordinator.py migrations tests/storage` | exit 0 |

`tests/storage/test_repository.py` and `test_migrations.py` contain 14 real
on-disk SQLite tests with independent connections, schema/index/FK comparison,
idempotency conflicts, transaction fencing, cancel/publish ordering, retry,
restart/restore recovery, dependency retention, backup content and artifact
availability. They explicitly skip only when the SQLAlchemy/Alembic extra is
absent. Therefore no DB behavior test passed on this host; these tests must run
with the declared `db` extra before Task 6 can be accepted as runtime-verified.

## Remaining validation

Run the 14 DB tests with SQLAlchemy 2 and Alembic installed, inspect migration
autogeneration drift and exercise concurrent SQLite writers. Integrate the
native writer guard, process-group stop observer, publisher byte verifier and
artifact backup inventory. Native lock, filesystem durability, crash recovery,
upgrade of a released schema and G1 acceptance remain open.

## Review fix round 1

The static [Task 6 I/O review](task-6-io-review.md) found three repository
defects. `reconcile_owner_leases(old_owner_id, old_owner_epoch, evidence)` now
retires only the named earlier generation after an internal native
`OwnerStopEvidence.assert_stopped(project_id, owner_id, owner_epoch)` succeeds.
Normal release still rejects a different owner generation; dependency pins
remain independent. The native adapter has not yet supplied this evidence
object, so old leases remain retained until that integration is implemented.

Attempt rows now record `cancel_requested`, `cancelled`, `failed` and
`succeeded` through cancel, stop, recovery and publication transitions. Open
and restore reject inconsistent current attempt keys, owner identity, token and
stop state, attempt count, publication state, immutable intent, and job state.
The draft initial migration and ORM both include assignment/stop and active
state checks. Restore validates these semantics before copying the backup.

New regression cases cover stale lease refusal and exact stop provenance,
published/cancelled/recovered attempt rows, semantic corruption with valid
SQLite integrity, and DB rejection of a running job without allocated compute.
Initial focused RED command could only report 17 explicit DB skips because
SQLAlchemy and Alembic remain absent. After implementation:

| Command | Exit and observed result |
| --- | --- |
| `python -m unittest discover -s tests/storage -q` | exit 0, 64 run: 46 passed, 18 DB skips |
| `python -m unittest discover -s tests/jobs -q` | exit 0, 17 passed |
| `python -m compileall -q backend/geoai/storage migrations tests/storage` | exit 0 |
| `git diff --check -- backend/geoai/storage/repository.py backend/geoai/storage/db_models.py backend/geoai/storage/guards.py migrations/versions/0001_initial.py tests/storage/test_repository.py` | exit 0 |

A subsequent full storage discovery while the publisher agent was adding
`test_publisher_io.py` returned exit 1: 65 run, 18 DB skips and one import error
for its not-yet-landed `geoai.jobs.publisher`. Scoped Task 6 reruns returned
17 repository skips and one migration skip (exit 0); the stable Windows I/O
suite returned 7 passed (exit 0). This transient import is outside Task 6.

The 18 DB skips are still an unverified runtime requirement. The review fixes
are source-level until the optional DB extra is available and native stop
evidence is integrated.

## Final review lifetime fix

Final review found that concurrent `close()` could release the retained writer
lease while `engine.connect()` or online backup was in flight. The repository
now serializes lifecycle registration with an RLock and counts the operation
before acquiring a connection. Close refuses every active transaction/backup,
and commit rechecks the held guard. Backup also refuses a closed repository.
Two regressions coordinate connection/raw-connection acquisition against close;
they require real SQLAlchemy/SQLite and remain skipped here, as recorded in
[task-6-lifetime-not-run.log](task-6-lifetime-not-run.log). Syntax checking passed.
The shared native owner now supplies exact prior-generation stop evidence
through `owner.recovery_evidence(writer)`; missing Job Object proof fails closed.

Parent also added `collect_unretained` for Task 9: an explicit internal policy
and verified collector run under the SQLite write transaction, only after
compute stop and with no retained dependency pin/lease. Its DB test is also
unrun. This is source delivery pending DB runtime verification, not a pass.
