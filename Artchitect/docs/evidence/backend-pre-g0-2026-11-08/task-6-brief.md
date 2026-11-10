# Task 6 — SQLAlchemy repository and Alembic migration

Read AGENTS.md, SPEC-004, architecture.md, ADR-002/011, ipc-protocol.md, Task4 report and coordinator.py before coding. This extends the authorized plan: user says skip environment deficiencies and generate complete code. Do not install/repair dependencies. Write production adapter and meaningful real-SQLite tests even if SQLAlchemy/Alembic are unavailable; report not-run separately. No subagents, Git, public writer/job routes, heavy model/GIS calls or global changes. Parent owns status docs.

## Deliverable and interfaces

- `storage/db_models.py`: SQLAlchemy 2 declarative tables for immutable job intent, attempts, one active assignment/project, one publication/job, artifact inventory, dependency pin/lease and recovery status. Use DB constraints, foreign keys and indexes, not just Python validation. Keep identity project-scoped consistently; no job lookup can silently target another project. Owner ID+epoch metadata and current attempt/token are explicit. Token/grant revocation and OS process-stop observation are separate fields. Never expose ORM across IPC.
- `storage/repository.py`: explicit project database initialization/open/close and transaction methods. `PRAGMA foreign_keys=ON`, WAL, bounded busy timeout; open only explicit trusted absolute local path, refuse network path and reparse/symlink where detectable. No production sqlite3 repository substitute and no `create_all` replacing migration. SQLAlchemy and Alembic optional extra in pyproject. Import storage package itself remains usable without DB dependency.
- `migrations/env.py`, initial revision and `alembic.ini`: one schema source synchronized with models. Upgrade under caller-held execution/project writer guard. Guard must be an application-internal lifetime-bearing interface supplied by native task; no public request boolean claiming ownership. If native adapter is not yet present, require explicit context-manager/guard protocol and document composition. Do not claim guard proves OS ownership until task7 supplies it.
- Durable methods enqueue/claim/current key/cancel/worker failure/confirmed stop/retry/conditional publication/lease/pin/reconcile views, compatible with Task4 semantics. Recheck full attempt key/current state and unique publication in the write transaction. Same project/key+same full canonical intent returns same job; different intent conflicts; duplicate job IDs never overwrite. Generate fresh attempts/tokens coordinator side. Retry bound explicit; never reassign if old process stop unknown, even after crash or expired heartbeat.
- Backup with SQLite online backup through DBAPI connection under a quiesced writer guard; do not raw-copy live db missing WAL. Restore validates schema version, foreign keys and metadata; running attempts become recovery-required and revoked, not running again. Existing active attempts at startup are not silently requeued; require native stop/reconcile. No filesystem existence implies publication.
- Persistence of leases/pins survives cancelled/failed attempt as retention demands; close/drop grant never deletes a dependency. Return immutable bytes or defensive validated records. Internal helper dataclasses need no new exchange schema; new serialized values must be canonical Pydantic with fixtures/exporter/docs.

## Test cycle

Write RED tests first, record command/exit including missing dependency if applicable; implement; compileall and existing dependency-free suites; attempt real tests once without installs. `tests/storage/test_migrations.py` and repository tests use SQLAlchemy+temporary on-disk SQLite, independent sessions, constraint violations and restart. No mocked SQL assertions or fake pass. Missing imports must produce explicit unittest skip for only dependency-required tests, with reason and counts in report; source still gets syntax checked. Test schema/index/FK migration/downgrade policy, project idempotency/conflict, mutation, duplicate ID, cancel/publish ordering, stale token after retry, unknown stop blocks dispatch, unique publication from competing connections, restart/recovery, retained leases, WAL-consistent backup and missing-byte availability metadata. Do not manufacture an old released migration fixture: draft initial version only.

Report `task-6-report.md` with APIs needed by publisher/worker composition, source/test list, actual executed pass/skip/not-run and logs, unverified adapter limitations. Native owner/transaction/filesystem/process acceptance remains unclosed until integrated tests run. Tests requiring unavailable DB packages are evidence of a remaining validation requirement, not reason to omit code.

## Continuation interface ruling

Read task-3-4-report.md (the combined report replaces the earlier separate Task4
report reference) and task-7-preflight.md. Implement the proposed WriterGuard and
GuardLease protocols in storage/guards.py: owner_id:str, owner_epoch:positive int,
assert_held(project_id), retain(project_id), lease.close(), guard.close(). Native
Task7 supplies the actual guard; repository tests use explicitly fixture guards.
Do not derive authority from a boolean or public request. The lease is retained
until all connections/transactions are closed. Storage may not import jobs;
factor shared canonical intent encoding into storage/intents.py and update the
coordinator's import if needed, preserving its public canonical_intent API and
digest profile. Do not duplicate state-machine implementation by serializing
an in-memory coordinator as the durable database. Every transition is checked
in the SQLAlchemy transaction against durable rows/constraints.
