# Roadmap và trạng thái hiện tại

**Giai đoạn hiện tại: chuẩn bị G0; G0 chưa hoàn tất.** Ngày ghi nhận: 08/11/2026. Cơ sở [G0–G4 v1.4](../plans/15_lo_trinh_va_cong_nghiem_thu.md). File này phải được đọc đầu phiên và cập nhật bằng bằng chứng, không suy gate đạt từ số lượng tài liệu.

**Phạm vi công việc hiện tại:** ngày 08/11/2026 người dùng yêu cầu thực thi kế hoạch gen code bằng Superpowers theo bộ docs, thay cho phạm vi chỉ tài liệu trước đó. Bắt đầu SPEC-001, sau đó SPEC-003 → SPEC-009 → SPEC-004 theo dependency; chỉ triển khai phần được phép trước G0. [Nhật ký triển khai](evidence/codegen-2026-11-08/progress.md) lưu baseline, rulings và việc còn chờ. G0 chưa đạt; yêu cầu code không thay quyết định nghiệp vụ/GIS/ML còn thiếu.

**Tổ chức tài liệu:** ngày 08/11/2026, chuyển toàn bộ thư mục tài liệu từ root vào `Artchitect/docs/` theo yêu cầu người dùng; đã cập nhật hướng dẫn và liên kết theo vị trí mới. Bằng chứng kiểm sau di chuyển được bổ sung vào báo cáo của SPEC-000.

**Sắp xếp theo chủ đề 10/11/2026:** theo yêu cầu người dùng, đã hoàn tất phạm vi tổ chức tài liệu vào `platforms/`, `domain/`, `guides/` và `project/`; xem [mục lục](README.md), [báo cáo kiểm](evidence/docs-organization-2026-11-10/review.md) và [kết quả](evidence/docs-organization-2026-11-10/results.json). Các đường dẫn bắt buộc trong AGENTS và trang tương thích cho liên kết cũ được giữ; không đổi trạng thái gate/runtime. Mốc tài liệu SPEC-000/000.6 đã được kiểm.

**Bàn giao code 08/11/2026:** [báo cáo cuối](evidence/codegen-2026-11-08/handoff.md) ghi 55 tests contracts + 14 integration + 2 architecture + 7 DOM đều pass, schema/client current, typecheck/Vite build pass và review độc lập không còn finding chặn. Chỉ hoàn tất SPEC-001 draft và phần nền độc lập của SPEC-003; native launcher/owner/Job Object/WebView2 cùng các gate vẫn chưa đạt.

Theo dõi trạng thái từng SPEC, mốc con, dependency, việc còn chờ và lịch sử tại [task tracker](task-tracker.md). Cập nhật tracker/spec khi bàn giao; roadmap giữ trạng thái gate và phạm vi tổng thể.

**Đợt làm tiếp:** người dùng yêu cầu ghi rõ [thiếu sót/nguyên nhân](project/implementation-gaps.md) và hoàn thiện trước phần có thể. Thực thi [backend trước G0](evidence/backend-pre-g0-2026-11-08/plan.md) bằng fixture; thiếu native không chặn policy/context/framing/job core thuần. Các điều kiện nghiệm thu native/DB/live/model vẫn giữ nguyên.

**Bàn giao tiếp nối 09/11/2026:** [báo cáo](evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md)
ghi IPC/core, SQLAlchemy/Alembic source, Windows owner/Job Object/I/O,
worker transport và process→staging→publisher fixture. [Kiểm tổng thể](evidence/backend-pre-g0-2026-11-08/final-results.json):
192 Python tests pass, 25 DB tests skip; 7 DOM/typecheck/frontend build/schema/client checks pass.
Không cài thêm dependency. Rust/Tauri chưa build; SPEC-003/004/009 vẫn partial,
G0/G1/G2 chưa đạt và capability thực thi vẫn tắt.

## Yêu cầu Ubuntu LTS và kiểm thử Cloud 10/11/2026

**Yêu cầu tiếp nối hiện tại:** đã hoàn tất lập plan triển khai thật kỹ bằng Superpowers để AI gen code từng bước. [Plan tổng](superpowers/plans/2026-11-10-ubuntu-foundation.md), 5 plan phần A–E và catalog/handoff chia 26 task/133 bước; [hồ sơ kiểm plan](evidence/ubuntu-plan-2026-11-10/review.md) đóng mốc tài liệu SPEC-000/000.8. Phiên này chỉ lập/kiểm plan; A-01–E-05 và 010.1–010.3 chưa thực thi.

