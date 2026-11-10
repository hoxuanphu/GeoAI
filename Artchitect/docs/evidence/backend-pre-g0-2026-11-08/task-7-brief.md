# Task 7 — Windows owner, process containment and Tauri handoff

Read AGENTS.md, SPEC-003/004, ADR-011, architecture, IPC, worker-resolver and prior native scaffold. User explicitly says skip environment deficiencies and generate code; do not install Rust/MSVC/packages. No subagents or Git. Parent owns status docs. Implement real Windows adapters plus tests; do not call source-only or same-session tests cross-session acceptance. Keep public capabilities false until their actual acceptance runs.

## Native primitives

Use narrow modules under storage (OS handles/owner/project locks) and jobs (process lifecycle), following allowed imports; bootstrap is composition root. Windows ctypes is available and can be tested on this host without Rust. No Unix lock presented as Windows support. Owner is machine-local per current Windows SID across sessions/install paths; canonical namespace/path from trusted OS account/profile data, not client path or app installation. Explicit SID-only ACL for private runtime records/handles. Use a real exclusive OS primitive; store owner ID/epoch/PID+process creation time/session metadata without secrets. Writer lock/project is separate and acquired after owner. Native lifetime guard implements repository guard interface and refuses use after release; no client boolean lock proof.

Abandoned acquisition is recovery, not immediate permission to compute. Persist/check prior process identity and containment state; unknown/alive prior workload keeps recovery_required/resource busy. PID reuse is checked against process creation time. Only confirmed old workload stopped permits new owner/epoch. Hold owner/writer until managed workload exited and writer DB closed. Include explicit release refusal while child/model process still alive. Fail closed where OS cannot prove required state.

Windows Job Object uses kill-on-last-handle-close and no breakaway for sidecar/descendants. Create child with explicit inherited handle allowlist and no window; assign before user code executes. Prefer atomic job assignment at process creation via STARTUPINFOEX job-list on supported Windows, or another proven no-orphan method; a spawn-then-assign race is not acceptable. No insecure fallback on unsupported OS/attribute failures. Reader/writer/bootstrap handles are inherited deliberately; owner/JobObject/DB handles are not accidentally inherited. Explicit environment allowlist, absolute runtime executable; preserve required Windows OS variables, no credentials or arbitrary PYTHONPATH/DLL search from UI.

## Rust shell

Replace `native_launcher_unavailable` scaffold with usable, narrowly configured launcher implementation and lifecycle state. Only main local webview may invoke handoff; one sidecar/session, repeated calls return same active descriptor or safely restart after confirmed stop. Executable path is trusted bundled resource/explicit compile-time dev runtime, never an invoke parameter or general PATH search. Session descriptor validates loopback URL/schema and token stays memory only. Startup reads bounded one-line descriptor with deadline, drains bounded stderr without exposing raw data/token, verifies health through existing UI. Any startup parse/timeout/exit failure closes/kills/waits group before retry. Window/app close: graceful pipe shutdown then bounded group termination/wait. Shell death must close root Job Object so descendants die. Code may use Rust Windows API crate or raw FFI with checked handle RAII; no fabricated Cargo.lock. Sidecar native mode uses production Origin policy; keep existing explicit dev flags/tests valid.

If some native guarantees require new kernel APIs unsupported here, implement explicit supported-path checks plus refusal; no placeholder success or empty TODO. Keep metadata-only API routes/capabilities until writer/job integration separately verified. Do not bundle interpreter/models/weights or fetch binaries.

## Tests and reporting

TDD for Windows owner/process primitives in integration tests using temporary private test namespaces, two processes/projects, normal release, contender denial, crash with live descendants, PID identity mismatch, release while child alive, startup failure cleanup, inherited handle sentinel and Unicode paths. Exercise actual ctypes Windows calls when available. Avoid acquiring production owner or terminating unrelated processes; tests only own their children. New-instance recovery must not kill a PID based only on durable text.

Run actual available Python tests and syntax checks, frontend typecheck/build if interface changes, and attempt cargo test/build only if executable exists (no install). Rust unbuilt/cross-session/WebView2 checks explicitly remain pending. Write `task-7-report.md` with exact interfaces for worker transport/storage adapters, commands/counts, verified primitives and all unverified claims. Independent review follows.

## Continuation integration ruling

Read task-7-preflight.md for the concrete OS APIs and WriterGuard/GuardLease
contract. Task6 owns storage/guards.py (protocol only), storage/db_models.py,
repository.py, intents.py, migrations, pyproject and DB tests. Task7 owns new
storage/windows_owner.py and jobs/native_process.py, bootstrap native mode,
Rust src-tauri code/Cargo.toml and native integration tests. Do not edit Task6
files; use the stated guard interface structurally, request coordination if a
change is needed. owner_epoch must be a positive integer. Parent allows these
two disjoint adapters to progress concurrently after the guard interface is
fixed; no overlapping edits or installations. Task8 consumes ManagedProcess
and pipes; document their precise methods/ownership in report.
