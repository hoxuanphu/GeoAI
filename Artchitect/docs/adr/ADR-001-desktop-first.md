# ADR-001: Windows desktop trước, server theo nhu cầu

**Trạng thái:** Định hướng kế thừa; ràng buộc triển khai cụ thể còn cần G0. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../architecture.md).

**Mở rộng 10/11/2026:** người dùng bổ sung Ubuntu 22.04 LTS và Ubuntu 24.04 LTS bên cạnh Windows. [ADR-012](ADR-012-ubuntu-desktop.md) ghi thiết kế adapter đề xuất; desktop local vẫn là hướng triển khai, server vẫn mở riêng ở G4. Phần Windows trong hồ sơ này giữ phạm vi/bằng chứng lịch sử; chưa có nghiệm thu Linux.

## Bối cảnh

Người dùng cần quy trình GIS/AI chạy cục bộ trên máy Windows, có khả năng offline và dữ liệu ở local.

## Lựa chọn

Dùng Tauri/React/Giro3D và Python sidecar/worker local. Server là mở rộng G4 khi cần chia sẻ tài nguyên/dữ liệu.

## Phương án đã cân nhắc

Web-first phụ thuộc mạng/hạ tầng; native Qt/C++ tăng chi phí viết lại UI và dùng lại web. Chưa loại bỏ vĩnh viễn server.

## Hệ quả

Giảm dịch vụ phải cài; phải hỗ trợ nhiều cấu hình máy, vòng đời tiến trình, pack và offline resources.

## Bằng chứng và người chốt

G0 xác định động lực offline/dữ liệu local, số máy, OS và nhu cầu chia sẻ. G1/G3 chứng minh sidecar và máy sạch. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Khi nhiều người dùng cần dữ liệu chung hoặc yêu cầu tổ chức buộc server. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

