# Review contract for independent pre-G0 backend tasks

Read the numbered task brief/report plus plan.md, relevant SPEC-009/004, security/IPC/architecture contracts, and implementation-gaps.md. Workspace has no Git; baseline-inventory.json records original hashes. Parent owns status docs and final evidence. No subagents, no production edits, no global installs. Review only the assigned task now; final whole-change review will be separate.

Verify spec compliance, correctness and meaningful tests using real byte/record fixtures. Seek actionable bugs or unsafe enabling, not speculative future design. Report severity/file/line and reproducing input when possible. Distinguish pure metadata/policy/framing/state semantics from native/OS/transport/DB/ML acceptance. In particular no actual file confinement, rebinding-safe network, SQLite fencing or owner lifecycle can be claimed from pure tests. Missing later integration isn't a defect in the explicitly bounded task; falsely documenting it as complete is.

Task 1 risks: ZIP bombs/forged sizes/CRC/trailing/overlaps, bounded decompression, Windows path aliases, unsupported links/encryption/archive types, explicit finite policy, clean no-write behavior, credential leaks in errors, URL origins/IP/private policy and stream budgets vs blocking I/O. New exchanged types canonical Pydantic; registry/schema/fixtures coherent.

Task 2 risks: byte identity/snapshot mutation, trust source of expected bindings, worker/project/nonce/owner/epoch/attempt/token/start/job/snapshot/grid/budget match, missing dependencies, one-use/revocation, stale/cross-scope candidates, actual handles explicitly pending. Registry state must not be caller mutable.

Task 3 risks: exact inclusive LF size bound, poison state, EOF, large chunks/multiframe memory, UTF8/nonfinite/duplicate keys/surrogates/batch; classify parse/envelope/method/params and correlate valid IDs; notification no-response and sanitized errors; parser isn't native pipe validation.

Task 4 risks: immutable intent/canonical idempotency, duplicate IDs/projects, coordinator-issued attempts/token, deterministic cancel/publish and stale events, unknown stopped state/retry budget, checkpoint fields exact matching, defensive views; in-memory state must never be described as durable DB fencing/OS stop proof.

Use global Python with PYTHONPATH=backend. Existing packages Pydantic/FastAPI/httpx available; SQLAlchemy/Alembic not installed and wheel fetch rechecked403. Relevant unittest suites/checks should run; don't broaden into real data/native calls. Write task-N-review.md in this directory, return bounded approval or concise findings. Parent dispatches fixes to implementer and scoped re-review.
