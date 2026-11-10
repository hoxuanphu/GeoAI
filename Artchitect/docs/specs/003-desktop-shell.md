# SPEC-003 — Desktop shell và vòng đời sidecar

**Trạng thái:** thực hiện một phần — API/session/UI và Python Windows owner/Job Object đã có kiểm fixture; Rust/Tauri launcher đã có source nhưng chưa build, còn WebView2/cross-session acceptance. **Mục tiêu đầy đủ:** Tauri/React khởi động Python API, UI nhận health/capabilities qua phiên local và dừng sạch. Có thể làm skeleton trước G0; không tự chốt hardware/model nghiệp vụ. [Tiến độ backend](../evidence/backend-pre-g0-2026-11-08/progress.md).

## Yêu cầu Linux ghi nhận ngày 10/11/2026

Ngoài Windows, mục tiêu hỗ trợ cần triển khai/kiểm chứng gồm **Ubuntu 22.04 LTS và Ubuntu 24.04 LTS** theo yêu cầu người dùng. [Hồ sơ yêu cầu và đánh giá Cloud](../evidence/2026-11-10-linux-support-assessment.md) ghi nguồn, phụ thuộc Windows hiện có, hướng build trên 22.04 và ma trận kiểm hai LTS. Chưa có runtime/bộ cài Linux hoặc test Cloud đã chạy. Các acceptance Windows bên dưới giữ nguyên phạm vi; phải bổ sung ADR/thiết kế Linux và acceptance tương ứng trước triển khai, không chỉ đổi tên Job Object/WebView2 thành primitive Linux. Python >=3.12, WebKitGTK, process containment/owner, native I/O, Host/Origin và packaging cần kiểm riêng. Chỉ được chuẩn bị phần độc lập trước G0; ghi pass/skip/fail và giới hạn môi trường khi kiểm thực tế.

## Kiểm môi trường 09/11/2026

[Bằng chứng](../evidence/environment-2026-11-09/results.json): npm trust store đã sửa bằng user `NODE_USE_SYSTEM_CA=1`; restore, 7 DOM tests, typecheck/frontend build pass. CLI Tauri vẫn thiếu binding: GET package 2.12.4 trả 403 `MediaTypeBlocked`; Rustup download 403. Build Tools installer có hash hợp lệ nhưng hai lần dừng 1602, bootstrap log nhắc UAC/elevation. WebView2 đã được phát hiện ở lượt chẩn đoán trước, chưa chạy acceptance thực. Python sạch chưa cài đủ dependency do wheel 403; 57 contracts tests chỉ kiểm bằng package có sẵn. Cần xử lý phê duyệt mạng và cài Build Tools với elevation trước native compile. SPEC này vẫn partial, chưa có native acceptance.

## Input/output và interface

Source tiếp nối ngày 09/11/2026 ở [Task 7](../evidence/backend-pre-g0-2026-11-08/task-7-report.md): exclusive account owner/project writer, retained guard, atomic Job Object/handle-list launcher, native bootstrap mode và Rust handoff/lifecycle. [Review](../evidence/backend-pre-g0-2026-11-08/task-7-review.md) phát hiện các lỗi cần sửa; trạng thái fix/kiểm cuối theo progress, không suy Rust pass từ ctypes. API capability native/owner/writer/inference tiếp tục false; các mốc 003.1–003.3 chưa hoàn tất toàn bộ.

Đọc [architecture](../architecture.md), ADR-001/003/006, [IPC](../ipc-protocol.md). Output dự kiến: `apps/desktop/` với package/pnpm/Cargo/Tauri config, `backend/geoai/bootstrap.py`, `api/app.py`, `api/session.py`, scripts dev/build và hướng dẫn README. Khóa dependency sau resolve thật; không viết lockfile giả.

SPEC-001 phải hoàn tất phần contracts dùng bởi routes trước triển khai. Phạm vi UI ban đầu là workspace có trạng thái bootstrap/health/error, không tự khai có viewer/model nghiệp vụ chạy được. Kiểm viewer/GIS/PDF/bundle đầy đủ thuộc [SPEC-007](007-g1-platform-validation.md); skeleton shell pass chưa đủ đóng G1.

Routes tối thiểu: GET `/v1/health` trả `{status:"ok", app_version, schema_version}`; GET `/v1/capabilities` trả runtime/feature thực và readiness. Không khai inference ready khi mới có contracts. Shell cấp cổng loopback/token qua IPC có quyền, không qua URL; UI dùng header token cho fetch/SSE adapter. API kiểm Host/Origin/token theo build và WebView2 thực.

## Acceptance

- Clone/setup theo README chạy UI/API trên Windows dev, không dựa PATH/native cache vô tình.
- Request hợp lệ có token hoạt động; sai Host/Origin/token hoặc token phiên cũ bị từ chối. Thiếu Origin chỉ đi policy đã định, vẫn token/Host.
- Đóng app khi idle thu hồi sidecar; shell crash không để worker/sidecar mồ côi. Graceful stop có deadline, Job Object không tự checkpoint.
- Unicode path/log không hỏng; secret/header token không vào URL/log. Chưa thêm pipeline/model/solver hoặc editor tổng quát.
- Theo [ADR-011](../adr/ADR-011-local-execution-owner.md), shell/coordinator phải nhận execution owner lock liên process/cùng tài khoản xuyên session trước project writer/migration/worker. Instance thứ hai cùng hoặc khác project chỉ đọc hoặc báo bận; không nạp model resident hay mở queue ghi riêng. Không hỗ trợ nhiều tài khoản cùng compute bằng cách bỏ qua khóa.

