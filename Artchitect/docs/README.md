# Tài liệu GeoAI — mục lục và đường đọc

Cơ sở: [đề xuất v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md) và [kiến trúc hệ thống](../kien_truc_he_thong.md). Bộ này cụ thể hóa thiết kế thành hợp đồng/task có thể kiểm tra; không kế thừa các đoạn lỗi của bản hợp nhất v2.1.

## Bắt đầu một công việc

1. Đọc [roadmap](roadmap.md) để biết gate, phạm vi và bằng chứng hiện tại.
2. Mở [task tracker](task-tracker.md) để biết mốc, dependency và việc còn chờ; sau đó đọc [spec của task](specs/README.md).
3. Chọn tài liệu theo phần việc. Bàn giao phải cập nhật spec/tracker/roadmap liên quan và dẫn tới bằng chứng thực.

| Nhu cầu | Đường đọc |
| --- | --- |
| Hiểu toàn hệ thống và các quyết định | [Kiến trúc hệ thống](../kien_truc_he_thong.md) → [kiến trúc triển khai](architecture.md) → [chỉ mục ADR](adr/README.md) |
| Desktop Windows | [Sơ đồ Windows](platforms/windows/desktop-architecture-diagrams.md) → [SPEC-003](specs/003-desktop-shell.md) → [kiểm thử](guides/testing-strategy.md) |
| Desktop Ubuntu | [Nền tảng](platforms/README.md) → [ADR-012](adr/ADR-012-ubuntu-desktop.md) → [SPEC-010 + profile native/interface](specs/010-ubuntu-foundation.md) → [môi trường/đóng gói](platforms/ubuntu/ubuntu-development-and-packaging.md) → [UB-01–20](platforms/ubuntu/ubuntu-validation-matrix.md) |
| AI gen code Ubuntu từng bước | [Plan tổng Superpowers](superpowers/plans/2026-11-10-ubuntu-foundation.md) → catalog/handoff → một trong 5 plan phần A–E → task được giao; 26 task dự kiến, chưa thực thi |
| AOI, GIS, nhãn hoặc nghiệm thu | [Dữ liệu/nghiệp vụ](domain/README.md) → [quy tắc địa lý](domain-rules.md) → [SPEC-002](specs/002-g0-evidence.md) |
| Model hoặc training | [Prithvi profile](prithvi-profile.md) → [SPEC-005](specs/005-prithvi-spike.md) / [SPEC-008](specs/008-training-evaluation-model-pack.md) → [tiêu chí nghiệm thu](domain/acceptance-criteria.md) |
| Worker, job, import hoặc publish | [Hợp đồng](contracts.md) → [IPC](ipc-protocol.md) → [worker resolver](worker-resolver.md) → [bảo mật importer/resolver](importer-resolver-security.md) → SPEC-003/004/009 |
| Chuẩn bị, kiểm hoặc bàn giao | [Hướng dẫn](guides/README.md) → [thiếu sót](project/implementation-gaps.md) → [bằng chứng](evidence/README.md) |

## Các nhóm tài liệu

| Vị trí | Nội dung |
| --- | --- |
| [platforms/](platforms/README.md) | Sơ đồ Windows; kiến trúc, đóng gói và nghiệm thu Ubuntu |
| [domain/](domain/README.md) | AOI, bộ lớp lớp phủ, tiêu chí nghiệm thu HLS |
| [guides/](guides/README.md) | Hướng dẫn phát triển và chiến lược kiểm thử |
| [project/](project/implementation-gaps.md) | Thiếu sót và nguyên nhân cần theo dõi cùng tracker |
| [adr/](adr/README.md) | Các quyết định kiến trúc, trạng thái và điều kiện kiểm chứng |
| [specs/](specs/README.md) | Đặc tả task, dependency và acceptance |
| [evidence/](evidence/README.md) | Bằng chứng, kết quả và hồ sơ lịch sử theo đợt |

Các file nền được `AGENTS.md` chỉ định trực tiếp tiếp tục ở cấp `docs/`, gồm architecture, contracts, domain rules, Prithvi profile, IPC, resolver/security, physical models, roadmap và tracker. Những file cũ tại cấp này có tiêu đề **“đường dẫn tương thích”** chỉ dẫn đến tài liệu chính trong thư mục chủ đề; chúng giữ các anchor để hồ sơ và liên kết cũ vẫn tra cứu được. Chỉnh nội dung nghiệp vụ ở tài liệu chính, không chỉnh trong trang dẫn.

## Danh mục tài liệu