Yêu cầu trước đó là hoàn thiện spec trước khi gen code Ubuntu. [SPEC-010](specs/010-ubuntu-foundation.md), [native profile](platforms/ubuntu/ubuntu-native-profile.md) và [interface adapter](platforms/ubuntu/ubuntu-adapter-interfaces.md) đã hoàn tất rà soát/kiểm tài liệu, cụ thể hóa namespace, FD/handshake, owner journal/recovery, adapter và fixture. [Báo cáo spec](evidence/spec010-2026-11-10/review.md) đóng mốc tài liệu SPEC-000/000.7; 010.1–010.3 chưa triển khai và không mở scope code từ lịch sử yêu cầu cũ.

Ghi nhận mục tiêu hỗ trợ Linux gồm **Ubuntu 22.04 LTS và Ubuntu 24.04 LTS**, bên cạnh Windows, theo yêu cầu người dùng. [Đánh giá khả thi ban đầu](evidence/2026-11-10-linux-support-assessment.md) là hồ sơ tiếp nhận. Đã hoàn tất phạm vi tài liệu bổ sung [ADR-012](adr/ADR-012-ubuntu-desktop.md), [kiến trúc/sơ đồ Ubuntu](platforms/ubuntu/ubuntu-desktop-architecture.md), [môi trường/đóng gói](platforms/ubuntu/ubuntu-development-and-packaging.md) và [ma trận UB-01–20](platforms/ubuntu/ubuntu-validation-matrix.md); đồng bộ SPEC-003/004/009, kiến trúc và nguồn/plans. [Bằng chứng kiểm tài liệu](evidence/ubuntu-2026-11-10/review.md) và [kết quả](evidence/ubuntu-2026-11-10/results.json) đóng mốc SPEC-000/000.5; không đóng gate runtime. Các primitive kỹ thuật còn đề xuất; chưa triển khai Linux hoặc chạy kiểm Cloud. Còn review/chốt thiết kế, executor/dependency lock và bằng chứng trên hai LTS.

## Vẽ lại kiến trúc desktop 09/11/2026

