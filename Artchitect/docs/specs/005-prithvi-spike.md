# SPEC-005 — Spike kỹ thuật Prithvi G1

**Trạng thái:** chưa triển khai. **Mục tiêu:** kiểm chứng input/shape/CPU/export/runtime với backbone thật và decoder đúng kiến trúc, có thể ngẫu nhiên; nhãn tiếp tục chuẩn bị song song.

Input bắt buộc: HLS fixture thực đã QA/hash, hardware/budget và product/CRS profile G0 tương ứng, backbone revision, code kiến trúc/license và packaging environment. Đọc [Prithvi profile](../prithvi-profile.md), [domain rules](../domain-rules.md), ADR-004/008. Chưa đủ input thì chưa báo G1 pass.

Output dự kiến: adapter/preprocess trong `geoprocessing/`, `models/`, `compute/`; profile registry và scripts export/benchmark; manifest model kỹ thuật có seed/hash/readiness=technical; `Artchitect/docs/evidence/g1/` chứa tensor/ONNX checks, benchmark/pack report. Không đưa weights lớn vào Git.

Tạo product/catalog adapter tối thiểu để resolve fixture thực đã khóa danh tính, không cần marketplace/provider tổng quát. Chuẩn hóa band/QA thuộc products/geoprocessing, device/backend thuộc compute; không đặt preprocessing nghiệp vụ trong API/UI. Bàn giao hồ sơ theo [Prithvi profile](../prithvi-profile.md); [SPEC-007](007-g1-platform-validation.md) cung cấp phần GIS/viewer/PDF/bundle bổ sung của G1.

Input/model registry/allowlist được cấp theo SPEC-009; benchmark chạy trong execution owner ADR-011 và ghi tải nền/máy thực. Có thể sàng lọc 300M/100M/tiny trong ngân sách đã duyệt, không biến thứ tự benchmark thành yêu cầu cứng. Nhãn/recipe/checkpoint nghiệp vụ do [SPEC-008](008-training-evaluation-model-pack.md) phụ trách; decoder ngẫu nhiên ở đây không thay đầu ra training.

## Acceptance

[Tiêu chí nghiệm thu](../acceptance-criteria.md) bổ sung yêu cầu GPU/tài nguyên/điểm dừng được cung cấp; phạm vi máy thực và phép đo còn cần khóa trước benchmark. G1 chỉ đo kỹ thuật với checkpoint/decoder technical; không áp bảng F1 nghiệp vụ để tuyên bố decoder ngẫu nhiên đạt hoặc dùng SLA GPU thay CPU SLO.

- Đúng S30 band mapping/scale/mean/std, shape B×6×1×224×224, metadata policy/QA/padding/crop/GridSpec; sai band/GSD/T/metadata thiếu bị chặn.
- Encoder thật + UPerNet cùng kiến trúc dự kiến, decoder ngẫu nhiên được ghi rõ, không show business ready hoặc tính F1 như nghiệm thu.
- PyTorch FP32 reference; thử ONNX cả encoder/decoder, so output với tolerance kỹ thuật đặt trước tối ưu. Chưa export đúng có hồ sơ ngoại lệ, không loại Prithvi khỏi bản đầu.
- Đo cold/warm, I/O/preprocess/infer/postprocess, peak RAM/VRAM, đĩa tạm và UI. Dynamic INT8 nếu CPU bottleneck; kết quả chỉ sơ bộ cho đến checkpoint G2.
- Fixture CRS cắt 108°E, native pack/CPU/offline phù hợp; không dùng crop/scene giả để hứa workload tỉnh đã hoàn thành.

Test dự kiến: `tests/geoprocessing/test_hls_profile.py`, `tests/compute/test_prithvi_runtime.py`, benchmark CLI có manifest/seed/hardware/hash. Tách test nhẹ schema/QA khỏi chạy weights lớn/GPU. Báo cáo phải ghi số đo, tolerance, lỗi/operator và phạm vi chưa kiểm chứng; G2 chạy lại checkpoint nghiệp vụ.
