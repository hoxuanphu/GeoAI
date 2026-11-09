# ADR-009: JSON-RPC local và fencing theo attempt

**Trạng thái:** Đề xuất thiết kế; wire draft 0.1.0, chưa có transport. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../ipc-protocol.md).

## Bối cảnh

Worker native có thể crash/log bẩn/stdout treo; retry có thể để worker cũ trả candidate sau attempt mới.

## Lựa chọn

JSON-RPC 2.0 UTF-8/LF, request ID và protocol/schema version rõ; chỉ tham chiếu dữ liệu. Coordinator duy nhất publish, kiểm generation token và state trong transaction. Không có HTTP header trong framing stdin/stdout này.

## Phương án đã cân nhắc

Tensor JSON, queue từng pixel, idempotency thay fencing hoặc stdout log lẫn protocol đều không đáp ứng hợp đồng. Transport nhiều máy dành adapter server.

## Hệ quả

Cần reader/writer riêng, native stdout redirection Windows, bounded buffers, cancel/heartbeat không bị inference chặn. Job Object không tự checkpoint.

## Bằng chứng và người chốt

Contract tests kiểm envelope; SPEC-004/G1 kiểm framing partial/oversized/native logging, cancel/retry/crash và từ chối stale attempt. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Khi sang nhiều máy hoặc transport không đạt yêu cầu đo được. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

