# Task 3 — SPEC-003 shell/API foundation

Date: 2026-11-08. Result: independently testable pre-G0 API/UI foundation implemented and verified on this Windows development machine. **SPEC-003 remains partial. Native Tauri launcher, execution ownership, Windows Job Object containment and cross-session acceptance are unverified and blocked by missing native toolchains. G0/G1 are not closed.**

## Implemented boundary

- `backend/geoai/api/session.py`: per-launch `secrets.token_urlsafe(32)` token; constant-time byte comparison; exact `127.0.0.1:<session-port>` Host; explicit production/dev Origin allowlists; optional missing-Origin policy still requires Host/token; case-insensitive header handling; duplicate authorization/Host/Origin/preflight headers rejected. Errors never reflect raw headers/token. Query strings do not grant access and are rejected even with a valid header token.
- `backend/geoai/api/app.py`: authenticated GET `/v1/health` and `/v1/capabilities`; no docs/openapi URL served, path/URL proxy, shutdown, writer, job or inference route. Capabilities describe only metadata foundation: technical readiness true, inference/native launcher/execution owner/project writer readiness all false.
- CORS valid preflight returns 204 metadata only, restricted to the two GET routes, configured Origin, exact Host and authorization header; an actual GET still needs its session token. Invalid Origin/Host/method/header/path/query preflight cannot obtain success or CORS permission.
- `backend/geoai/bootstrap.py`: explicit development-only `--dev-stdio-handoff --no-console` mode; both stdin/stdout must be pipe handles, not console/files. Bind `127.0.0.1:0` once, retain socket and give it directly to Uvicorn without probe/rebind. Emit one canonical descriptor through the private stdout pipe after the server starts. Trusted stdin control/EOF requests graceful stop. No token in CLI/env/URL. Uvicorn access logging is disabled; diagnostic sink strips request targets, headers, arguments and exception text. No production owner or project writer is acquired.
- `backend/geoai/contracts/api.py`, public exports/registries, fixtures/schema: Pydantic health/capability response DTOs in wire registry; `SessionDescriptor` only in private runtime registry, never durable project registry. Descriptor validates exact loopback URL/port and token syntax, excludes token from repr. Bootstrap serializes that DTO.
- `tools/export_api_client.py`: deterministic OpenAPI and TypeScript generation/check from Pydantic route schemas and private descriptor DTO, fail closed for unsupported schema shapes. Generated `schemas/openapi-v0.1.0.json`, `apps/desktop/src/generated/api.ts`; existing contracts exporter regenerates `schemas/contracts-v0.1.0.json`. No duplicate handwritten frontend response/handoff interface. JS runtime guard checks descriptor before credentials are sent; requests use header, `credentials: omit`, `redirect: error`, no cache.
- `apps/desktop`: React/TypeScript/Vite workspace, Vietnamese bootstrap/error/retry/status UI, project note state held in App outside panels; handoff uses Tauri invoke, token kept in memory only. Browser mode reports missing desktop connection. A 10-second technical UI connection deadline aborts fetch and ignores late/stale handoff/completion; retry creates a new connection attempt. This deadline is not a G0/business performance SLO.
- `apps/desktop/src-tauri`: minimal Tauri v2 configuration/Rust scaffold; custom command returns sanitized `native_launcher_unavailable` and starts no processes. CSP restricts API connections to loopback `/v1/`, IPC and necessary dev HMR; capability scoped to main webview with no shell/filesystem plugin permissions. No fabricated Cargo.lock.
- Optional `api` and `test` Python dependencies in `pyproject.toml`; frontend scripts `test`, `typecheck`, `build`, `api:generate`, `api:check`; local setup/limitations in `apps/desktop/README.md`. Root roadmap/spec/tracker/docs are maintained by parent task.

## Environment and dependency resolution

Verified Python 3.12.4, Windows 11 build 26200, FastAPI 0.141.1, Uvicorn 0.49.0, httpx 0.28.1, Pydantic 2.13.2. Used existing global Python packages with `PYTHONPATH=backend`; no global package installation or TLS bypass. Fresh Python wheels were already known blocked HTTP403 in parent baseline.

Node 24.19.0/npm 11.17.0; actual npm resolve produced `apps/desktop/package-lock.json`. Final frontend: React 19.3.1, Tauri API/CLI JS package 2.12.4, TypeScript 5.9.3, Vite 7.3.7, Vitest 4.1.12. Package overrides map Rollup to official `@rollup/wasm-node@4.53.0` and esbuild to `esbuild-wasm@0.25.12`. The aliases are configured in package.json/lock, not manual node_modules patches.

Reproduction actually executed after resolution: `NODE_USE_SYSTEM_CA=1 npm ci` from `apps/desktop`, exit 0; added 91 packages, audited 92 packages in 5 seconds, zero vulnerabilities. Subsequent tests/typecheck/build passed against that install. Windows system trust was enabled, certificate checking stayed enabled. `npm audit --json` final result zero vulnerabilities is in [audit log](task-3-npm-audit.log).

## TDD and failed attempts

