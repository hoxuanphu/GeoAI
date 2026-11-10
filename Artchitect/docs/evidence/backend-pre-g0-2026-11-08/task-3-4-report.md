# Tasks 3–4: IPC parser and job metadata core

Date: 2026-11-09. Scope: pre-G0 pure Python foundation only. No public route,
native worker, database migration, filesystem publication, or capability enabled.

## Implemented API

`backend/geoai/jobs/protocol.py`:

- `JsonLines(max_bytes=1_048_576).feed(bytes) -> list[dict]`; `finish() -> None`.
  Incremental UTF-8/LF framing; limit includes LF. A malformed/truncated frame
  poisons the reader and raises `ProtocolError`/`TruncatedFrame`.
- `encode(value, max_bytes=1_048_576) -> bytes`; compact UTF-8 object plus LF.
  `RpcFailure(id=None)` retains explicit JSON `id:null`. Encode and decode
  reject nonfinite numbers, escaped surrogates, and JSON nesting over 256.
- `classify(dict) -> RpcRequest | RpcNotification | RpcSuccess | RpcFailure`.
  Checks envelope before method/params; methods and events use existing
  Pydantic 0.1.0 wire types. Unknown/malformed notifications raise protocol
  errors and get no response. Safe request errors use -32600/-32601/-32602;
  capability version mismatch uses -32001 `unsupported_schema`.
- `correlate_response(message, expected_id) -> RpcSuccess | RpcFailure` checks
  exact ID and type. The transport adapter still owns its pending-request map.
  `failure(code, id)` builds sanitized standard/domain error envelopes;
  -32700 parse-error construction is available to the caller after fatal parse.

`backend/geoai/jobs/coordinator.py`:

- `RetryPolicy(max_attempts, backoff_seconds)` is mandatory and bounded.
- `canonical_intent(JobSpec) -> (bytes, sha256_hex)` validates the full spec,
  serializes Pydantic JSON in UTC with sorted keys, compact UTF-8 and finite
  numbers, then hashes `b"job-spec-json-v1\0" + canonical_bytes` with SHA-256.
  The profile constant is `INTENT_DIGEST_PROFILE`.
- `JobCoordinator(retry_policy)` offers `enqueue(spec)`, `get(project_id,
  job_id)`, `claim(project_id, job_id, owner_id=, owner_epoch=,
  elapsed_backoff_seconds=)`, `cancel(project_id, job_id)`, `cancel_ack(...)`,
  `progress(...)`, `candidate(...)`, `fail(..., retryable=)`,
  `confirm_stopped(...)`, `publish(..., publication_id)`, and
  `retain_dependency(...)` / `release_dependency(...)`. Public `JobView` is
  frozen; the JobSpec property reparses immutable intent bytes. Attempt keys
  are fresh coordinator-generated values. Owner epoch is a positive integer,
  matching `WorkerAccessContext`.
- Project-scoped idempotency returns the same job only for identical full
  intent; conflicting keys or reused job IDs cannot overwrite metadata.
  Claim binds project/job/attempt/token/owner/epoch. Cancel blocks publication
  immediately; ACK does not release compute. A trusted `confirm_stopped` call
  releases compute and decides cancelled/failed/queued retry. Retry rotates
  attempt/token and requires explicit elapsed backoff. Stale progress/candidate
  events are ignored; stale publication is rejected. Publication then late
  cancel retains success. Dependency retention is separate from compute.
- `CheckpointIdentity.compatible_with` compares input/model/config/runtime/grid
  identities exactly. It does not prove native checkpoint usability.

## Verification

RED: `task-3-4-red.log` shows protocol edge failures and missing coordinator;
`task-3-4-red-followup.log` shows absent correlation/lease API. Additional
direct RED runs caught deep JSON recursion and encoder/read-depth mismatch.

GREEN commands (PowerShell, `PYTHONPATH=backend`), direct process exit code 0:

| Command | Result |
| --- | --- |
| `python -m unittest discover -s tests/jobs -q` | 17 tests, OK after review fix round 2 |
| `python -m unittest discover -s tests/contracts -q` | 57 tests, OK |
| `python -m unittest discover -s tests/storage -q` | 32 tests, OK |
| `python -m unittest discover -s tests/catalog -q` | 9 tests, OK |
| `python -m unittest discover -s tests/integration -q` | 14 tests, OK |
| `python -m unittest discover -s tests/architecture -q` | 2 tests, OK |

Detailed output: `task-3-4-green.log`, `task-3-4-contracts.log`,
`task-3-4-storage.log`, `task-3-4-catalog.log`, `task-3-4-integration.log`,
`task-3-4-architecture.log`. PowerShell `2>&1 | Tee-Object` wraps the first
stderr line as a `NativeCommandError` record even when unittest ends `OK`;
the direct `-q` runs above supplied clean exit codes and counts.

## Review fix round 1

Independent review found two boundary defects. RED evidence is in
`task-3-4-fix-round1-red.log`: cancelling a retryable failed attempt could
still requeue after stop confirmation, and `encode(max_bytes=2_000_000)` could
override the 1 MiB wire ceiling. The fixes are in the coordinator cancel
transition and protocol encoder bound. GREEN evidence is in
`task-3-4-fix-round1-green.log` (2 tests, OK); the focused jobs suite now has
16 tests, OK. A cancel on an allocated failed attempt enters
`cancel_requested`, clears retry intent, and `confirm_stopped` makes it
`cancelled`; encoder limits are always clamped to `MAX_FRAME_BYTES`.

## Review fix round 2

RED evidence `task-3-4-fix-round2-red.log` reproduced two jobs in the same
project receiving one `publication_id`. The metadata core now tracks
`(project_id, publication_id)` uniqueness; a conflict leaves the second job
running and unmodified. The same publication ID in a different project is
allowed. GREEN evidence `task-3-4-fix-round2-green.log` has 1 test, OK; all
six related suites were rerun with direct exit code 0 (jobs 17, contracts 57,
storage 32, catalog 9, integration 14, architecture 2). The eventual database
adapter needs the matching unique constraint on `(project_id, publication_id)`
alongside one publication per job and transaction-time fencing.

## Integration boundary and remaining work

The core is single-threaded metadata logic. A repository adapter must serialize
transitions with SQLAlchemy/SQLite transaction constraints, persist the digest
profile and unique project/key/job/publication indexes, and recheck token/state
at publication commit. A native owner observer must prove old process groups
have stopped before calling `confirm_stopped`; timeout, heartbeat loss and
cancel ACK are insufficient. The publisher must validate candidate ownership,
file bytes/hash, grid/coverage and immutable manifest before `publish`, then
reconcile file/DB crash windows. `GrantRegistry` validates metadata only.
No OS pipe/stderr drain, process stop, WAL recovery, checkpoint resume, GIS,
model inference or G0/G1 acceptance is established by these tests.
