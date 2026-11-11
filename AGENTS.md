# Hướng dẫn làm việc trong GeoAI

Đầu phiên đọc [roadmap](Artchitect/docs/roadmap.md), sau đó đọc spec của task trong [Artchitect/docs/specs](Artchitect/docs/specs/README.md). Chỉ đánh dấu hoàn tất khi có bằng chứng kiểm tra; cập nhật trạng thái và đường dẫn bằng chứng trong roadmap/spec.

Theo dõi công việc tại [task tracker](Artchitect/docs/task-tracker.md); khi bàn giao cập nhật trạng thái/mốc con, việc còn chờ và liên kết bằng chứng, đồng bộ spec/roadmap liên quan.

| Khi làm việc | Phải đọc |
| --- | --- |
| Xuyên module, đổi kiến trúc | [Architecture](Artchitect/docs/architecture.md) và [ADR index](Artchitect/docs/adr/README.md) |
| Tạo/đổi dữ liệu trao đổi | [Contracts](Artchitect/docs/contracts.md), schema Pydantic trong `backend/geoai/contracts/` và test contracts |
| Raster, vector, CRS, diện tích | [Domain rules](Artchitect/docs/domain-rules.md) |
| Model, band/QA, tiền xử lý | [Prithvi profile](Artchitect/docs/prithvi-profile.md) |
| Worker, coordinator, cancel/retry | [IPC protocol](Artchitect/docs/ipc-protocol.md) |
| Nhiều instance/project, tài nguyên dùng chung | [ADR-011](Artchitect/docs/adr/ADR-011-local-execution-owner.md) và SPEC-003/004 |
| Import/provider, worker resolve/quyền đọc ghi | [Worker resolver](Artchitect/docs/worker-resolver.md), [security acceptance](Artchitect/docs/importer-resolver-security.md) và SPEC-009 |
| Dataset, training/evaluation/model pack | [SPEC-008](Artchitect/docs/specs/008-training-evaluation-model-pack.md) và Prithvi profile |
| Toán–vật lý, solver, hiệu chuẩn | [Physical models](Artchitect/docs/physical-models.md) và ADR-010 |

Nguồn thiết kế là [đề xuất tổng hợp v1.4](Artchitect/solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), được tổ chức lại trong [kiến trúc hệ thống](Artchitect/kien_truc_he_thong.md). `Artchitect/docs/` cụ thể hóa để triển khai; schema hiện tại là dự thảo `0.1.0`, chưa là API sản phẩm đã phát hành. Không dùng các đoạn mâu thuẫn của bản chuyên gia v2.1 để thay yêu cầu đã xác nhận. Quyết định có trạng thái đề xuất/có điều kiện chưa đồng nghĩa đã nghiệm thu.

- Prithvi-EO-2.0 + decoder nghiệp vụ bắt buộc từ bản đầu; RF/boosting là đối chứng, nghiệm thu theo ngưỡng tuyệt đối.
- G0 chưa hoàn tất thì chỉ thực hiện task được ghi rõ có thể chạy trước gate; không tự đặt nhãn, AOI, ngưỡng chất lượng hoặc ngân sách thành thông số đã được chủ nghiệp vụ duyệt.
- Worker chỉ gửi event/candidate; coordinator duy nhất ghi trạng thái và kiểm token attempt khi công bố. Không dùng idempotency thay fencing.
- Schema Pydantic là nguồn kiểu trao đổi; JSON Schema/client sinh ra, không sửa tay. Thay schema phải sửa docs, fixture và test liên quan trong cùng task.
- Giữ nguyên dữ liệu và thay đổi không thuộc task. Không đưa credential, signed URL, dữ liệu khách hàng hoặc trọng số lớn vào Git/log/snapshot.
- Sửa quyết định đã chấp thuận bằng ADR thay thế có liên kết; cập nhật tài liệu nguồn bị ảnh hưởng. Hồ sơ ADR chính thức đặt trong `Artchitect/docs/adr/` theo yêu cầu người dùng.
- Kiểm tra hiện có: `$env:PYTHONPATH = 'backend'; python -m unittest discover -s tests/contracts -v`.
- Hiện chưa có runtime desktop/GIS/AI/solver; pass test schema không chứng minh model, installer hoặc CRS đã chạy đúng.
- Không tự ý tạo nhánh mới, push code, ghi commit khi chưa có lệnh.