| File | Nội dung | Khi đọc |
| --- | --- | --- |
| [architecture.md](architecture.md) | Tiến trình, hướng import, luồng dữ liệu, repository và publish | Làm việc xuyên module |
| [contracts.md](contracts.md) + [Pydantic dự thảo](../../backend/geoai/contracts) | Ngữ nghĩa, validation/version; schema sinh và phạm vi đã kiểm ở SPEC-001 | Tạo/đổi dữ liệu trao đổi |
| [adr/README.md](adr/README.md) | ADR-001–012 với trạng thái và bằng chứng | Đề xuất lại/thay đổi quyết định |
| [ubuntu-desktop-architecture.md](platforms/ubuntu/ubuntu-desktop-architecture.md) | Kiến trúc Ubuntu 22.04/24.04 LTS, supervisor/owner, FD/I/O và publish | Thiết kế adapter Linux; chưa là runtime đã kiểm |
| [ubuntu-development-and-packaging.md](platforms/ubuntu/ubuntu-development-and-packaging.md) | Preflight, dependency, build ABI, `.deb`, offline và upgrade | Chuẩn bị executor/build; chưa có bộ cài Linux |
| [ubuntu-validation-matrix.md](platforms/ubuntu/ubuntu-validation-matrix.md) | UB-01–20, thứ tự task và bằng chứng hai LTS | Triển khai/kiểm Ubuntu và phân biệt Cloud với desktop |
| [domain-rules.md](domain-rules.md) | CRS, diện tích, QA/NoData, resample, VN-2000 | Raster/vector/địa lý |
| [aoi-policy.md](domain/aoi-policy.md) | Vẽ AOI, import footprint/Shapefile, geometry và snapshot | G0/GIS/import |
| [landcover-taxonomy.md](domain/landcover-taxonomy.md) | Bộ 7 lớp HLS, crosswalk WorldCover/JAXA, ignore và T=3 | Nhãn/model/evaluation |
| [acceptance-criteria.md](domain/acceptance-criteria.md) | Ngưỡng chất lượng/coverage/diện tích/CRS/tài nguyên người dùng cung cấp và protocol còn mở | G0, evaluation, benchmark và nghiệm thu |
| [prithvi-profile.md](prithvi-profile.md) | HLS bands, normalization, T=1 spike/T=3 nghiệp vụ, decoder, gate và điểm dừng | ML/tiền xử lý |
| [ipc-protocol.md](ipc-protocol.md) | JSON-RPC/framing, attempt/fencing, stdout và lỗi | Worker/coordinator |
| [worker-resolver.md](worker-resolver.md) | Bootstrap/context, resolve ID và quyền đọc/ghi theo project/attempt | Worker, importer, storage và start params |
| [importer-resolver-security.md](importer-resolver-security.md) | Ca kiểm archive/path/reparse/VRT/network và candidate isolation | Import/provider/security acceptance |
| [physical-models.md](physical-models.md) | Phương pháp vật lý, dữ liệu, đơn vị, solver/uncertainty và G4 | Feature toán–vật lý |
| [roadmap.md](roadmap.md) | G0–G4, hiện trạng, bằng chứng và task tiếp theo | Đầu mỗi phiên |
| [task-tracker.md](task-tracker.md) | Trạng thái SPEC-000–010, checklist mốc con, dependency, việc chờ và lịch sử | Khi nhận việc và cập nhật tiến độ |
| [specs/README.md](specs/README.md) | Một file cho mỗi task, dependency và điều kiện hoàn tất | Khi nhận task |
| [development-guide.md](guides/development-guide.md) | Cấu trúc file đích, thứ tự làm, đầu vào còn chờ và bàn giao | Chuẩn bị xây codebase |
| [testing-strategy.md](guides/testing-strategy.md) | Ma trận yêu cầu–kiểm tra–bằng chứng, phân biệt kiểm tài liệu và runtime | Viết spec hoặc nghiệm thu |

**Trạng thái ngày 08/11/2026:** đã thực thi code SPEC-001 và phần API/UI foundation SPEC-003. [Bàn giao cuối](evidence/codegen-2026-11-08/handoff.md): 55 tests contracts, 14 integration, 2 architecture, 7 DOM và artifact/typecheck/frontend build đều pass; review độc lập không còn lỗi chặn. SPEC-003 native chưa hoàn tất, G0/G1 chưa đạt; không suy model/native acceptance từ schema hay Vite build. Lịch sử [SPEC-000](specs/000-documentation-baseline.md) và [báo cáo tài liệu](evidence/2026-11-08-documentation-review.md) giữ nguyên phạm vi kiểm cũ.

Bổ sung sau review ngày 08/11/2026: [SPEC-008](specs/008-training-evaluation-model-pack.md) tạo model pack nghiệp vụ; [SPEC-009](specs/009-importer-worker-resolver.md) đặc tả importer/resolver; [ADR-011](adr/ADR-011-local-execution-owner.md) đề xuất phạm vi execution owner. Đã kiểm phạm vi tài liệu theo [báo cáo riêng](evidence/2026-11-08-review-followup.md); các phần runtime/model vẫn chưa triển khai/nghiệm thu.

## Nguồn sự thật và cập nhật

- Yêu cầu trực tiếp của người dùng và quyết định đã xác nhận giữ ưu tiên. Bản tổng hợp v1.4 là cơ sở nội dung thiết kế; ADR/spec bổ sung phải nhất quán, nếu thay thiết kế phải cập nhật nguồn cùng lúc.
- Pydantic là nguồn trường/kiểu của schema dự thảo `0.1.0`. [Contracts](contracts.md) đặc tả ngữ nghĩa và giới hạn; [schema](../../schemas/contracts-v0.1.0.json) sinh bằng exporter SPEC-001, không sửa tay. OpenAPI/client TypeScript chỉ sinh từ routes có thật trong task API.
- ADR-001–008 giữ mã của sổ cũ; ADR-009 bổ sung IPC/attempt, ADR-010 bổ sung mô hình vật lý, ADR-011 cụ thể hóa quyền thực thi giữa instance/project và ADR-012 đề xuất adapter Ubuntu. `Artchitect/docs/adr/` là đường đặt ADR theo yêu cầu mới, thay đường đề xuất `Artchitect/plans/adr/` trong tài liệu trước. Yêu cầu Prithvi và mục tiêu hỗ trợ Ubuntu 22.04/24.04 LTS đã được người dùng xác nhận; các lựa chọn kỹ thuật giữ trạng thái đề xuất/có điều kiện.
- Không nhân bản toàn bộ 17 tài liệu vào đây. Tài liệu ngắn dẫn tới phần chi tiết bằng liên kết; thay thiết kế phải rà cả [bộ plans](../plans/README.md) và kiến trúc.
- Không tự nâng gate vì đã viết tài liệu/schema. Dữ liệu thực, nhãn, checkpoint nghiệp vụ, coverage, ngưỡng và ngân sách còn phải có bằng chứng riêng.
