# Chuẩn bị môi trường build Ubuntu trong Cloud — 11/11/2026

Baseline source: `d4e0060`, nhánh `feat/ubuntu-installer`; giữ nguyên các thay đổi tài liệu và A-01 chưa commit có sẵn. Theo yêu cầu người dùng, ưu tiên chuẩn bị compiler/dependency cho bản build Ubuntu trước runtime foundation đầy đủ. Không tạo nhánh, commit hoặc push.

## Kết quả

Đã dựng image Docker `geoai-ubuntu-build:22.04` trên host Debian 13; container Ubuntu 22.04.5 amd64/glibc 2.35 chạy dưới UID/GID 1000. Docker dùng vfs nên wrapper tái sử dụng container, tránh chép image mỗi lệnh. Rust/Cargo 1.99.1, Python 3.12.16, uv 0.13.7, Node 24.20.0/npm 11.19.0, Tauri CLI 2.12.4; có compiler C/C++, pkg-config, GTK 3/WebKitGTK 4.1, OpenSSL, librsvg, libxdo, patchelf, dpkg, Xvfb và D-Bus session. Base image digests, Python và uv đã pin từ resolve thực. [Preflight](preflight.log), [system packages](system-packages.txt), [Python packages](python-packages.txt) và [kết quả/hash](results.json).

Bộ script tại `tools/ubuntu-build/`: build image, setup dependency, preflight, verify và wrapper mở shell/chạy lệnh. State Python/npm/Cargo/target nằm trong `.venv-ubuntu-env/` đã được gitignore; `.venv` và host node_modules được giữ. Wrapper đặt python mặc định vào `/state/python`, không thay Python hệ thống Ubuntu hoặc Debian. Proxy/CA được cấp lúc build/run, không đóng session CA/credential vào image.

## Kiểm chứng

Chạy từ repo root:

```bash
tools/ubuntu-build/build-image.sh
tools/ubuntu-build/run.sh bash tools/ubuntu-build/setup.sh
tools/ubuntu-build/run.sh bash tools/ubuntu-build/verify.sh
```

Setup exit 0. Verify lượt cuối exit 1 duy nhất do lỗi DB có sẵn; từng trạng thái ở [status](status.txt). Cargo check, frontend, schema/client, pip check, Xvfb/D-Bus và native-link đều exit 0. [Cargo check](cargo-check.log) là kiểm biên dịch Rust/Tauri, không phải tạo binary hay installer.

| Suite | Tổng | Pass | Skip | Error |
| --- | ---: | ---: | ---: | ---: |
| contracts | 58 | 58 | 0 | 0 |
| integration | 56 | 14 | 42 | 0 |
| architecture | 2 | 2 | 0 | 0 |
| catalog | 9 | 9 | 0 | 0 |
| storage | 78 | 55 | 22 | 1 |
| jobs | 17 | 17 | 0 | 0 |
| Tổng | 220 | 155 | 64 | 1 |

Frontend 7/7 tests pass và Vite/typecheck build pass. `test_attempt_state_tracks_publication_cancel_and_stop` vẫn lỗi `CursorResult` tại `tests/storage/test_repository.py:288`, xem [storage log](storage.log); không sửa hoặc skip assertion. 64 skip thuộc Windows, không là bằng chứng native thành công.

[Native link smoke](native-link.log) thực sự biên dịch C, link GTK/WebKitGTK và gọi gtk_init_check dưới Xvfb. AT-SPI bus chưa có nên có warning accessibility; phép kiểm này không nghiệm thu accessibility/WebKit rendering của app. Cargo check còn 3 warnings về mut/validate không dùng trên Linux, không thêm lint suppression.

## Các lỗi source được lộ ra khi kiểm compiler

Lượt đầu Cargo check không tìm thấy `icons/icon.png`; bổ sung placeholder từ template Tauri, chuyển RGBA bằng chính Tauri CLI. Source/license được ghi tại `apps/desktop/src-tauri/icons/README.md`; cần thay bằng icon sản phẩm trước release.

Sau đó compiler tái hiện E0597 (temporary MutexGuard sống lâu hơn state) và deny(let_underscore_lock) ở nhánh non-Windows. Sửa tối thiểu: thêm dấu chấm phẩy để guard được drop trước state và dùng `drop(session)` rõ ràng. Cargo check đỏ → xanh, lượt cuối verify exit Cargo 0. Không sửa cơ chế Windows owner/process/I/O, capabilities hoặc triển khai backend Linux. `Cargo.lock` được Cargo sinh từ fetch thực, không viết tay.

## Giới hạn và việc tiếp theo

Môi trường compiler/dependency Ubuntu đã kiểm được trong Cloud; chưa cần phương án dự phòng Debian cho bước này. Chưa tạo `.deb`/binary, chưa khởi chạy app Tauri hoặc nghiệm thu Ubuntu 24.04/Windows. Container chia sẻ kernel host, không có systemd user manager/desktop thật và không thay fixture ext4 hoặc VM máy sạch. Bước build shell/packaging vẫn cần cấu hình artifact và tài nguyên phù hợp. Nhánh non-Windows vẫn trả `windows_required`; UI build không chứng minh backend/worker đã chạy Linux.

A-01 vẫn partial; 010.1 cần baseline hai LTS và Windows regression, 010.2–010.3/G0–G4 chưa đóng. Tiếp tục phần có thể chạy bằng wrapper, không dùng thiếu kiểm Windows để chặn chuẩn bị/build shell Ubuntu.
