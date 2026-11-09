# Bàn giao tài liệu để xây codebase

**Đã được yêu cầu triển khai code ngày 08/11/2026.** Thực thi theo thứ tự và dependency bên dưới; trạng thái/bằng chứng thực nằm ở roadmap/spec/tracker. Bắt đầu mỗi phiên bằng [roadmap](roadmap.md), sau đó chọn [spec](specs/README.md), không dùng cây thư mục như danh sách việc đã hoàn tất.

## Bộ tài liệu cần đọc

| Công việc | Đọc trước | Kết quả cần thống nhất |
| --- | --- | --- |
| Nhận dự án | [AGENTS](../../AGENTS.md), roadmap, spec của task | Phạm vi, gate hiện tại, dependency và bằng chứng còn thiếu |
| Ghép module/tiến trình | [Architecture](architecture.md), [ADR](adr/README.md) | Import được phép, coordinator/worker, chủ sở hữu ghi dữ liệu |
| Trao đổi dữ liệu | [Contracts](contracts.md), mã Pydantic đang có | Trường/đơn vị/version, validation payload và kiểm liên record |
| GIS và model | [Domain rules](domain-rules.md), [Prithvi profile](prithvi-profile.md) | CRS/grid, band/QA, checkpoint, tensor và ngưỡng được duyệt |
| Điều phối | [IPC](ipc-protocol.md), [job nguồn](../plans/08_job_tai_nguyen_va_phuc_hoi.md) | Framing, fencing, cancel/retry, publish/recovery |
| Thực thi nhiều instance/project | [ADR-011](adr/ADR-011-local-execution-owner.md), SPEC-003/004 | Execution owner liên session/process khác khóa writer và dependency pin |
| Import và worker resolve | [Worker resolver](worker-resolver.md), [security acceptance](importer-resolver-security.md), SPEC-009 | Context ID/hash, read allowlist, staging/candidate isolation |
| Tạo model nghiệp vụ | [SPEC-008](specs/008-training-evaluation-model-pack.md) | Ai tạo dataset/split/recipe/checkpoint/evaluation/pack cho SPEC-006 |
| Vật lý | [Physical models](physical-models.md), ADR-010 | Dữ liệu/đơn vị/miền hiệu lực, calibration/solver/uncertainty |
| Bàn giao | [Testing strategy](testing-strategy.md) | Lệnh đã chạy, artifact/log, người duyệt và giới hạn |

## File hiện có và cấu trúc đích

Đã có: contracts common/geography/models/runs/rpc/access/API DTOs, public/private registries, schema và OpenAPI/TypeScript client sinh; FastAPI session/metadata routes, dev pipe bootstrap, React/Vite UI và scaffold Tauri trả lỗi chưa hỗ trợ. Test/fixture và [bằng chứng](evidence/codegen-2026-11-08/progress.md) ghi phạm vi thực. Native launcher/owner/Job Object, resolver/importer/provider, database/job, GIS/AI/solver và installer chưa được triển khai/nghiệm thu. Không dùng file scaffold làm bằng chứng runtime.

```text
apps/desktop/                    # SPEC-003: Tauri/React và adapter viewer
  src/                           # state UI, gọi client sinh ra, không suy luận AI
  src-tauri/                     # launcher, handoff token, Windows Job Object
backend/geoai/
  contracts/                     # SPEC-001/009: Pydantic, access context, public exports
  bootstrap.py                   # SPEC-003/004: ghép adapter và registry tĩnh
  api/                           # SPEC-003: routes/session/SSE/asset authorization
  storage/                       # SPEC-004/009: repository, artifact/lease, importer/resolver
  jobs/                          # SPEC-004: coordinator/protocol/publisher
  workers/                       # SPEC-004/009: bootstrap handle/context và handler
  products/                      # SPEC-005: HLS/product/QA profile
  catalog/                       # SPEC-005/006/009: provider/resolve/materialize có policy
  geoprocessing/                  # SPEC-005/007: QA, grid, CRS, window, area
  models/                        # SPEC-005: kiểm ModelSpec/pack/compatibility
  compute/                       # SPEC-005: runtime CPU/CUDA và budget
  analytics/                     # SPEC-006: GEO-01; adapter PHY chỉ khi chọn G4
  workflows/                     # SPEC-006: chuỗi bước lớp phủ có version
  domains/                       # SPEC-006: đăng ký feature/gate, không sao chép I/O
  review/                        # SPEC-006: revision/representation/review
  reports/                       # SPEC-006/007: snapshot/map/Typst
  viewer/                        # SPEC-007: asset/Range/tile serving
migrations/                      # SPEC-004: Alembic, revision DB độc lập schema DTO
tools/                           # SPEC-001/005: exporter/benchmark có manifest
schemas/                         # SPEC-001: artifact sinh từ Pydantic
tests/                           # theo spec; hiện chỉ có contracts và fixture JSON
Artchitect/docs/evidence/         # báo cáo kiểm tra đã thực hiện, không phải dữ liệu gốc
```

Tạo package khi có task sử dụng; `products` có thể là `catalog.products` nếu giữ ranh giới import. Không tạo đủ folder rỗng, plugin loader hay DAG engine chỉ để khớp sơ đồ. Model/ảnh/nhãn lớn ở kho dữ liệu được kiểm soát; Git chỉ giữ manifest đã lọc, fixture nhỏ được phép và test.

## Thứ tự triển khai khi được yêu cầu code

