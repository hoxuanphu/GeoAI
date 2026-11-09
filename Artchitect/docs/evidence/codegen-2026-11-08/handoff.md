# Bàn giao code foundation — 08/11/2026

**Kết quả:** SPEC-001 hoàn tất phạm vi schema draft 0.1.0; SPEC-003 hoàn tất phần nền API/session/UI có thể kiểm độc lập, chưa hoàn tất native desktop acceptance. G0/G1 vẫn chưa đạt. Thực hiện bằng Superpowers, Codex triển khai và hai lượt review độc lập; chưa có người phụ trách gate được xác nhận để thay quyết định nghiệp vụ/GIS/ML.

## Code và phạm vi đã kiểm

- Pydantic run/revision/evaluation/metrics/report, JSON-RPC method/event, private worker context/bootstrap, registries; exporter JSON Schema xác định và fixture âm/dương.
- FastAPI health/capabilities có Host/Origin/session-token boundary, CORS preflight có giới hạn, redaction, bootstrap pipe dev và real-process startup/stop/EOF/token-rotation tests. Chỉ công bố metadata; inference/native launcher/owner/project writer đều false.
- Health/capability và private session handoff DTO từ Pydantic; OpenAPI/TypeScript client sinh và có stale checks. Token chỉ trong bộ nhớ/pipe private, không thuộc record project bền vững.
- React/Vite UI tiếng Việt có lỗi/thử lại, timeout/abort và chặn kết quả kết nối cũ; state giữ qua panel. Tauri v2 scaffold chỉ trả lỗi chưa hỗ trợ, không tạo process hay token giả.
- Kiểm static import theo architecture và giới hạn contracts chỉ dùng stdlib/Pydantic. Các package/adapter chưa có task chưa được tạo rỗng.

Chi tiết file/quyết định ở [Task 1](task-1-report.md), [review contracts](task-2-review-report.md), [Task 3](task-3-report.md) và [review cuối](final-review-report.md). Finding FR-01 về kết nối treo đã sửa và kiểm lại; không còn finding code/security chặn trong phạm vi này.

## Lượt kiểm cuối do agent chính chạy

Môi trường: Windows 11 AMD64, CPython 3.12.4/Pydantic 2.13.2, FastAPI 0.141.1/Uvicorn 0.49.0/httpx 0.28.1; Node 24.19.0/npm 11.17.0. Ngày báo cáo 08/11/2026, Asia/Bangkok. [Inventory môi trường](environment.json), [thử thiết lập và giới hạn](setup-experiments.md). Python dùng package đã có; chưa có bằng chứng cài Python mới sạch.

Python chạy ở root với `PYTHONPATH=backend`; npm chạy ở `apps/desktop` với trust store Windows. Mọi lệnh sau exit 0; thời lượng thực và command arrays ở [Python checks](final-python-checks.json), [frontend checks](final-frontend-checks.json).

| Lệnh | Kết quả | Log |
| --- | --- | --- |
| `python -m unittest discover -s tests/contracts -v` | 55 pass, không fail/skip | [contracts](final-contracts.log) |
| `python -m unittest discover -s tests/integration -v` | 14 pass, không fail/skip | [integration](final-integration.log) |
| `python -m unittest discover -s tests/architecture -v` | 2 pass, không fail/skip | [architecture](final-architecture.log) |
| `python tools/export_contract_schemas.py --check` | Artifact current | [schema](final-schema.log) |
| `python tools/export_api_client.py --check` | OpenAPI/client current | [API artifacts](final-api-artifacts.log) |
| `npm test` | 7 DOM tests pass | [DOM](final-npm-tests.log) |
| `npm run typecheck` | Pass | [typecheck](final-typecheck.log) |
| `npm run build` | Vite frontend production build pass | [build](final-frontend-build.log) |

Tổng: 71 Python tests và 7 DOM tests. Baseline trước sửa code có 30 tests, 1 failure/45 errors gồm subtests; [log mới chạy ở đầu phiên](contracts-baseline.log). Kết quả này không là phép đo ML/GIS/native hoặc performance nghiệp vụ.

`npm ci` được agent triển khai chạy lại thành công từ package-lock thật; audit tại thời điểm resolve có 0 vulnerabilities. WASM Rollup/esbuild được cấu hình trong package/lock để tránh binary bị HTTP403, không vá node_modules. Review chỉ kiểm độc lập tests/build, không tuyên bố tự cài lại dependency. Không tạo Cargo.lock giả hoặc tắt TLS. Package snapshot là môi trường dev, chưa là support matrix GIS/AI phát hành.

## Việc còn chờ và ranh giới bằng chứng

| Phần | Trạng thái / điều kiện tiếp tục |
| --- | --- |
| SPEC-003 native | Thiếu Rust/Cargo/MSVC/Tauri CLI binary và harness cross-session. Chưa compile Tauri, chạy WebView2/CSP/Origin thật, shell crash/Job Object, owner ACL/namespace/epoch/PID reuse, hai bản cài/hai session hay Unicode native paths |
| SPEC-009 / SPEC-004 | Typed context có rồi; native bootstrap/registry/resolver/importer/provider, owner/launcher, worker IPC, SQLite/migration/publish/fencing/recovery chưa triển khai/kiểm. Tiếp tục theo dependency; không coi schema pass là quyền I/O hoặc fencing |
| SPEC-002 / SPEC-005 / SPEC-008 / SPEC-006 | Còn đầu vào thực G0: AOI kiểm định, HLS band/QA có quyền, QC/nhãn/split/profile/CRS/điểm chuẩn, hardware/protocol/budget và người chốt. Không tự đặt input hoặc training/benchmark/checkpoint/gate giả |
| SPEC-007 / G3 / G4 | Chưa có GIS/viewer/PDF/native bundle/clean installer acceptance; PHY cần feature/profile/provenance có kiểu riêng. RunManifest chặn physical refs/provenance tới lúc đó |

Bootstrap dev chỉ kiểm metadata API qua pipe riêng; không thay native production launcher, owner lock hay crash containment. DOM tests dùng React DOM với doubles tại handoff/fetch; chưa chạy trình duyệt đồ họa hoặc WebView2. Timeout UI 10 giây là giá trị phục hồi kết nối kỹ thuật, không là SLO nghiệp vụ được duyệt. Các ca native còn thiếu được ghi là chưa kiểm, không tạo skip giả để tính pass.

Không có Git repository: không init/commit/merge/push. [Baseline inventory](baseline-inventory.json) và [88 source/config/docs hashes cuối](final-inventory.json) ghi trạng thái file thực; không mất file baseline, test contracts và workflow fixture gốc giữ nguyên. [Kiểm tài liệu cuối](final-docs-check.json): 60 Markdown, 447 link nội bộ, 16 anchor, 5 JSON blocks không lỗi UTF-8/fence/link/parse; không render Mermaid. Không tải weights, dữ liệu khách hàng hoặc provider credentials. Roadmap/spec/tracker và README đã đồng bộ với phạm vi/bằng chứng này.
