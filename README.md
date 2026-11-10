# GeoAI

Ứng dụng Windows desktop xử lý GIS/AI cục bộ, thiết kế theo [đề xuất v1.4](Artchitect/solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md). Feature đầu đề xuất: HLS 30 m → Prithvi-EO-2.0 + UPerNet → review → thống kê → PDF.

Đã có contracts Pydantic dự thảo, IPC/coordinator core, policy/grant/resolver, native Windows owner/Job Object và I/O đã kiểm bằng fixture, source repository SQLAlchemy/Alembic và publisher. API vẫn chỉ health/capabilities; UI shell React giữ capability thực thi tắt. Rust/Tauri đã có source launcher nhưng chưa build; tests DB còn skip vì thiếu dependency. Chưa có GIS/AI/solver nghiệp vụ hoặc installer đã nghiệm thu. Trạng thái và bằng chứng ở [roadmap](Artchitect/docs/roadmap.md), [task tracker](Artchitect/docs/task-tracker.md) và [tiến độ backend](Artchitect/docs/evidence/backend-pre-g0-2026-11-08/progress.md). G0 chưa đạt.

## Bắt đầu

1. Đọc [AGENTS.md](AGENTS.md), [chỉ mục tài liệu](Artchitect/docs/README.md), [roadmap](Artchitect/docs/roadmap.md).
2. Chọn task ở [Artchitect/docs/specs](Artchitect/docs/specs/README.md), đọc các hợp đồng/ADR mà task dẫn chiếu.
3. Đọc [hướng dẫn dev](Artchitect/docs/development-guide.md) để chọn task có đủ dependency; chỉ phần được ghi rõ mới chạy trước G0. Không dùng fixture tổng hợp làm dữ liệu/model/gate nghiệp vụ.

## Kiểm tra Python

Python 3.12; contracts chỉ cần Pydantic, API/test dùng extras bên dưới. Thiết lập môi trường riêng khi package registry cho phép:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[api,test]"
$env:PYTHONPATH = 'backend'
.venv\Scripts\python.exe -m unittest discover -s tests/contracts -v
.venv\Scripts\python.exe -m unittest discover -s tests/integration -v
.venv\Scripts\python.exe -m unittest discover -s tests/architecture -v
.venv\Scripts\python.exe tools/export_contract_schemas.py --check
.venv\Scripts\python.exe tools/export_api_client.py --check
```

Đợt kiểm 09/11/2026 có 57 contracts tests pass bằng Python/package đã có; `.venv-clean` đã tạo với system packages tắt nhưng tải wheel vẫn bị HTTP 403 `MediaTypeBlocked`, chưa chứng minh cài mới sạch. [Kết quả sửa môi trường](Artchitect/docs/evidence/environment-2026-11-09/results.json): đã lưu user `NODE_USE_SYSTEM_CA=1`, npm restore/7 DOM tests/typecheck/frontend build pass; Rustup/Tauri native còn bị 403, Build Tools dừng 1602 ở bước UAC/elevation. [Môi trường và thử thiết lập](Artchitect/docs/evidence/codegen-2026-11-08/setup-experiments.md) ghi giới hạn này. Không tắt xác minh TLS để cài dependency.

Sinh lại artifact bằng `python tools/export_contract_schemas.py` và `python tools/export_api_client.py`; Pydantic là nguồn kiểu, không sửa tay JSON Schema/OpenAPI/client. Các test không tải model/provider hay yêu cầu GPU. Process test chỉ kiểm metadata API dev qua pipe riêng; chưa chứng minh native shell crash containment hoặc chất lượng nghiệp vụ.

## UI shell

Node 24/npm 11; từ root:

```powershell
Set-Location apps/desktop
$env:NODE_USE_SYSTEM_CA = '1'
npm ci
npm test
npm run typecheck
npm run build
npm run dev
```

Trust store Windows giữ xác minh TLS. Lockfile được resolve thực; Rollup/esbuild dùng package WASM để build frontend trong môi trường chặn binary native. [README shell](apps/desktop/README.md) mô tả session/Host/Origin/token, dev pipe protocol và source native. `npm run build` chỉ build frontend; Cargo/Tauri/WebView2 và installer vẫn chưa có phép kiểm thực. Kiểm khả dụng không cài dependency: `python Artchitect/docs/evidence/backend-pre-g0-2026-11-08/verify.py`; báo cáo tách pass/skip và không đóng gate bằng fixture.
