# Task 3–4 — IPC and coordinator foundation

Continue the existing authorized plan, tasks 3 and 4. Read AGENTS.md, roadmap,
SPEC-004, ipc-protocol.md, contracts.md, contracts/rpc.py and runs.py, current
jobs/protocol.py and storage/resolver.py before coding. No subagents, installs,
Git commits, public job routes or capability enablement. Preserve dirty code.

Finish and test bounded strict JSON-RPC framing/classification in protocol.py.
It exists as unverified work: do not replace without examining it. Cover partial
UTF-8/LF, exact size bounds (LF included), poison/EOF, duplicate keys, nonfinite
numbers including exponent overflow, surrogates, batch, envelope, methods,
versions, params, IDs, success/failure correlation and notifications. Invalid
envelope takes priority over method/params classification; unknown notification
must not elicit a response. Keep fatal corruption separate from safe responses.

Implement jobs/coordinator.py as an explicit pure state machine, never pretend
it is a DB transaction. Immutable canonical full JobSpec intent digest with a
version, project-scoped idempotency conflict, no duplicate ID overwrite, queued
claim with coordinator-created attempt/token, active owner/epoch binding,
cancel request blocking publish, stop confirmation separate from revocation,
terminal states and explicit bounded retry/backoff parameters. A revoked/expired
attempt cannot release compute or authorize another attempt until process stop
is confirmed. Validate full project/job/attempt/token/owner context. Late cancel
after success leaves publication. Old events cannot mutate current attempt.
Checkpoint resume compares snapshot/model/config/runtime identities exactly.
Keep retained dependency leases separate from compute allocation. Public
records are defensive immutable values/bytes; do not add exchange schemas for
internal helpers. Publisher and SQLAlchemy adapter will consume this interface.

TDD: meaningful RED tests first, then implement and run focused suites plus
contracts/storage/catalog/integration/architecture regression. Log exact
commands/actual results to task-3-4-red.log and task-3-4-green.log. Write
task-3-4-report.md with API signatures, semantics, test counts and limitations.
Parent handles task status docs and independent review. Return concise status.