1. Preserved original eight parent session-test expectations and reproduced eight RED failures because SessionPolicy/API did not exist (parent [session RED log](task-3-session-red.log)). Replaced deprecated Starlette/httpx TestClient harness with real `httpx.ASGITransport`/AsyncClient, without suppressing deprecation warnings. Eight original tests then passed; duplicate-header/CORS/redaction cases brought session tests to eleven.
2. Real Python process tests first failed because bootstrap/handoff did not exist. Implemented private dev-pipe startup/health/graceful stop, per-launch token freshness and EOF stop; three process tests passed. These do not stand in for native owner/Job Object tests.
3. Frontend tests were written before App. Initial execution was blocked at tooling startup: native Rolldown binding absent; direct native package downloads for Rolldown and Tauri CLI returned HTTP403 `MediaTypeBlocked`. Rolldown WASI fallback installed with explicit wasm CPU selection but could not resolve Windows absolute entry/import paths. This fallback was removed. No machine compiler/toolchain was installed.
4. Switched to official WASM Rollup/esbuild via npm overrides; Vite6/Vitest3 then reached the intended missing-App RED failure and the five initial DOM tests passed after App implementation. Audit exposed old Vitest/tinypool advisories, so updated final stack to Vite7/Vitest4.1.12. Final audit zero; no forced audit fix or policy bypass.
5. Review requested canonical Pydantic descriptor instead of handwritten generated-interface template. Missing-descriptor test observed RED, then strict private DTO, serialization and generated type passed. Review also found a hung handoff/network would leave UI loading indefinitely. Two targeted timeout regressions observed RED in [timeout RED log](task-3-timeout-red.log); bounded timeout/abort/stale-attempt guards made all seven DOM tests pass. Late-handoff regression uses a valid distinct old loopback descriptor and proves no old network request is sent after successful retry.

## Final verification

All commands below exited 0. Python commands run from workspace root with `PYTHONPATH=backend`; npm commands run from `apps/desktop`.

| Command | Result | Evidence |
| --- | --- | --- |
| `python -m unittest discover -s tests/contracts -v` | 55 tests pass, including four API/private-handoff tests | [contracts log](task-3-contracts.log) |
| `python -m unittest discover -s tests/integration -v` | 14 tests pass: 11 session + 3 real Python dev-process tests | [integration log](task-3-integration.log) |
| `python -m unittest discover -s tests/architecture -v` | 2 parent-provided import boundary checks pass | [architecture log](task-3-architecture.log) |
| `python tools/export_contract_schemas.py --check` | Generated schema current | [schema log](task-3-schema.log) |
| `python tools/export_api_client.py --check` | OpenAPI/client current | [API artifact log](task-3-api-artifacts.log) |
| `npm test` | 7 DOM tests pass | [frontend test log](task-3-npm-tests.log) |
| `npm run typecheck` | TypeScript passes | [typecheck log](task-3-typecheck.log) |
| `npm run build` | Vite production assets built | [build log](task-3-frontend-build.log) |
| `npm audit --json` with system CA | 0 vulnerabilities | [audit log](task-3-npm-audit.log) |
| Python `jsonschema.validate(tauri.conf.json, installed-cli/config.schema.json)` | Configuration conforms to Tauri CLI 2.12.4 JSON Schema | [config-only log](task-3-tauri-config.log) |

DOM tests exercise App plus the generated client and real React DOM; controlled doubles exist only at native handoff/fetch boundaries. They verify valid header-authenticated connection, error sanitization, retry, state retention across panel changes, browser handoff absence, malicious descriptor rejection before fetch, hung handoff/fetch timeout, abort and stale completion. Real server process tests verify selected loopback port, private descriptor, health/capabilities, stale token rejection, token-query denial, no secret/query in logs, graceful stdin stop, pipe EOF, port no longer serving and fresh token per launch.

## Open acceptance and native blocker

Rust/Cargo/MSVC are absent; native package downloads also blocked. No Tauri compile, native binary launch, WebView2/CSP/production-Origin runtime check, graphical browser run or installer test was performed. Tauri schema validation and frontend Vite build are not evidence for those acceptance items. External Windows console-signal delivery has not been verified in this noninteractive harness; Uvicorn signal handling is retained, while actual trusted-pipe cancellation and EOF graceful exit are verified.

Before SPEC-003 completion, implement and compile the real launcher: execution-owner primitive across sessions/same account and installs with ACL/namespace/epoch/PID creation identity; receive ownership before writer/migration/worker; inherited anonymous handle handoff; Job Object process containment; graceful deadline and shell-crash cleanup; abandoned owner recovery that confirms native workers stopped before any new owner/job. Test cross-session, PID reuse, two projects/installations, normal/crash close, model residency/resource recovery on real Windows. No such tests have been replaced by fake passes. Owner lock remains separate from attempt fencing.

The scaffold deliberately cannot start processes or claim execution ownership. No importer/resolver, coordinator, database, worker, GIS/viewer/model/solver runtime or business readiness was added. SPEC-009/004 must not infer native launcher readiness from this foundation. No Git init/commit was performed and unrelated workspace changes/data were preserved.
