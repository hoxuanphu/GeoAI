# ADR-004: CPU chính thức, NVIDIA tùy chọn, ưu tiên ONNX

**Trạng thái:** Đề xuất có điều kiện runtime/benchmark G1–G2. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../prithvi-profile.md).

## Bối cảnh

Máy người dùng có thể không có GPU rời, nhưng feature Prithvi phải hữu ích trên workload CPU tối thiểu.

## Lựa chọn

Ưu tiên ONNX Runtime CPU/CUDA; PyTorch inference CPU/CUDA là ngoại lệ có hồ sơ. NVIDIA compute pack riêng, AMD AI hoãn.

## Phương án đã cân nhắc

PyTorch đầy đủ trong mọi pack làm nặng phân phối; CUDA bắt buộc loại nhiều máy; server fallback không tự thay yêu cầu local.

## Hệ quả

Probe operator/output rồi benchmark đầu-cuối; dynamic INT8 thử theo profiling, static cần calibration. Không tự fallback khi người dùng bắt GPU.

## Bằng chứng và người chốt

G0 chốt workload/hardware/SLO; G1 decoder kỹ thuật, G2 chạy lại checkpoint thật và mọi precision phân phối. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Khi model/operator không export đúng, runtime không có lợi hoặc phần cứng mục tiêu đổi. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

