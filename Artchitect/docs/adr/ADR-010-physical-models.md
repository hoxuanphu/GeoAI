# ADR-010: Mô hình toán–vật lý theo Domain Pack

**Trạng thái:** Đề xuất thiết kế; GEO-01 bản đầu, PHY chọn từng feature G4. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../physical-models.md).

## Bối cảnh

Người dùng yêu cầu bổ sung mô hình toán–vật lý; các đại lượng cần dữ liệu ngoài sáu band HLS và validation riêng.

## Lựa chọn

PhysicalModelSpec/parameter/forcing/biên/solver snapshot, dùng chung job/publish/review/report. PROSAIL, FAO-56, SEBAL, SCS-CN, HAND, nước nông 2D, RUSLE/allometry có profile/miền hiệu lực riêng.

## Phương án đã cân nhắc

Đưa mọi solver vào core ngay, suy mọi tham số từ ảnh, dùng HAND thay thủy lực hoặc coi mô phỏng là ground truth đều không đủ.

## Hệ quả

Analytics/solver adapter version/license; calibration/test, đơn vị và uncertainty có provenance. Solver liên kết chỉ native checkpoint khi hỗ trợ, không tile độc lập tùy ý.

## Bằng chứng và người chốt

GEO-01 G1/G2; mỗi PHY G4 có dữ liệu/hiệu chuẩn, gate tuyệt đối, miền/cân bằng/hội tụ, validation và ngân sách. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Khi chọn feature vật lý cụ thể, nguồn quan trắc/solver hoặc cách hiệu chuẩn đổi. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

