# Tài liệu làm việc cho AI và dev

Cơ sở: [đề xuất v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md) và [kiến trúc hệ thống](../kien_truc_he_thong.md). Bộ này cụ thể hóa thiết kế thành hợp đồng/task có thể kiểm tra; không kế thừa các đoạn lỗi của bản hợp nhất v2.1.

| File | Nội dung | Khi đọc |
| --- | --- | --- |
| [architecture.md](architecture.md) | Tiến trình, hướng import, luồng dữ liệu, repository và publish | Làm việc xuyên module |
| [contracts.md](contracts.md) + [Pydantic dự thảo](../../backend/geoai/contracts) | Ngữ nghĩa, validation/version; schema sinh và phạm vi đã kiểm ở SPEC-001 | Tạo/đổi dữ liệu trao đổi |
| [adr/README.md](adr/README.md) | ADR-001–011 với trạng thái và bằng chứng | Đề xuất lại/thay đổi quyết định |
| [domain-rules.md](domain-rules.md) | CRS, diện tích, QA/NoData, resample, VN-2000 | Raster/vector/địa lý |
| [aoi-policy.md](aoi-policy.md) | Vẽ AOI, import footprint/Shapefile, geometry và snapshot | G0/GIS/import |
| [landcover-taxonomy.md](landcover-taxonomy.md) | Bộ 7 lớp HLS, crosswalk WorldCover/JAXA, ignore và T=3 | Nhãn/model/evaluation |
| [acceptance-criteria.md](acceptance-criteria.md) | Ngưỡng chất lượng/coverage/diện tích/CRS/tài nguyên người dùng cung cấp và protocol còn mở | G0, evaluation, benchmark và nghiệm thu |
| [prithvi-profile.md](prithvi-profile.md) | HLS bands, normalization, T=1 spike/T=3 nghiệp vụ, decoder, gate và điểm dừng | ML/tiền xử lý |
| [ipc-protocol.md](ipc-protocol.md) | JSON-RPC/framing, attempt/fencing, stdout và lỗi | Worker/coordinator |
| [worker-resolver.md](worker-resolver.md) | Bootstrap/context, resolve ID và quyền đọc/ghi theo project/attempt | Worker, importer, storage và start params |
| [importer-resolver-security.md](importer-resolver-security.md) | Ca kiểm archive/path/reparse/VRT/network và candidate isolation | Import/provider/security acceptance |
| [physical-models.md](physical-models.md) | Phương pháp vật lý, dữ liệu, đơn vị, solver/uncertainty và G4 | Feature toán–vật lý |
| [roadmap.md](roadmap.md) | G0–G4, hiện trạng, bằng chứng và task tiếp theo | Đầu mỗi phiên |
| [task-tracker.md](task-tracker.md) | Trạng thái SPEC-000–009, checklist mốc con, dependency, việc chờ và lịch sử | Khi nhận việc và cập nhật tiến độ |
| [specs/README.md](specs/README.md) | Một file cho mỗi task, dependency và điều kiện hoàn tất | Khi nhận task |
| [development-guide.md](development-guide.md) | Cấu trúc file đích, thứ tự làm, đầu vào còn chờ và bàn giao | Chuẩn bị xây codebase |
| [testing-strategy.md](testing-strategy.md) | Ma trận yêu cầu–kiểm tra–bằng chứng, phân biệt kiểm tài liệu và runtime | Viết spec hoặc nghiệm thu |

**Trạng thái ngày 08/11/2026:** đã thực thi code SPEC-001 và phần API/UI foundation SPEC-003. [Bàn giao cuối](evidence/codegen-2026-11-08/handoff.md): 55 tests contracts, 14 integration, 2 architecture, 7 DOM và artifact/typecheck/frontend build đều pass; review độc lập không còn lỗi chặn. SPEC-003 native chưa hoàn tất, G0/G1 chưa đạt; không suy model/native acceptance từ schema hay Vite build. Lịch sử [SPEC-000](specs/000-documentation-baseline.md) và [báo cáo tài liệu](evidence/2026-11-08-documentation-review.md) giữ nguyên phạm vi kiểm cũ.

Bổ sung sau review ngày 08/11/2026: [SPEC-008](specs/008-training-evaluation-model-pack.md) tạo model pack nghiệp vụ; [SPEC-009](specs/009-importer-worker-resolver.md) đặc tả importer/resolver; [ADR-011](adr/ADR-011-local-execution-owner.md) đề xuất phạm vi execution owner. Đã kiểm phạm vi tài liệu theo [báo cáo riêng](evidence/2026-11-08-review-followup.md); các phần runtime/model vẫn chưa triển khai/nghiệm thu.

## Nguồn sự thật và cập nhật

- Yêu cầu trực tiếp của người dùng và quyết định đã xác nhận giữ ưu tiên. Bản tổng hợp v1.4 là cơ sở nội dung thiết kế; ADR/spec bổ sung phải nhất quán, nếu thay thiết kế phải cập nhật nguồn cùng lúc.
- Pydantic là nguồn trường/kiểu của schema dự thảo `0.1.0`. [Contracts](contracts.md) đặc tả ngữ nghĩa và giới hạn; [schema](../../schemas/contracts-v0.1.0.json) sinh bằng exporter SPEC-001, không sửa tay. OpenAPI/client TypeScript chỉ sinh từ routes có thật trong task API.
- ADR-001–008 giữ mã của sổ cũ; ADR-009 bổ sung IPC/attempt, ADR-010 bổ sung mô hình vật lý và ADR-011 cụ thể hóa quyền thực thi giữa instance/project. `Artchitect/docs/adr/` là đường đặt ADR theo yêu cầu mới, thay đường đề xuất `Artchitect/plans/adr/` trong tài liệu trước. Chỉ có yêu cầu Prithvi được ghi đã xác nhận; các lựa chọn kỹ thuật giữ trạng thái đề xuất/có điều kiện.
- Không nhân bản toàn bộ 17 tài liệu vào đây. Tài liệu ngắn dẫn tới phần chi tiết bằng liên kết; thay thiết kế phải rà cả [bộ plans](../plans/README.md) và kiến trúc.
- Không tự nâng gate vì đã viết tài liệu/schema. Dữ liệu thực, nhãn, checkpoint nghiệp vụ, coverage, ngưỡng và ngân sách còn phải có bằng chứng riêng.
