# Task 8 — Real worker process transport

Read AGENTS.md, SPEC-004/009, ipc-protocol.md, worker-resolver.md and reports/code
from tasks 3–4 and 7. No subagents, installations, commits, public job routes,
GIS/model/provider calls or capability enablement. Preserve other work.

Implement jobs/transport.py and workers/{bootstrap,main}.py using the existing
strict protocol and native managed-process adapter. Give trusted bootstrap and
context bytes only through explicit inherited handles, not paths/secrets in
argv/environment. Validate WorkerBootstrap, immutable registry/context/start,
manifest hashes, launch/project/owner/attempt/budget before accepted. Worker
never imports repository or reads DB. Coordinator supplies the allowlisted
fixture handler registry; do not implement dynamic imports from requests.

One locked binary writer, strict bounded readers, request correlation by both
type and value of ID, monotonic deadlines and bounded diagnostic storage.
Drain stderr independently; never relay raw diagnostic secrets. Protocol stdout
is duplicated before native imports; redirect fd1 and Windows StdHandle to
stderr so print/CRT/native logs cannot corrupt frames. Keep control reader and
heartbeat live while handler runs, one active attempt/slot, cancellation ack
separate from confirmed stop. Shutdown first refuses new work then bounded
graceful/terminate/wait. EOF/oversized/invalid JSON/correlation failures stop the
transport; timeout does not prove start was never accepted. Do not release
compute until process exit is observed. Child cleanup on startup failure and
shell crash uses native containment; no spawn-before-assign fallback.

Fixture technical handler can emit progress/candidate/completed and deliberately
block/log for tests; it does not fake business capability. Candidate IDs are
coordinator issued, events carry only typed contracts. Integrate APIs with pure
coordinator/grant registry as far as trusted composition permits. Missing native
support must fail closed, with portable subprocess tests explicitly identified
as mechanism tests rather than Windows containment acceptance.

TDD and tests/integration/test_worker_transport.py plus worker-access tests:
real subprocess pipes, partial/oversized/nonfinite frames, stdin/stdout close,
stderr beyond pipe capacity, native os.write logging, heartbeat when busy,
cancel while busy, request timeout, late response, stale start/replay and
bounded shutdown. No arbitrary local process termination; only own children.
Record task-8-red.log, task-8-green.log and task-8-report.md with real results,
APIs required for storage/publisher, unsupported/unverified paths. Parent owns
status docs and independent review.
