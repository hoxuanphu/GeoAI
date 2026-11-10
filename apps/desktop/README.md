# GeoAI shell foundation

Phần có thể kiểm độc lập trước G0: React UI giữ state trong App, nhận descriptor qua Tauri invoke, gọi hai route metadata bằng header. Browser mode hiện lỗi handoff và nút thử lại. Chưa có viewer, project writer, worker, inference hay native execution owner.

UI chờ handoff/kết nối tối đa 10 giây rồi hiện thử lại, abort fetch và bỏ kết quả trễ của lần cũ. Đây là deadline kỹ thuật để UI không treo ở loading, không là CPU SLO/ngưỡng hiệu năng G0 hay timeout công việc nghiệp vụ.

## Thiết lập và kiểm

Node 24/npm 11; Python 3.12 với extra `.[api,test]` trong môi trường riêng. Máy hiện tại dùng Python global đã có dependency do tải wheel mới bị HTTP 403; không thay global installs. Từ root:

```powershell
$env:PYTHONPATH = 'backend'
python -m unittest discover -s tests/contracts -v
python -m unittest discover -s tests/integration -v
python tools/export_contract_schemas.py --check
python tools/export_api_client.py --check
cd apps/desktop
$env:NODE_USE_SYSTEM_CA = '1'
npm ci
npm test
npm run typecheck
npm run build
npm run dev
```

`NODE_USE_SYSTEM_CA=1` dùng trust store Windows, không vô hiệu TLS. Package lock sinh từ npm resolve thật. Toolchain frontend là Vite 7/Vitest 4/TypeScript 5.9; npm overrides dùng `@rollup/wasm-node` và `esbuild-wasm` vì native binaries bị policy HTTP403. Đây là package WASM chính thức, không vá node_modules hoặc cài compiler máy. `npm run api:generate` sinh OpenAPI/client; `api:check` phát hiện artifact cũ. Không sửa tay response TypeScript hoặc JSON Schema; descriptor IPC cũng sinh từ Pydantic private runtime DTO.

## Phiên local và dev sidecar

Không có URL token, env token, localStorage hoặc console token. Các route đòi `Authorization: Bearer <token>`, Host chính xác `127.0.0.1:<cổng phiên>`, Origin có trong policy. Production Origin là `tauri://localhost` hoặc `http://tauri.localhost`; dev thêm duy nhất `http://127.0.0.1:1420`. Header nhạy cảm lặp bị từ chối. Thiếu Origin chỉ được phép khi caller đã cấu hình `allow_missing_origin=True`, vẫn bắt token/Host. Origin `null` bị chặn.

CORS preflight hợp lệ chỉ trả metadata 204 cho GET hai route, header authorization, Host/Origin hợp lệ; không trả dữ liệu hay cấp quyền GET. Request thật luôn cần token. API không hỗ trợ query params; token query không cấp quyền. Access logging Uvicorn tắt, diagnostic sink loại raw URL/header/exception text. Không có endpoint đọc path/URL tùy ý hoặc shutdown không xác thực.

`python -m geoai.bootstrap --dev-stdio-handoff --no-console` **chỉ dành cho test harness/launcher dev sở hữu anonymous stdin/stdout pipes**, không chạy trực tiếp trong terminal và không redirect descriptor vào file/log. Cả hai flag bắt buộc; kiểm file type cấm console/file handoff. Stdout chỉ nhận một descriptor sau server startup; stdin nhận dòng điều khiển hoặc EOF để dừng. Socket bind `127.0.0.1:0` một lần và truyền nguyên cho Uvicorn. Test process thật thực hiện giao thức này mà không in descriptor. Cơ chế này không cấp execution owner, không khởi project writer/job, không chứng minh chống shell crash bằng Job Object.

## Native chưa khả dụng

`src-tauri` đã có source launcher Tauri v2 **chưa compile/kiểm native**: command chỉ cho main webview tại URL local tin cậy, tạo sidecar bằng Job Object/handle allowlist nguyên tử, nhận descriptor qua pipe riêng và dừng nhóm có deadline. Debug runtime lấy `GEOAI_DEV_PYTHON`/`GEOAI_DEV_BACKEND` lúc compile; release chỉ dùng `geoai-sidecar.exe` trong resource bundle đã cấu hình. Chưa tạo sidecar bundle hay Cargo.lock giả. [Báo cáo native](../../Artchitect/docs/evidence/backend-pre-g0-2026-11-08/task-7-report.md) phân biệt ctypes đã kiểm và Rust chưa build. Đợt cài toolchain trước gặp Rustup/Tauri HTTP403 và Build Tools 1602/UAC; lượt tiếp tục code không thử cài lại. UI build không đồng nghĩa Tauri build hoặc WebView2 acceptance.

Trước khi nối launcher thật: triển khai execution owner liên process/cùng tài khoản xuyên session với ACL/epoch/PID creation time; nhận quyền trước writer/worker; anonymous handle handoff; Job Object containment; shutdown deadline; abandoned-owner recovery chờ worker native thực sự dừng; test hai bản cài/cross-session/shell crash/PID reuse. Cần compile trên Windows phù hợp, kiểm CSP/Origin thực WebView2 và native lifecycle tests trước khi bật capability. Owner lock không thay attempt fencing. SPEC-003 vẫn partial; G0/G1 chưa đóng.
