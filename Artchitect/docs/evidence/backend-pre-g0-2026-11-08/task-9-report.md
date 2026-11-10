# Task 9 — Native file I/O, extraction and publisher composition

Date: 09/11/2026, Asia/Bangkok. Source delivered for independent review; this
report does not close SPEC-004/009 or G1.

## Implementation

- `storage/windows_io.py`: internally registered `NativeRoot`, deny-delete
  ancestor pins, opened-file identity/final path/link checks, bounded hashing,
  read-only readers denying concurrent write/delete, exclusive bounded writes,
  rollback/delete by verified handle and same-volume no-overwrite rename by
  handle. Readers retain root lifetime. Unsupported platforms/volumes/reparse
  paths fail closed. No driver, model or provider is loaded.
- `storage/io_resolver.py`: `WorkerIOResolver` checks an accepted GrantRegistry
  ref before opening managed input or an independently registered external file.
  External registration must match exact path/native identity/hash. No generic
  public path API is provided; grant revocation does not claim to close an
  already-open handle or sandbox a hostile process of the same account.
- `storage/extraction.py`: inspect all immutable ZIP bytes under the existing
  policy before writing, then extract in bounded chunks under one total
  deadline/cancel budget. Recheck inventory/hash, never overwrite, roll back
  only newly written files by verified handles. Empty unregistered directories
  may remain for recovery. Inventory is not an activated asset/model pack.
- `jobs/publisher.py`: trusted registration snapshots candidate manifest/path
  bindings, checks accepted grant/project/attempt, snapshot/grid/transforms/
  model/pipeline identities and a mandatory trusted profile/coverage validator.
  It verifies files before moving, writes an immutable published RunManifest,
  then holds all verified output handles through repository commit. The
  repository must recheck token/owner/state/uniqueness transactionally. A cancel
  or crash after rename leaves unserved orphans; no file is auto-promoted.
- `storage/gc.py` and repository `collect_unretained`: internal disposable-file
  registrations plus explicit retention policy ID. Reject active compute and
  retained pin/lease, hold the DB write transaction during verified deletion,
  demote availability. No source directory traversal, default retention budget
  or automatic deletion policy is selected.

`Publisher.verify_inventory_record` is the native verifier callback for
repository reconciliation; it can demote missing/mismatched bytes only. Asset
serving still needs a registered available publication plus a verified reader.

## Actual checks

PowerShell with `PYTHONPATH=backend`:

| Check | Observed result |
| --- | --- |
| `unittest discover -s tests/storage -p test_windows_io.py -q` | 7 Windows tests pass; [I/O log](task-9-io-green.log), [rename/delete log](task-9-move-green.log) |
| `unittest discover -s tests/storage -p test_extraction.py -q` | 4 pass; [log](task-9-extraction-green.log) |
| `unittest discover -s tests/storage -p test_worker_io.py -q` | 3 pass; real GrantRegistry + files; [log](task-9-resolver-green.log) |
| `unittest discover -s tests/storage -p test_publisher_io.py -q` | 6 pass using real files and explicit metadata-core repository fixture, 2 SQLite integration skips; [log](task-9-publisher-green.log) |
| GC repository regression | Dependency-required test added; not run because SQLAlchemy/Alembic absent; [log](task-9-gc-not-run.log) |
| `unittest discover -s tests/architecture -q` / `compileall -q backend migrations` | 2 import tests pass / syntax exit 0 |

RED logs exist for missing I/O/extraction/resolver/publisher APIs, rename/delete,
and mutation during commit. The latter failed before output handles were held
through commit, then passed in [GREEN](task-9-commit-handle-green.log).

The Windows tests exercise Unicode paths, read sharing, ancestor rename denial,
hardlink/junction/traversal/ADS/device denial, sentinel preservation, same-size
mutation, quota/cancel/rollback, exact external registration, no-overwrite move,
candidate hash/profile/grid mismatch, grant revocation and cancel-before-commit.
The metadata repository fixture explicitly provides no database transaction.
Real SQLite publish/reconcile/cancel-order tests exist and remain skipped.

## Remaining acceptance

Run SQLAlchemy/Alembic tests and integrated worker→candidate→SQLite publication,
kill processes at rename/commit boundaries, validate GC transaction races and
artifact-aware backup/restore, and complete native cross-session/support-matrix
tests. No real CRS/grid/profile validator, provider/driver policy, model inference
or business coverage is approved by a fixture callback. This is application
boundary enforcement, not an OS sandbox or a power-loss durability guarantee.
