# Yêu cầu Ubuntu LTS và đánh giá kiểm thử Cloud — 10/11/2026

## Yêu cầu được ghi nhận

Người dùng yêu cầu bộ cài Linux và bổ sung Ubuntu 22.04 LTS vào hướng Ubuntu 24.04 LTS đã đề xuất. Ghi cả Ubuntu 22.04 LTS và 24.04 LTS vào mục tiêu hỗ trợ cần triển khai/kiểm chứng, bên cạnh Windows. Kiến trúc CPU x86_64 là đề xuất ban đầu; chưa chốt ARM64, support matrix phần cứng hoặc lịch phát hành. Yêu cầu nền tảng không đồng nghĩa runtime/bộ cài đã được nghiệm thu.

Đây là hồ sơ tiếp nhận yêu cầu và đánh giá khả thi, chưa quyết định primitive Linux hoặc thay thế các ADR Windows. Trước triển khai phải bổ sung ADR mở rộng nền tảng, liên kết ADR-001/006/011 và đồng bộ tài liệu thiết kế nguồn, SPEC-003/004/009. Prithvi + decoder nghiệp vụ vẫn là yêu cầu bản đầu; G0–G4 giữ nguyên trạng thái.

## Nguồn đã đọc ngày 10/11/2026

- [Tauri 2 — Debian](https://v2.tauri.app/distribute/debian/): khuyến nghị build trên hệ cũ nhất được hỗ trợ có WebKitGTK 4.1; nêu Ubuntu 22.04 là nền phù hợp. Build trên hệ mới có thể làm tăng yêu cầu glibc. Đây là hướng dẫn Tauri, chưa là bằng chứng GeoAI tương thích.
- [Tauri 2 — prerequisites](https://v2.tauri.app/start/prerequisites/): Linux cần các thư viện hệ thống, gồm `libwebkit2gtk-4.1-dev` cho build.
- [OpenAI Docs — Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments): môi trường dùng repository/dependency/tool được cấu hình, có thể chạy lệnh và kiểm workflow; tạo qua Work in > Cloud hoặc Settings > Codex Cloud > Environments. Cần kiểm tài nguyên và quyền truy cập thực của môi trường được chọn.

## Hiện trạng source và môi trường

- `apps/desktop/src-tauri/src/main.rs`: nhánh ngoài Windows trả `windows_required` khi bootstrap; `tauri.conf.json` vẫn `bundle.active=false`.
- `backend/geoai/bootstrap.py`, `jobs/native_process.py`, `jobs/transport.py`, `storage/windows_owner.py`, `storage/windows_io.py`: có phụ thuộc Windows; resolver/publisher/extraction cũng sử dụng native I/O này. Chưa có adapter Linux được kiểm chứng.
- `pyproject.toml` yêu cầu Python >=3.12. Không được giả định Python hệ thống của hai bản Ubuntu đáp ứng; cần runtime Python riêng, dependency lock và kiểm khả năng đóng gói từng nền tảng.
- Executor của phiên hiện tại là workspace Windows local. Danh sách công cụ phiên không có `cloud_environment.environment_status` hoặc executor Linux Cloud. Không có lần chạy Cloud/Linux nào được thực hiện trong đánh giá này; không suy tài khoản người dùng đã có môi trường/GPU/Docker sẵn.

## Kế hoạch kiểm thử cần thực hiện

| Nhóm | Cách kiểm dự kiến | Giới hạn bằng chứng |
| --- | --- | --- |
| Contracts/backend thuần, SQLite/migration, frontend | Chạy trên userland Ubuntu 22.04 và 24.04, phân biệt pass/skip/fail; dùng Python phù hợp | Không chứng minh native launcher/GIS/model |
| Native build và `.deb` | Build trên Ubuntu 22.04; kiểm executable, Python sidecar và mọi thư viện native; kiểm dependency/runtime trên cả hai LTS | Build thành công chưa chứng minh app chạy; có thể cần gói riêng nếu dependency hai LTS khác nhau |
| Desktop tự động | Tauri thực + WebKitGTK/WebDriver, Xvfb/D-Bus nếu môi trường đáp ứng; startup, token/Origin, Unicode, đóng/crash, owner giữa instance/session và resolver | Playwright/Chromium chỉ kiểm frontend web; Xvfb không chứng minh Wayland hoặc GPU thật |
| Bộ cài máy sạch | VM/desktop Ubuntu 22.04 và 24.04: install, launch, upgrade, uninstall, dữ liệu giữ đúng; gói offline kiểm riêng | Container dùng kernel host, không thay nghiệm thu desktop/máy sạch G3 |
| GIS/viewer/Prithvi | Fixture/profile theo gate; CPU kỹ thuật khi đủ tài nguyên; NVIDIA/driver và hiệu năng trên phần cứng phù hợp | Không giả định Cloud có GPU; phần mềm render không thay benchmark AMD/Intel/NVIDIA hoặc máy đích |

Cloud có thể dùng cho các kiểm tra trên khi có đúng OS/tool/dependency/tài nguyên. Nếu host Cloud không chạy đúng Ubuntu mục tiêu, dùng container Ubuntu 22.04/24.04 khi Docker thực sự khả dụng hoặc executor/VM ngoài tương ứng. Phải kiểm preflight trước khi hứa build/desktop test. Dùng checkout cùng revision và đưa đủ thay đổi local cần kiểm vào Cloud; không coi checkout Cloud tự chứa thay đổi chưa commit của máy Windows. Không đưa credential, dữ liệu khách hàng hoặc trọng số lớn vào repository/log.

## Trạng thái và việc còn chờ

Đã ghi yêu cầu và đối chiếu nguồn/source; chưa triển khai Linux, chưa chạy test/build/installer trên Linux hoặc Cloud. Còn chờ ADR/thiết kế adapter, cấu hình executor, dependency lock, bằng chứng chạy hai LTS và nghiệm thu các gate liên quan. Kiểm cấu trúc/liên kết của hồ sơ này được lưu tại [kết quả kiểm tài liệu](2026-11-10-linux-support-doc-check.json); kết quả đó chỉ chứng minh tài liệu hợp lệ.