| Bước | Công việc và điểm dừng review | Có thể trước G0? |
| --- | --- | --- |
| 1 | SPEC-001: kiểm kiểu nền/fixture/exporter cho các module đầu; phần start/access context nghiệm thu cùng SPEC-009 rồi chạy lại toàn suite/schema check | Có, bản dự thảo; không dùng thứ tự nghiệm thu toàn task để tạo vòng dependency |
| 2 | SPEC-002: khóa feature/AOI/provider/class schema/split/CRS/gate/hardware/ngân sách và người quyết định | Là công việc để đóng G0 |
| 3 | SPEC-003: shell/API/owner lock; SPEC-009: bootstrap/importer/resolver; SPEC-004: job/IPC/publish/SQLite/recovery tích hợp | Có, fixture kỹ thuật và giới hạn rõ; ca live cần provider policy/quyền |
| 4 | SPEC-005: HLS thực → Prithvi backbone thật + decoder kỹ thuật → export/CPU; nhãn vẫn chuẩn bị song song | Chỉ khi có đủ đầu vào G0 tương ứng |
| 5 | SPEC-007: kiểm nền tảng GIS/viewer/PDF/bundle/security, tổng hợp bằng chứng G1 | Ca kỹ thuật tổng hợp có thể chạy trước; chưa chốt tolerance/support matrix thay chủ nghiệp vụ |
| 6 | SPEC-008: dataset/split/recipe/training/evaluation/model pack, chuẩn bị song song bước 2–5 khi đủ input; SPEC-006 nhận pack để tích hợp G2 | Training/promotion cần profile/nhãn/budget được chốt; SPEC-006 cần G0 và các phần G1 phụ thuộc đạt |
| 7 | Lập spec G3 từ support matrix đã đo: máy sạch/offline/installer/upgrade/restore; G4 chọn từng PHY/provider/server | Chờ dữ liệu và nhu cầu tương ứng |

Không có lịch triển khai cam kết trước G0/G1. Một spec pass chỉ đóng tiêu chí của spec; người phụ trách gate đối chiếu đủ [ma trận bằng chứng](testing-strategy.md) rồi mới kết luận gate đạt.

Checkout và môi trường training của SPEC-008 được ghi riêng trước khi chạy, có thể cùng hoặc khác repository; chưa thêm thư mục training rỗng vào desktop. Runtime chỉ nhận model pack có provenance và được kiểm, không phân phối optimizer/notebook/training dependencies. Vai trò tạo/kiểm/chốt từng đầu ra ở SPEC-008; SPEC-002 ghi người thực khi có phân công.

## Đầu vào phải xin quyết định, không tự suy

| Đầu vào chưa có | Ai cần xác nhận | Phần bị chặn |
| --- | --- | --- |
| Feature đầu, AOI, bộ lớp và mục đích sử dụng | Chủ nghiệp vụ, GIS | G0, dataset/evaluation và nghiệp vụ G2 |
| Quyền đọc HLS, QA/coverage 2–3 năm, license dữ liệu | GIS/data | Chốt chiến lược ảnh và spike trên dữ liệu thực |
| Nhãn/split không gian–thời gian và người duyệt | Chủ nghiệp vụ, ML/data | Training/checkpoint và test độc lập G2 |
| CRS/VN-2000, điểm khống chế, tolerance và datum đứng | GIS/đơn vị dữ liệu | Chứng minh độ chính xác GIS, không dùng round-trip thay thế |
| Ngưỡng tuyệt đối theo lớp, coverage, CPU SLO và ngân sách/điểm dừng | Chủ nghiệp vụ, chủ dự án | Pass/fail nghiệp vụ, lựa chọn model/runtime cuối |
| Máy CPU/NVIDIA/OS/driver, workload và tài nguyên khả dụng | Kỹ thuật, chủ dự án | Benchmark, support matrix và pack phát hành |
| Dữ liệu/solver/hiệu chuẩn cho một PHY cụ thể | Chuyên gia ngành, chủ nghiệp vụ | Feature vật lý G4; không chặn GEO-01 bản đầu |

Đây là các quyết định còn mở, không phải chỗ trống cho dev điền giá trị tùy ý. Fixture tổng hợp phục vụ kiểm cấu trúc/cơ chế; không thay hồ sơ G0 hoặc golden output nghiệp vụ.

## Quy trình bàn giao một task

1. Ghi mục tiêu, file sẽ thay, interface và phần ngoài phạm vi vào spec. Đọc ADR liên quan; thay quyết định đã chấp thuận phải có ADR thay thế.
2. Khi triển khai được yêu cầu, kiểm trạng thái workspace, giữ thay đổi khác, dựng môi trường riêng và khóa dependency từ resolve thực. Chưa có lockfile GIS/AI đã kiểm chứng để sao chép.
3. Kiểm tra các ca bắt buộc của spec bằng đúng loại bằng chứng; schema test, GIS fixture, process test và evaluation ML có giá trị khác nhau.
4. Lưu lệnh/môi trường/kết quả/hash/log đã lọc, giới hạn và việc còn chờ; cập nhật roadmap/spec cùng đường dẫn bằng chứng. Không gắn nhãn hoàn tất cho test chưa chạy hoặc dependency mới chỉ có file.

Nếu phát hiện tài liệu và mã khác nhau, ghi rõ sai khác trong SPEC-001; đồng bộ Pydantic, fixture, schema/client sinh ra, docs và test trong cùng task. Báo cáo tài liệu lịch sử giữ nguyên phạm vi/lệnh đã chạy lúc đó, không sửa thành bằng chứng runtime mới.
