# ADR-008: Prithvi-EO-2.0 dùng cho phân tích ngay bản đầu

**Trạng thái:** Yêu cầu sản phẩm đã được người dùng xác nhận; cấu hình kỹ thuật chưa nghiệm thu. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../prithvi-profile.md).

## Bối cảnh

Yêu cầu Prithvi từ bản đầu độc lập với việc model có thắng RF hay không.

## Lựa chọn

Feature đầu phải có Prithvi + decoder nghiệp vụ thực chạy trên dữ liệu phù hợp. Khởi đầu 300M-TL/UPerNet/HLS, ứng viên nhỏ/non-TL kiểm riêng. Gate tuyệt đối, RF đối chứng.

## Phương án đã cân nhắc

Chỉ backbone/reconstruction/demo menu, S1-only hoặc RF thay toàn bộ không đáp ứng yêu cầu. Không bắt buộc thắng RF để nghiệm thu.

## Hệ quả

Cần nhãn/split/checkpoint thật, CPU workload, evaluation và pack; G1 decoder ngẫu nhiên chỉ khảo sát kỹ thuật. Có ngân sách và điểm dừng.

## Bằng chứng và người chốt

G0 chốt feature/nhãn/gate/ngân sách; G2 đạt ngưỡng tuyệt đối/coverage/tài nguyên và chạy lại mọi runtime/precision. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Thay yêu cầu phải do chủ dự án xác nhận, ghi ADR thay thế và cập nhật nguồn, không tự hạ gate. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