## Test phải có trong task

`tests/integration/test_local_session.py`: correct session, missing/bad/stale token, wrong Host/Origin, header redaction. `tests/integration/test_shell_lifecycle.py`: startup/normal exit/shell crash bằng process thật trên Windows. Frontend test: bootstrap handoff, health/error state, đóng/mở panel không mất project state.

`tests/integration/test_execution_owner.py`: hai instance/project cùng khởi động, hai bản cài và cùng tài khoản ở session khác; một owner duy nhất; ACL/namespace khóa; PID tái sử dụng; abandoned owner nhưng native worker vẫn sống phải recovery/chặn thay vì cấp job mới. Chuyển project giữ/nhả quyền đúng, đóng app giải phóng worker/model trước nhả owner. Ca xuyên session cần môi trường Windows thật; chưa chạy/không đủ môi trường phải ghi chưa kiểm, không báo G1 pass.

Lệnh test/lint/typecheck/build cụ thể phải được khai báo trong package/README khi dựng stack và ghi output vào spec này lúc bàn giao; không báo build pass trước khi đã chạy. Task này chỉ chứng minh shell/API foundation, chưa là installer/model G1 hoàn chỉnh.

## Bàn giao phần nền ngày 08/11/2026

Đã có `api/{app,session}.py`, `bootstrap.py` chế độ pipe dev; Pydantic `HealthResponse`/`CapabilitiesResponse` public wire và `SessionDescriptor` private IPC, OpenAPI/client sinh bằng `tools/export_api_client.py`. API chỉ metadata, toàn bộ capability native/owner/writer/inference đều false. Không route project writer/job, không tự nhận quyền khi owner chưa có.

`apps/desktop` có React/Vite/TypeScript, state ngoài panel, session header và xử lý lỗi/thử lại; package lock từ resolve thực. Rollup/esbuild dùng WASM chính thức qua npm overrides vì native binary bị policy HTTP403. Tauri config/scaffold có command chỉ trả `native_launcher_unavailable`; không spawn sidecar hoặc trả token giả. Không có Cargo.lock tạo tay.

| Phép kiểm đã chạy | Kết quả / bằng chứng |
| --- | --- |
| `python -m unittest discover -s tests/contracts -v` với `PYTHONPATH=backend` | 55 tests pass sau bổ sung DTO/handoff; [log](../evidence/codegen-2026-11-08/task-3-contracts.log) |
| `python -m unittest discover -s tests/integration -v` | 14 tests pass: Host/Origin/token/CORS/header/redaction và process metadata API qua private pipe; [log](../evidence/codegen-2026-11-08/task-3-integration.log) |
| `python -m unittest discover -s tests/architecture -v` | 2 tests pass về static imports/contracts dependency; [log](../evidence/codegen-2026-11-08/task-3-architecture.log) |
| Hai exporter `--check` | Contracts schema và OpenAPI/client current; [schema](../evidence/codegen-2026-11-08/task-3-schema.log), [API](../evidence/codegen-2026-11-08/task-3-api-artifacts.log) |
| `npm ci`, `npm test`, `npm run typecheck`, `npm run build` trong apps/desktop | Lock được kiểm lại; DOM/typecheck/Vite build pass; [DOM](../evidence/codegen-2026-11-08/task-3-npm-tests.log), [typecheck](../evidence/codegen-2026-11-08/task-3-typecheck.log), [build](../evidence/codegen-2026-11-08/task-3-frontend-build.log) |

Lệnh thiết lập/kiểm và policy Origin/CORS/dev pipe ở [README shell](../../../apps/desktop/README.md). Kiểm pipe dev không thay native launcher. Chưa build Cargo/Tauri, chưa chạy WebView2, shell crash/Job Object, execution owner xuyên session/hai bản cài/PID reuse, Unicode native path hay clean installer. Thiếu Rust/Cargo/MSVC/Tauri CLI binary và harness cross-session; không đánh dấu task hoặc G1 hoàn tất. Native command giữ trạng thái chưa hỗ trợ cho tới khi đủ implementation và kiểm chứng. SPEC-009 native resolver và SPEC-004 tích hợp tiếp tục theo launcher/owner dependency.

[Bàn giao cuối](../evidence/codegen-2026-11-08/handoff.md) lưu lượt agent chính chạy lại toàn bộ: 55/14/2 Python tests, 7 DOM tests, hai artifact checks, typecheck và frontend build đều pass. [Review độc lập](../evidence/codegen-2026-11-08/final-review-report.md) không còn finding chặn sau sửa timeout UI/abort/stale handoff; timeout 10 giây chỉ cho phục hồi kết nối kỹ thuật, không là business SLO. Không có native/browser test được suy ra từ kết quả này.
