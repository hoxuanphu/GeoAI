# Final independent review - codegen foundation

Date: 2026-11-08. Verdict: **bounded approval of draft contracts plus the independently testable API/UI foundation; no blocking code or security defect found.** The UI recovery finding below was fixed and independently rechecked before handoff. SPEC-003 remains partial, and neither G0 nor G1 is closed.

## Scope and evidence

Read the final-review/task-3 briefs, baseline inventory, roadmap/spec index, SPEC-003, architecture/ADR index/ADR-011, IPC and contracts documentation, task-2 independent contracts review, and desktop README. Inspected API/session/bootstrap, API/private DTO and registry additions, generated OpenAPI/TypeScript and generator, React handoff/state/tests, Tauri Rust/config/capabilities, package/build configuration, and static architecture tests. Existing SPEC-001 semantic coverage was re-run; the prior independent review remains the detailed assessment of unchanged run/RPC/context semantics. No production edits, subagents, Git operations, browser checks, or native compilation were performed by this reviewer.

The [task-3 implementation report](task-3-report.md) was read after publication. Its final verification counts, implementation boundary and native/toolchain limitations agree with the reviewed code and independently observed checks. It additionally records a successful npm-ci reproduction/audit and Tauri JSON Schema validation; those are implementer evidence, not independent reviewer install/native execution. Parent owns final roadmap/spec/tracker/source-doc synchronization; stale status text observed during concurrent edits is a handoff action, not a code defect.

## Finding resolved in scoped follow-up

**FR-01, nonblocking for this fail-closed scaffold:** `apps/desktop/src/App.tsx:14` connection effect awaits handoff and both metadata requests without a deadline (`:20`, `:23` at initial inspection). The abort only runs on effect cleanup, and Retry appears only in the error branch (`:37`). Therefore a promise that stays pending leaves the screen loading with no recovery action; a late handoff can also enter the fetch block after cleanup. This follows directly from control flow; the initial five DOM tests cover rejection and successful retry, not a hung operation. Add a technical connection deadline, abort active fetches, ignore late handoff/results, and test timeout/retry isolation. Parent has assigned this bounded follow-up to the implementer. No native execution is enabled by this issue.

**Resolved:** the final effect has a 10-second technical UI deadline, marks timed-out work inactive, aborts fetches, checks activity immediately after handoff, and clears the timer on completion/cleanup. The new tests cover hung handoff and hung network recovery. The stale-handoff test resolves a valid but distinct old loopback session after retry succeeds and proves the fetch count stays exactly two, so the old token does not initiate another request. Product copy was simplified without implying available GIS/AI/project persistence. Independent scoped recheck at 23:26 local time: **7 DOM tests passed**, typecheck passed, Vite production build passed (33 modules). The earlier 5-test run below records the pre-fix baseline. The 10-second timeout is an internal connection-recovery value, not an approved G0/business SLO.

## Independently observed verification

Executed in the current Windows checkout using existing global Python and `PYTHONPATH=backend`:

- `python -m unittest discover -s tests/contracts -v`: **55 tests passed**, 2.398 seconds.
- `python -m unittest discover -s tests/integration -v`: **14 tests passed**, 6.791 seconds. Includes real Python subprocess/socket handoff, authenticated health/capabilities, stale-token rejection, shutdown, EOF stop, token rotation, and no subsequent token-bearing output. These are development-sidecar tests, not Tauri/Job Object or cross-session owner acceptance.
- `python -m unittest discover -s tests/architecture -v`: **2 tests passed**, 0.028 seconds. Static imports follow the documented dependency map; contracts import only standard-library/Pydantic/internal contracts. This is static coverage, not a sandbox or future dynamic-import guarantee.
- `python tools/export_contract_schemas.py --check`: **Contract schema is current**.
- `python tools/export_api_client.py --check`: **API artifacts are current**.
- From `apps/desktop`, `npm test`: **5 DOM tests passed**; `npm run typecheck`: passed; `npm run build`: passed, Vite 7.3.7, 33 modules. These checks use the resolved lockfile and official WASM overrides already installed by the implementer. Reviewer did not perform a new dependency installation.

## Boundary assessment

- Session middleware enforces exact `127.0.0.1:<session port>` Host, configured explicit Origin, constant-time bearer-token comparison, duplicate sensitive-header rejection, and explicit missing-Origin policy. Valid CORS preflight grants no GET authorization. Query strings are rejected. The API exposes only the two metadata routes; interactive docs/OpenAPI HTTP endpoints are disabled.
- Bootstrap binds one socket to loopback port zero and passes that socket into Uvicorn, avoiding probe/rebind. Development mode requires both explicit flags and piped streams. Descriptor output is confined to the private development handoff; access logs are disabled and the configured diagnostic sink removes raw messages/exception text. Runtime tests observed clean stop on control input and pipe EOF, and fresh tokens between launches. This does not prove anonymous-handle provenance, forced native descendant termination, or native crash containment.
- SessionDescriptor is a canonical private Pydantic DTO, excluded from durable contracts and marked private in generated OpenAPI. Response types are generated from the route schemas. Frontend transport validates loopback destination before sending the in-memory token, uses Authorization headers, omits credentials, rejects redirects, and disables cache; errors are generic. Project note state lives above panel switches. No storage/console/token-URL flow was found.
- Capability DTOs forbid promoting native launcher, execution owner, project writer, or inference readiness. The Rust command explicitly returns `native_launcher_unavailable`, with no spawn/owner/writer logic. Static CSP permits only necessary IPC/loopback paths; the main capability does not grant shell/filesystem/network plugins. Actual Tauri compilation, CSP enforcement and WebView2 Origin behavior remain unverified.
- No production GIS/AI/solver, importer/resolver, worker transport, DB/publisher or business workflow is supplied by this change. Type checks and synthetic fixtures are not evidence of runtime fencing, real hashes/paths, business accuracy, CRS, or installer behavior.

## Required honest handoff

Keep SPEC-003 partial with native launcher, execution-owner lock/recovery, Job Objects, real Windows cross-session/process scenarios, WebView2 CSP/Origin and native compile/run pending. Rust/Cargo/MSVC and the cross-session harness are unavailable; the native CLI download restriction and fresh Python install HTTP 403 are explicit in the implementation report. External Windows console-signal delivery is also explicitly unverified; stdin control and EOF graceful exit were tested. No Cargo.lock or clean Python/native install claim was manufactured. Parent must synchronize final evidence/counts and statuses after the scoped UI follow-up. No outstanding code finding remains in this bounded review.
