# ADR-006: Khóa dependency và chọn sidecar từ máy sạch

**Trạng thái:** Đề xuất; công cụ đóng gói cuối chưa chốt. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../architecture.md).

**Mở rộng Ubuntu 10/11/2026:** [ADR-012](ADR-012-ubuntu-desktop.md) và [guide Linux](../platforms/ubuntu/ubuntu-development-and-packaging.md) đề xuất `.deb` build từ 22.04, kiểm ABI/dependency/runtime trên cả 22.04 và 24.04 LTS. NSIS/WebView2 dưới đây thuộc Windows; công cụ freeze Python và lock Linux phải được resolve/kiểm thật, không suy từ pack Windows.

## Bối cảnh

Stack native GDAL/PROJ/codec/ORT/CUDA và WebView2 có tài nguyên ngoài package Python.

## Lựa chọn

Pixi/lockfile theo OS/architecture, tránh cùng package hai nguồn. So environment di chuyển được và PyInstaller onedir bằng fixture; NSIS Standard trước, Offline khi kiểm đủ.

## Phương án đã cân nhắc

Chỉ wheel pip có thể nhiều GDAL/PROJ; chọn PyInstaller vì tên công cụ không chứng minh đủ DLL/data; build mọi MSI/EXE/ARM tổ hợp tăng ma trận.

## Hệ quả

Pack manifest/chữ ký/hash/tương thích; WebView2 offline, fonts/WASM/PROJ grid; không tự cài driver.

## Bằng chứng và người chốt

G1 so phương án; G3 Windows sạch tài khoản thường, đường dẫn tiếng Việt, mất mạng/thiếu đĩa, upgrade/restore/uninstall. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Khi support matrix, runtime hoặc chính sách triển khai thay đổi. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