Đã bổ sung [bộ sơ đồ chi tiết](platforms/windows/desktop-architecture-diagrams.md) theo lựa chọn Windows desktop của người dùng: tiến trình/module, execution owner, pipeline Prithvi, fencing/publish, provenance/storage và training ngoài runtime. [Bằng chứng kiểm cấu trúc tài liệu](specs/000-documentation-baseline.md#vẽ-lại-kiến-trúc-desktop-ngày-09112026) ghi 8 diagram, link/fence/UTF-8 hợp lệ; chưa parse/render Mermaid tự động. Không thay quyết định ADR, implementation hoặc trạng thái G0–G4.

## Khắc phục môi trường 09/11/2026

[Bằng chứng kiểm](evidence/environment-2026-11-09/results.json): đã lưu `NODE_USE_SYSTEM_CA=1` ở user, npm ping/restore và 7 DOM tests/typecheck/frontend build pass; 57 contracts tests pass bằng Python/package có sẵn. Rustup và Tauri native binding tải GET bị HTTP 403; Python wheel bị `MediaTypeBlocked`; Build Tools hai lần dừng 1602 ở bước elevation/UAC. `.venv-clean` cô lập đã tạo nhưng chưa cài đủ dependency. Chưa khắc phục xong native/clean Python; cần phê duyệt mạng và cài Build Tools tương tác có quyền quản trị. Không tắt TLS hoặc đổi gate; SPEC-003 vẫn partial.

## Hiện trạng

- Đã có đề xuất v1.4, kiến trúc hệ thống và bộ plans; bộ docs này tổ chức cách đọc cho AI/dev.
- Đã hoàn thiện Pydantic 0.1.0 trong phạm vi SPEC-001: run/RPC/private context, public registries, exporter và schema sinh. 51 test nền qua và review độc lập không có lỗi chặn; sau DTO API SPEC-003 đã chạy lại 55 tests/schema/client đều pass ở [bàn giao cuối](evidence/codegen-2026-11-08/handoff.md).
- Đã có FastAPI metadata/session và UI shell; Windows owner/Job Object/I/O có source và tests fixture thật. Rust/Tauri launcher, SQLAlchemy repository/migration và publisher đã có source, còn kiểm phụ thuộc môi trường/tích hợp. Chưa có GIS/AI/solver nghiệp vụ, model pack hay installer đã nghiệm thu; [tiến độ backend](evidence/backend-pre-g0-2026-11-08/progress.md) phân biệt source/pass/skip.
- Chưa có AOI/dataset/nhãn thực đã khóa, khảo sát coverage, CRS/operation/điểm chuẩn và protocol nghiệm thu hoàn chỉnh. Đã có giá trị ngưỡng định lượng do người dùng cung cấp; còn lựa chọn/phạm vi đo, CPU SLO và budget thử nghiệm thực cần khóa.
- Đã xác nhận [quyết định G0 từng phần](evidence/g0/decision-record.md): chia đợt, HLS 30 m + lớp phủ/chỉ số/thống kê/PDF trước; sau đó rừng/mất rừng, đất ngập nước/ngập lụt và profile 10/5/1 m. Nguồn mở/miễn phí trước; ảnh thương mại khi có quyền/ngân sách. Mục tiêu máy ít nhất 20 GB RAM/8 GB VRAM còn chờ máy tham chiếu và benchmark. [Kiểm tài liệu đợt ghi nhận](evidence/2026-11-08-g0-intake-review.md) chỉ xác minh tài liệu, không đóng G0.
- Bốn chỉ số đầu đã được chọn: NDVI, EVI, NDMI, MNDWI; chỉ tiêu đất/cây trồng định lượng chuyên sâu bổ sung sau. Chưa chốt policy/QA/tolerance hoặc ngưỡng diễn giải từ các chỉ số.
- Đã chốt cách tạo [AOI](domain/aoi-policy.md): vẽ trên bản đồ, dùng footprint ảnh vệ tinh import hoặc import Shapefile; đã cung cấp [bảy lớp IDs 0–6](domain/landcover-taxonomy.md) với `-1` ignore và dấu hiệu T=3. T=1 giữ cho spike kỹ thuật. Chưa có AOI kiểm định/thời gian, QC/crosswalk/nhãn độc lập hoặc model T=3 đã chạy; [bằng chứng đồng bộ tài liệu](evidence/2026-11-08-aoi-taxonomy-review.md) không đóng G0.
- Đã cụ thể hóa [nhóm 3/4 SPEC-002](specs/002-g0-evidence.md#nhóm-3--nguồn-ảnh-và-đóng-gói-input-x): cặp ảnh/nhãn X–Y, ba loại nguồn nhãn và kiểm thời gian/lưới/ignore/split trước chipping. [Đối chiếu tài liệu](evidence/2026-11-08-input-label-review.md) chưa thay thử đọc nguồn thực, QC/split có duyệt hoặc bằng chứng đóng G0.
- Đã ghi [bộ tiêu chí định lượng](domain/acceptance-criteria.md) theo nội dung người dùng: bảy lớp/macro/OA, coverage, diện tích/CI/CRS và tài nguyên/điểm dừng. Máy GPU 16–24 GB VRAM/RAM 32 GB/SSD 500 GB dùng riêng cho training/benchmark; desktop giữ mục tiêu ít nhất 20 GB RAM/8 GB VRAM (G0-D10). [Đối chiếu kỹ thuật](evidence/2026-11-08-acceptance-review.md) giữ protocol/máy thực/CI/budget chưa rõ ở trạng thái mở; chưa có model, coverage hay benchmark đạt ngưỡng, G0 vẫn chưa hoàn tất.

## Gates

| Gate | Điều kiện | Trạng thái |
| --- | --- | --- |
| G0 | Một feature/AOI/lớp/nhãn/split; provider HLS đã đọc được band/QA; khảo sát 2–3 năm theo ngày/tháng; CRS/VN-2000; ngưỡng tuyệt đối/coverage, hardware/workload/thời gian/RAM và ngân sách/số vòng/điểm dừng có người chốt | Chưa đạt, đầu vào ở SPEC-002 |
| G1 | Backbone thật + decoder đúng kiến trúc có thể ngẫu nhiên; shape/export/runtime/CPU/NVIDIA; fixture kỹ thuật; CRS/UTM, IPC/native log, Job Object, viewer/PDF/bundle/security và SQLite/migration | Chưa đạt; contracts metadata đã kiểm, còn runtime/native/model/GIS và các phần khác |
| G2 | Checkpoint nghiệp vụ + test độc lập; HLS→Prithvi→review→metrics→PDF; baseline RF đối chứng; gate tuyệt đối/coverage/tài nguyên và golden output nghiệp vụ | Chưa bắt đầu |
| G3 | Máy sạch/offline, pack/installer, backup/restore/upgrade, pin/retention, log/chẩn đoán và support matrix | Chưa bắt đầu |
| G4 | Chọn từng feature PHY/provider/model hoặc server; data/calibration/uncertainty/solver/license và gate riêng | Chưa bắt đầu |

## Thứ tự task và việc được làm trước gate

| Task | Dependency | Có thể làm khi G0 chưa đóng? | Trạng thái |
| --- | --- | --- | --- |
| [SPEC-000 Tài liệu](specs/000-documentation-baseline.md) | Thiết kế v1.4 và cấu trúc docs người dùng chọn | Có | Hoàn tất phạm vi tài liệu; [bằng chứng 08/11/2026](evidence/2026-11-08-documentation-review.md); không đóng gate runtime |
| [SPEC-001 Contracts](specs/001-contracts-baseline.md) | Thiết kế v1.4 và ngữ nghĩa contracts | Có, schema dự thảo | Hoàn tất phạm vi schema dự thảo; [51 tests/exporter](evidence/codegen-2026-11-08/task-1-report.md) và [review](evidence/codegen-2026-11-08/task-2-review-report.md); runtime context chờ SPEC-009 |
| [SPEC-002 Đầu vào G0](specs/002-g0-evidence.md) | Chủ nghiệp vụ/data/ML cung cấp đầu vào | Đây là công việc đóng G0 | Đã chốt phạm vi/thứ tự/chính sách nguồn, cách tạo AOI và bộ bảy lớp; chờ AOI kiểm định, QC/nhãn/dữ liệu và các quyết định còn thiếu |
| [SPEC-003 Desktop shell](specs/003-desktop-shell.md) | Contracts và ranh giới bảo mật | Có, skeleton/test máy dev; chưa chốt support matrix | API/UI và ctypes Windows owner/Job Object có kiểm; Rust launcher source chưa build, còn WebView2/xuyên session/support matrix; [Task 7](evidence/backend-pre-g0-2026-11-08/task-7-report.md) |
| [SPEC-004 Job/publish](specs/004-jobs-and-publish.md) | Kiểu nền contracts và launcher SPEC-003; nghiệm thu tích hợp resolver SPEC-009 | Có, bằng fixture tổng hợp, không nghiệm thu model | IPC/core/worker/publisher có kiểm fixture; repository/migration/backup/GC có source, tests DB còn skip; [bàn giao](evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md), chưa nghiệm thu toàn SPEC |
| [SPEC-009 Importer/resolver](specs/009-importer-worker-resolver.md) | Kiểu nền SPEC-001, launcher SPEC-003; tích hợp với SPEC-004, không vòng dependency | Có, ca tổng hợp/offline; live provider cần quyền/policy G0 | Policy/grants/native I/O/extraction/bootstrap có kiểm fixture; còn DB/provider/driver và toàn bộ IMP/NET/RES acceptance; [bàn giao](evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md) |
| [SPEC-010 Ubuntu foundation](specs/010-ubuntu-foundation.md) | Kiểu SPEC-001, phần nền SPEC-003/004/009, executor/dependency tương ứng | Có, phần nền/fixture đủ dependency; dữ liệu/model/business giữ gate riêng | Đặc tả/profile/interface hoàn tất kiểm; code 010.1–010.3 chưa bắt đầu, không đóng gate từ spec |
| [SPEC-005 Prithvi spike](specs/005-prithvi-spike.md) | Profile/input fixture thực và hardware/budget G0 tương ứng; job/bundle đủ dùng | Chỉ khi đã có các đầu vào phụ thuộc được chốt | Chưa thực hiện |
| [SPEC-007 Nền tảng G1](specs/007-g1-platform-validation.md) | SPEC-001/003/004 và fixture; SPEC-005 khi kiểm cùng AI | Có thể chuẩn bị/kiểm cơ chế tổng hợp; chờ CRS/tolerance/hardware được chốt để nghiệm thu | Mới có đặc tả; chưa thực hiện |
| [SPEC-008 Training/model pack](specs/008-training-evaluation-model-pack.md) | G0/profile/ngân sách tương ứng; nhãn/split; SPEC-005 giúp chọn runtime/profile, promotion chạy lại G2 | Có thể chuẩn bị nhãn/recipe; training/promotion chờ đầu vào được chốt | Mới có đặc tả; chưa dataset/checkpoint/evaluation thật |
| [SPEC-006 Luồng nghiệp vụ](specs/006-landcover-workflow.md) | G0 đóng, G1 phù hợp gồm phần resolver SPEC-009, model pack/nhãn/test từ SPEC-008 | Không nghiệm thu G2 bằng prototype | Chưa thực hiện |

## Quy tắc cập nhật

Task hoàn tất phải ghi lệnh kiểm tra, kết quả, ngày và artifact/log có thể xem; kiểm tra local và benchmark nghiệp vụ là bằng chứng khác nhau. SPEC-001 hoàn tất không làm G0/G1 đạt. Cập nhật trạng thái task sau mỗi bàn giao; ghi giới hạn và việc còn chờ, không tự chuyển các giá trị đề xuất thành số đã được duyệt.

Việc tiếp theo là hoàn thiện phần native SPEC-003 trong môi trường có Rust/MSVC và harness Windows, rồi resolver SPEC-009 và tích hợp SPEC-004. SPEC-002/008 vẫn cần đầu vào G0/nhân sự thực và review ADR-011 còn đề xuất. SPEC-005/007 thực hiện theo dependency; nhãn/recipe/training SPEC-008 chỉ chạy khi có input/budget, promotion pack trước SPEC-006. G1 cần đủ shell/job/resolver/GIS/viewer/PDF/bundle/spike; G2 cần evaluation model và workflow business. [Hướng dẫn dev](guides/development-guide.md) và [ma trận kiểm tra](guides/testing-strategy.md) là đầu mối bàn giao.
