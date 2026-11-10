# Final continuation review — 09/11/2026

Reviewed the selected current working-tree source, not only a HEAD diff:
repository/models/migration/guards, Windows owner/process/I/O, extraction,
grant-to-I/O resolution, GC, publisher, protocol/transport/private bootstrap,
fixture worker and Rust launcher. Plan/progress, SPEC-004, resolver/IPC rules
and preceding task reports/reviews establish the permitted synthetic scope.
No source edits, installation or commit were performed by this reviewer.

## Findings and disposition

1. **P1 — Repository can release writer authority during an operation.**
   Original `storage/repository.py` `_transaction` checked the lease, acquired
   a connection, and only then incremented `_transactions`; `close` was not
   synchronized. Thread A could pause inside `engine.connect`, thread B could
   close and release the lease, then A could execute and commit without writer
   authority. `backup` never registered its raw connection as an operation.
   A controlled regression pauses `connect`/`raw_connection` and calls `close`
   concurrently; close must refuse while the operation remains active.
   **Resolved in source during this review:** `_operation` registers before
   either connection acquisition under the same lifecycle RLock as `close`;
   backup uses that scope and transactions recheck the lease before commit.
   Scoped source rereview approves this fix. Its real SQLAlchemy/SQLite
   regressions remain unrun because the DB dependencies are absent.

2. **P2 — Finished transports retain a permanent writer thread.**
   `jobs/transport.py` `_write_stdin` waits indefinitely in `_outgoing.get`.
   Neither original `shutdown` nor `_fail` supplied its `None` sentinel, so
   each completed worker retained a daemon thread and its transport/process
   object. Live Windows reproduction using `WorkerTransportTests.setUp/launch`:
   `shutdown(.2,3)` returned `True`; after `_writer_thread.join(.2)`,
   `_writer_thread.is_alive()` remained `True`. Termination needs to wake and
   stop the writer on normal and failure paths, without self-join or blocked
   pipe/queue deadlock. **Fix and scoped rereview pending at this checkpoint.**

## Confirmed previous fixes and bounded conclusions

- Task 6 old leases now have an explicit evidence-gated retirement method;
  attempt terminal states are updated; open/restore validate semantic intent,
  current-attempt and publication relationships in addition to SQLite checks.
- Task 7 process handle lifecycle is serialized, attribute-list deletion is
  gated on successful initialization, Rust pointer structs have explicit
  defaults, and native recovery evidence is bound to the exact prior owner
  generation and a live writer. Missing/unknown named Job Object state fails
  closed. These do not establish general automatic crash recovery.
- NativeRoot pins ancestor handles, denies reparse/multiple-link input,
  verifies bytes using the opened handle, and uses exclusive creation and
  handle-based move/delete. NativeReader serializes reads/close. Extraction
  validates the immutable archive before writing and rolls back verified new
  files. No further concrete blocker found in these reviewed paths.
- Publisher snapshots candidate bytes/bindings, checks grant and attempt,
  verifies inputs/profile through a required trusted validator, and holds all
  output readers denying write/delete until repository publication returns.
  Cancel and publish are serialized by the repository transaction; failed
  rename-to-commit sequences leave unregistered orphans. GC checks pins,
  leases and active compute while holding its DB transaction.
- Framing is bounded and strict; transport queues and pending/expired IDs are
  bounded, correlation checks exact IDs, start requires negotiation and private
  bootstrap travels through an explicit inherited handle. Fixture output
  composition is being completed separately and requires the scoped follow-up
  below before the final verdict.

## Reviewer-run checks

`PYTHONPATH=backend;tests/storage; python -m unittest
tests.storage.test_windows_io tests.storage.test_extraction
tests.storage.test_worker_io tests.storage.test_publisher_io
tests.integration.test_native_owner tests.integration.test_native_process -q`
completed with **44 tests, 42 passed, 2 DB skips**, exit 0. The initial package
invocation without `tests/storage` on PYTHONPATH had two fixture-import errors;
the corrected command above is the verification result. No DB behavior was
counted as passing.

SQLAlchemy/Alembic persistence, restore/GC transaction races, Rust compilation,
WebView2 handoff, cross-session ownership, supported-machine installer/runtime,
real GIS/profile/coverage validation and model acceptance remain distinct
acceptance gaps. They are not errors against this permitted source/fixture
delivery and this review does not close SPEC-003/004/009 or G0/G1.

## Scoped final follow-up

Pending transport writer-lifetime fix and the final optional fixture-output
packet/real process-to-publisher composition. Broad review found no additional
concrete source blocker beyond the two findings above; final limited approval
will be recorded after those focused follow-ups.

## Parent disposition after stable source

The implementer added bounded writer termination/join on normal and fatal
shutdown, with regressions for normal, fatal and stalled-child paths. The
optional canonical FixtureOutput now writes fixed synthetic bytes before
candidate/completed, and a real Windows process→staging→Publisher test checks
success and cancel fencing. The reviewer inspected these final source changes
and reported no new blocker before its last verification turn was interrupted
by the tool provider. No final independent test rerun or approval is inferred
from that interruption.

The parent then ran `python Artchitect/docs/evidence/backend-pre-g0-2026-11-08/verify.py`
on stable source: **217 Python tests discovered, 192 passed, 25 DB skips**, all
available suite commands exit 0; 7 DOM tests, typecheck, frontend build and
schema/client checks passed. [Machine-readable result](final-results.json).
This includes the transport lifecycle regressions and process/file publication
test. All reported concrete source findings are addressed; DB/Rust and the
listed acceptance gaps remain unverified. Repository publication now explicitly
flushes its FK parent row before adding artifact rows within the same write
transaction; the reviewer agreed with this source ordering safeguard.
