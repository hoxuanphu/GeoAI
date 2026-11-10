# Chỉ mục ADR

Ngày cập nhật: 10/11/2026. Các mã 001–008 giữ chủ đề của [sổ v1.4](../../plans/16_quyet_dinh_can_chot_va_danh_doi.md#muc-17-1); 009–010 cụ thể hóa IPC và toán–vật lý; 011 bổ sung execution owner liên project/instance/session sau review; 012 mở rộng desktop Ubuntu LTS. Theo yêu cầu người dùng, hồ sơ đặt tại Artchitect/docs/adr. ADR-008 ghi yêu cầu Prithvi đã xác nhận; ADR-012 phân biệt yêu cầu Ubuntu đã xác nhận với lựa chọn adapter/packaging còn đề xuất. Các lựa chọn kỹ thuật chưa được nâng thành Accepted từ tài liệu.

| ADR | Chủ đề | Trạng thái |
| --- | --- | --- |
| [ADR-001](ADR-001-desktop-first.md) | Windows desktop trước, server theo nhu cầu | Định hướng kế thừa; ràng buộc triển khai cụ thể còn cần G0 |
| [ADR-002](ADR-002-sqlite-repository.md) | SQLite WAL sau repository và migration | Đề xuất thiết kế; chưa kiểm chứng migration/recovery |
| [ADR-003](ADR-003-viewer.md) | Giro3D và adapter viewer phạm vi hẹp | Đề xuất có điều kiện fixture G1 |
| [ADR-004](ADR-004-cpu-runtime.md) | CPU chính thức, NVIDIA tùy chọn, ưu tiên ONNX | Đề xuất có điều kiện runtime/benchmark G1–G2 |
| [ADR-005](ADR-005-crs.md) | Backend quản lý CRS và TransformSpec | Đề xuất thiết kế; cần điểm khống chế/tolerance G0–G1 |
| [ADR-006](ADR-006-packaging.md) | Khóa dependency và chọn sidecar từ máy sạch | Đề xuất; công cụ đóng gói cuối chưa chốt |
| [ADR-007](ADR-007-reporting.md) | PDF Typst từ revision và metrics snapshot | Đề xuất; cần fixture tiếng Việt/offline |
| [ADR-008](ADR-008-prithvi-required.md) | Prithvi-EO-2.0 dùng cho phân tích ngay bản đầu | Yêu cầu sản phẩm đã được người dùng xác nhận; cấu hình kỹ thuật chưa nghiệm thu |
| [ADR-009](ADR-009-ipc-attempts.md) | JSON-RPC local và fencing theo attempt | Đề xuất thiết kế; wire draft 0.1.0, chưa có transport |
| [ADR-010](ADR-010-physical-models.md) | Mô hình toán–vật lý theo Domain Pack | Đề xuất thiết kế; GEO-01 bản đầu, PHY chọn từng feature G4 |
| [ADR-011](ADR-011-local-execution-owner.md) | Quyền thực thi local giữa project/instance/session | Đề xuất có điều kiện G1; một owner/tài khoản Windows trên máy, chưa nghiệm thu |
| [ADR-012](ADR-012-ubuntu-desktop.md) | Ubuntu 22.04/24.04 LTS: WebKitGTK, supervisor/owner, FD/I/O và `.deb` | Mục tiêu OS đã xác nhận; thiết kế kỹ thuật đề xuất, chưa triển khai/kiểm Linux |

[SPEC-010](../specs/010-ubuntu-foundation.md) cụ thể hóa profile/interface của ADR-012 để làm đầu vào gen code; ADR vẫn đề xuất. Quyết định thiết kế, nghiệm thu foundation và công bố hỗ trợ sản phẩm là các trạng thái riêng, không đợi tất cả UB-01–20 mới được viết phần nền đủ dependency.

Một ADR hoàn chỉnh có bối cảnh, lựa chọn, phương án, hệ quả, người chốt/bằng chứng và điều kiện xem lại. Không đánh dấu Accepted vì file đã được tạo; không dùng trạng thái đề xuất để bỏ yêu cầu sản phẩm đã xác nhận. Liên kết ADR thay thế khi có quyết định mới và cập nhật roadmap/tài liệu nguồn chịu ảnh hưởng.

