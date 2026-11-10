# SDD ledger — plan: Artchitect/docs/evidence/backend-pre-g0-2026-11-08/plan.md

- Task 1: complete — policy/archive inventory và endpoint/stream logic thuần; scoped review đã duyệt hai fix P2, 19 storage + 2 probe tests pass. [Review](task-1-review.md); không đóng native/transport acceptance.
- Task 2: complete — metadata grant/reference/candidate registry, 13 focused tests and independent review approved; 57 contracts +32 storage +9 catalog +14 integration +2 architecture pass. [Report](task-2-report.md), [review](task-2-review.md). Native handles/OS owner/I/O remain pending.
- Task 2: pending — context/grant/reference/candidate scope thuần.
- Task 3: pending — IPC framing và classification.
- Task 4: pending — job state/idempotency/fencing/checkpoint rules thuần.
- Task 5: pending — review/verification/docs/handoff.

Ruling: tiếp tục trong workspace không Git, baseline source/hash và suite trước sửa được lưu cùng folder. Không lặp lại foundation đã hoàn tất ở codegen-2026-11-08. Chỉ owner/native/DB/live/model acceptance thực sự thiếu dependency mới ghi chờ; logic thuần đủ spec sẽ được triển khai.

Task1 review round1 (09/11/2026): reviewer kiểm lại 57 contracts/15 storage/9 catalog/2 architecture và artifacts pass, nhưng probe tìm reserved-device aliases và ZIP envelope (prefix/concat/trailing/EOCD metadata) còn lọt. Đã giao implementer viết regression RED và sửa; chưa ghi Task1 hoàn tất. [Report triển khai](task-1-report.md); native/transport/extraction không thuộc kết luận unit tests.

Ruling (yêu cầu mới 09/11/2026): không tiếp tục sửa/cài môi trường. Mở rộng plan với SQLAlchemy/Alembic, native lifecycle, worker transport và storage I/O; viết code/test dù chưa chạy được dependency-specific checks. G0/đầu vào model/nghiệp vụ vẫn ràng buộc; không suy nghiệm thu từ code đã sinh. Agent cũ không còn live sau handoff; scoped reviewer mới chỉ kiểm hai fix Task1, không tái triển khai task đã xong.

## Continuation 09/11/2026

Ruling: repository now exists (HEAD 6566d94), contrary to the old no-Git note. Continue on branch `codex/pre-g0-continuation-2026-11-09`, preserving all dirty/untracked work in place; a fresh worktree would omit unfinished resolver/protocol code. No automatic commits or environment installation.

Ruling: duplicate Task 2 pending entry above is stale; its completion/report/review take precedence. Task 3 framing source exists but has no acceptance evidence yet. Execute Task 3–4 together, then repository, native, transport and storage adapters, with independent review. Native/DB code may be written despite missing dependencies; checks remain distinct from source delivery.

Preflight: Task 3 consumes contracts and feeds Task 8; Task 4 consumes JobSpec/AttemptKey and feeds Task 6/9. Repository depends on native lifetime guard, so define an internal guard protocol before native composition. Storage may consume contracts only, never jobs. Task 7/8 share process handles: Task 7 provides containment and launch, Task 8 provides framed transport. Task 9 publishes through a jobs composition service and a storage-only I/O adapter. No capability enabled from source generation.

- Task 3–4: in_progress.
- Task 6–9: pending.
- Task 5/10: pending final verification and documentation.

Parent review during Task 3–4: require positive integer owner_epoch matching WorkerAccessContext; preserve nullable id on JSON-RPC failure encoding; malformed notifications never generate responses; parse recursion errors must be sanitized. Implementer acknowledged and is adding RED regressions. Final approval waits for green evidence and independent review.

Native preflight identified thread-affine named-mutex ownership, spawn-before-assignment orphan race and insufficient root-PID/group-handle stop proofs. Task 7 must implement lifetime guards and atomic job/handle attribute lists, refusing unknown recovery state rather than claiming compute released.

Ruling: adopt internal WriterGuard/GuardLease interface from [native preflight](task-7-preflight.md). owner_epoch is a positive integer; repository retains the guard across connections and rechecks it per transaction. Fixture guards do not establish OS ownership. Lock release refuses live leases/workloads. Cross-session/native support remains unaccepted until actual tests.

Task 3–4 review round1 fixed P1 cancel-after-failure/retry and P2 encoder hard bound; parent 16 focused tests pass, reviewer approved scoped fixes. A separate P2 duplicate publication ID within project is being fixed in round2. Full available backend regression at this point: 57 contracts, 32 storage, 9 catalog, 14 integration, 2 architecture, 16 jobs pass (130 total). Repository Task6 now in_progress; SQLAlchemy/Alembic absent, no installation attempted.

Evidence hygiene: task-2-report.md was existing Windows-1252 text (byte 0x97 in title); normalized its encoding to UTF-8 preserving decoded content. Documentation target existence and protected-file hashes check now succeeds; this does not render Mermaid or check GIS/model semantics.

Ruling: Task6 repository and Task7 native adapter now have a fixed guard interface and disjoint file ownership. Apply dispatching-parallel-agents for these independent adapters to continue implementation concurrently; do not overlap mutations. Task6 owns storage/guards.py/intents/repository/db_models/migrations/pyproject. Task7 owns windows_owner/native_process/bootstrap/Rust/native tests. Any interface change is coordinated explicitly; subsequent transport/storage integration remains sequential.

- Task 3: complete — pure framing/classification/correlation. Task 4: complete — pure coordinator metadata only. Independent review final approved all three findings; jobs17 plus baseline suites pass (131 backend tests total). [Report](task-3-4-report.md), [review](task-3-4-review.md). No durable/process/native/GIS acceptance claimed.
- Task 6: in_progress — repository agent.
- Task 7: in_progress — native adapter agent; guard file ownership coordinated.

- Task 6: source delivered; first review found three P2 issues (old lease recovery, attempt terminal state, restore semantic integrity), implementer reports fixes with regressions; DB tests still skipped. Scoped re-review pending.
- Task 7: source delivered, Windows17 native tests pass; independent review found Rust raw-pointer Default and Python lifecycle synchronization/attribute-list cleanup issues. Fix round1 in progress. Rust build/WebView2/cross-session remain unverified.
- Task 8: in_progress — real process transport, trusted private bootstrap and fixture worker.
- Task 9: source delivered for review — NativeRoot7, extraction4, grant+I/O3 and publisher6 Windows/mechanism tests pass; 2 real SQLite publisher tests skipped. Added transactional GC callback with explicit policy and registered disposable root; DB race tests remain unrun. [Report](task-9-report.md).

Final review finding: repository connection/backup acquisition could race close and release retained writer guard. Parent added lifecycle RLock + operation registration before connection, close refusal and precommit held check; concurrency tests require DB extra and remain skipped. Task8 writer-thread lifecycle leak reported to implementer. Native7 fix round complete, final25 native/devshell tests pass; unknown missing Job Object now blocks recovery. Exact prior-owner stop evidence supplied structurally to repository, current/wrong/closed guards refused.
