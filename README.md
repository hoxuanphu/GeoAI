# GeoAI

Ứng dụng Windows desktop xử lý GIS/AI cục bộ, thiết kế theo [đề xuất v1.4](Artchitect/solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md). Feature đầu đề xuất: HLS 30 m → Prithvi-EO-2.0 + UPerNet → review → thống kê → PDF.

Đã triển khai contracts Pydantic dự thảo, JSON-RPC/context metadata, exporter, API health/capabilities và UI shell React. Native Tauri mới là scaffold trả lỗi chưa hỗ trợ; chưa có launcher/owner/Job Object đã kiểm, database, GIS/AI/solver hay installer. Trạng thái và đầu vào còn chờ ở [roadmap](Artchitect/docs/roadmap.md), [task tracker](Artchitect/docs/task-tracker.md) và [nhật ký triển khai](Artchitect/docs/evidence/codegen-2026-11-08/progress.md). G0 chưa đạt.

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

Đợt kiểm hiện tại dùng Python/package đã có trên máy vì tải wheel mới bị HTTP 403 sau khi TLS đã xác minh; chưa chứng minh cài mới sạch. [Môi trường và thử thiết lập](Artchitect/docs/evidence/codegen-2026-11-08/setup-experiments.md) ghi giới hạn này. Không tắt xác minh TLS để cài dependency.

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

Trust store Windows giữ xác minh TLS. Lockfile được resolve thực; Rollup/esbuild dùng package WASM để build frontend trong môi trường chặn binary native. UI trình duyệt hiện trạng thái chưa nhận phiên desktop; nút thử lại và state panel hoạt động nhưng chưa có native handoff thật. [README shell](apps/desktop/README.md) mô tả session/Host/Origin/token, dev pipe protocol và phần native cần triển khai. `npm run build` chỉ build frontend; chưa có Cargo/Tauri/WebView2 hoặc installer test.
