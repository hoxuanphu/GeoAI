# Môi trường triển khai ngày 08/11/2026

Múi giờ báo cáo: Asia/Bangkok. [Inventory môi trường](environment.json) ghi version thực. Workspace chưa có Git; baseline code/docs được hash trước khi sửa.

| Kiểm tra/lệnh | Kết quả quan sát |
| --- | --- |
| `git status --short` | Exit 128: không phải Git repository; không init Git hoặc tạo worktree |
| `python -m unittest discover -s tests/contracts -v` với `PYTHONPATH=backend` | Exit 1, 30 tests, 1 failure/45 errors gồm subtests; public registry/exports và exporter chưa có. [Log](contracts-baseline.log) |
| `python --version` / Pydantic import | Python 3.12.4 / Pydantic 2.13.2 có ở interpreter hiện tại |
| `venv/Scripts/python.exe` / Pydantic import | Python 3.12.4; môi trường `venv` có sẵn nhưng thiếu Pydantic |
| `venv/Scripts/python.exe -m pip install -e .` | Exit 1: certificate verify failed khi resolve build dependency |
| Lệnh trên với `--use-feature=truststore` | Exit 1: build isolation subprocess vẫn lỗi certificate |
| Lệnh trên với `PIP_CERT` trỏ bundle ROOT/CA Windows sinh trong thư mục Temp | TLS xác minh được; exit 1 do tải setuptools wheel bị HTTP 403 `MediaTypeBlocked`. Không tắt TLS hoặc đổi sang HTTP |
| `node --version`, `npm --version` | v24.19.0 / 11.17.0 |
| `npm ping --fetch-retries=0 --fetch-timeout=15000` | Exit 1: `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` |
| Lệnh npm ping với `NODE_USE_SYSTEM_CA=1` | Exit 0, PONG; `npm view @tauri-apps/cli version` trả 2.12.4 |
| `Get-Command cargo,rustc`, kiểm `.cargo/bin/cargo.exe` và Visual Studio Installer/Build Tools | Không có Rust/Cargo/MSVC được tìm thấy; chưa thể build/test native Tauri |

Kiểm Python trong đợt này dùng interpreter/package đã có với `PYTHONPATH=backend`; không xem đây là bằng chứng cài mới sạch hoặc environment GIS/AI đã khóa. Bundle CA chỉ có public certificates, nằm ở Temp; không thêm certificate cá nhân hoặc credential vào source. Không thay proxy policy hay cài toolchain toàn máy.

Thiếu Rust/MSVC và test harness khác Windows session chặn acceptance native của SPEC-003. Chỉ tiếp tục các phần nền độc lập có thể kiểm. SPEC-009 I/O/native và SPEC-004 tích hợp còn cần launcher/context đã kiểm; SPEC-005/008/006 còn thiếu đầu vào thực G0 theo roadmap. Các giới hạn này không thay thế thiết kế hay hạ gate.
