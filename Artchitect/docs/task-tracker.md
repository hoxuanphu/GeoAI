# Task tracker GeoAI

**Cập nhật:** 11/11/2026, source `d4e0060` · **Múi giờ:** Asia/Bangkok (UTC+07:00).
**Giai đoạn:** chuẩn bị G0, chưa đạt. **Phạm vi hiện tại:** triển khai code theo yêu cầu mới ngày 08/11/2026; bắt đầu phần nền được phép trước G0, theo [nhật ký](evidence/codegen-2026-11-08/progress.md).

**Yêu cầu làm tiếp:** ghi lại [thiếu sót/nguyên nhân](project/implementation-gaps.md) và hoàn thiện các phần đủ điều kiện. [Kế hoạch backend trước G0](evidence/backend-pre-g0-2026-11-08/plan.md) / [tiến độ](evidence/backend-pre-g0-2026-11-08/progress.md): policy/archive, context/grant, framing và job core độc lập. Không ghi mọi logic chưa làm thành chờ native/G0.

Đọc [roadmap](roadmap.md) để biết gate/phạm vi, dùng file này theo dõi công việc và mở [spec](specs/README.md) để xem acceptance/test đầy đủ. Tracker không thay spec, quyết định G0 hoặc bằng chứng nghiệm thu. Vai trò dưới đây là trách nhiệm dự kiến, **chưa có tên người được giao hoặc deadline cam kết**.

## Sắp xếp tài liệu theo chủ đề 10/11/2026

Theo yêu cầu người dùng, đã hoàn tất nhóm tài liệu theo nền tảng, nghiệp vụ, hướng dẫn và dự án; các file bắt buộc trong `AGENTS.md` vẫn giữ đường dẫn và nội dung. [Báo cáo](evidence/docs-organization-2026-11-10/review.md) và [kết quả](evidence/docs-organization-2026-11-10/results.json) ghi kiểm liên kết/anchor và bảo toàn bằng chứng. Các mốc runtime và G0–G4 không thay đổi.

## Yêu cầu Ubuntu LTS và kiểm thử Cloud 10/11/2026

Người dùng đã yêu cầu thực thi plan 26 task. A-01–A-04 đã có implementation và test portable, A-05 runner đã chạy baseline Ubuntu 22.04/Debian; B-01 Rust/session/runtime paths đang triển khai. 010.1 vẫn partial vì chưa có baseline Ubuntu 24.04 và Windows/native regression; 010.2–010.3 chưa nghiệm thu. Xem [checkpoint 11/11](evidence/ubuntu-foundation-2026-11-11/progress.md).

- Đã ghi yêu cầu hỗ trợ Ubuntu 22.04 LTS và 24.04 LTS trong [SPEC-003](specs/003-desktop-shell.md); [hồ sơ đối chiếu](evidence/2026-11-10-linux-support-assessment.md) có nguồn Tauri/OpenAI, hiện trạng source và các lớp kiểm dự kiến.
- Đã hoàn tất phạm vi tài liệu [ADR-012](adr/ADR-012-ubuntu-desktop.md), [kiến trúc Ubuntu](platforms/ubuntu/ubuntu-desktop-architecture.md), [guide môi trường/đóng gói](platforms/ubuntu/ubuntu-development-and-packaging.md) và [UB-01–20](platforms/ubuntu/ubuntu-validation-matrix.md), đồng bộ SPEC-003/004/009 và nguồn/plans. [Kiểm cấu trúc](evidence/ubuntu-2026-11-10/results.json) pass, 145 file bảo vệ không đổi; [bàn giao/giới hạn](evidence/ubuntu-2026-11-10/review.md). ADR kỹ thuật vẫn đề xuất.
- Đã build và cài thử `.deb` shell preview trong Ubuntu 22.04 Docker, chưa có Linux backend trong pack; không phải bộ cài nghiệm thu G3. Foundation B–E đang tiếp tục; native user-manager/ext4, hai LTS và Windows vẫn cần bằng chứng riêng.
- Không thay bằng chứng Windows hiện có hoặc trạng thái G0–G4. [Kiểm tài liệu](evidence/2026-11-10-linux-support-doc-check.json) không là bằng chứng runtime/model/installer.

## Mốc tài liệu kiến trúc 09/11/2026

- Hoàn tất bản vẽ lại [kiến trúc Windows desktop chi tiết](platforms/windows/desktop-architecture-diagrams.md) theo phạm vi người dùng chọn; 8 sơ đồ Mermaid và bảng trách nhiệm/luồng dữ liệu, không triển khai runtime.
- [Bằng chứng trong SPEC-000](specs/000-documentation-baseline.md#vẽ-lại-kiến-trúc-desktop-ngày-09112026): UTF-8/link/fence/loại sơ đồ và delimiter pass; chưa parse/render Mermaid tự động.
- Còn chờ: kiểm renderer thực nếu cần ảnh xuất; các task runtime/native/model và gate giữ trạng thái riêng, không được coi hoàn tất từ sơ đồ.

## Mốc môi trường 09/11/2026

- Đã sửa trust store Node bền vững ở user (`NODE_USE_SYSTEM_CA=1`), npm ping/restore pass; 7 DOM tests, typecheck và frontend build pass.
- 57 contracts tests pass bằng Python/package có sẵn; `.venv-clean` không dùng system packages nhưng cài dependency chưa thành công.
- Còn chờ: cho phép tải Rustup/Tauri native/Python wheels qua chính sách mạng (GET trả 403; npm/pip ghi `MediaTypeBlocked`) và cài Build Tools tương tác có quyền quản trị (hai lần 1602, log nhắc UAC).
- [Bằng chứng/lệnh/kết quả](evidence/environment-2026-11-09/results.json). Không đóng SPEC-003/G1 hoặc xác nhận clean Python/native build.

## Quy ước trạng thái

| Trạng thái | Khi dùng |
| --- | --- |
| Chưa bắt đầu | Có spec, chưa thực hiện deliverable; dependency được ghi ở từng task |
| Chờ đầu vào | Thiếu dữ liệu/quyết định/phân công được nêu rõ; vẫn có thể chuẩn bị phần độc lập được phép |
| Đang làm | Đang thực hiện trong phạm vi được yêu cầu và đủ dependency cho bước đó |
| Chờ kiểm tra | Đã có deliverable nhưng chưa đủ acceptance/bằng chứng để đóng |
| Tạm dừng | Đã làm một phần, hiện dừng theo phạm vi người dùng; không coi là hoàn tất |
| Hoàn tất | Đạt acceptance trong spec, có ngày và đường dẫn bằng chứng; task hoàn tất không tự đóng gate |

Checkbox chỉ đánh dấu đầu ra đã kiểm, không đánh dấu vì đã có tài liệu mô tả. Checklist dưới là các mốc theo dõi, không thay toàn bộ acceptance của spec. Không tính tỷ lệ hoàn thành dự án từ số file, số checkbox hoặc số task khác kích thước.

## Bảng theo dõi chính

| Task | Trạng thái | Vai trò dự kiến | Dependency chính | Bước tiếp theo | Bằng chứng hiện có |
| --- | --- | --- | --- | --- | --- |
| [SPEC-000 — Tài liệu](specs/000-documentation-baseline.md) | Hoàn tất | Phụ trách kiến trúc/tài liệu | Baseline v1.4 và yêu cầu người dùng | Duy trì tracker khi có thay đổi đã kiểm | [Baseline/di chuyển](evidence/2026-11-08-documentation-review.md), [bổ sung review](evidence/2026-11-08-review-followup.md) |
| [SPEC-001 — Contracts](specs/001-contracts-baseline.md) | Hoàn tất phạm vi schema dự thảo | Backend/contracts | Ngữ nghĩa contracts; runtime access context tích hợp SPEC-009 | Tích hợp native context ở SPEC-009; chạy lại suite/schema mỗi khi đổi DTO | [55 tests và artifacts current sau API](evidence/codegen-2026-11-08/handoff.md), [review PASS](evidence/codegen-2026-11-08/final-review-report.md) |
| [SPEC-002 — Đầu vào G0](specs/002-g0-evidence.md) | Chờ đầu vào | Chủ nghiệp vụ/dự án + GIS/data + ML | AOI thực, QC bộ 7 lớp/T=3, provider/quyền, gate/hardware/budget và người chốt | Xác nhận AOI kiểm định, QC/crosswalk/nhãn độc lập, profile T=3 và nguồn cụ thể; thu dữ liệu thực | [Decision record](evidence/g0/decision-record.md), [AOI policy](domain/aoi-policy.md), [taxonomy](domain/landcover-taxonomy.md), [kiểm đồng bộ](evidence/2026-11-08-aoi-taxonomy-review.md); chưa đủ hồ sơ đóng G0 |
| [SPEC-003 — Desktop shell](specs/003-desktop-shell.md) | Chờ kiểm tra sau triển khai một phần | Frontend/native + backend | Kiểu nền SPEC-001; ADR-001/006/011 | ctypes owner/process đã kiểm; còn Rust build/WebView2/nested jobs/xuyên session | [Task 7](evidence/backend-pre-g0-2026-11-08/task-7-report.md), [bàn giao](evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md); chưa hoàn tất toàn SPEC |
| [SPEC-004 — Job/publish](specs/004-jobs-and-publish.md) | Chờ kiểm tra tích hợp DB/native | Backend/storage/IPC | Kiểu nền, launcher SPEC-003; nghiệm thu với resolver SPEC-009 | IPC/core/worker/publisher đã kiểm fixture; repository/migration/backup/GC đã kiểm phần DB thuần trên Debian; còn 1 error test DB và các ca DB+Windows skip | [Bàn giao 09/11](evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md), [review](evidence/backend-pre-g0-2026-11-08/task-final-review.md); không đóng 004.1–004.3 |
| [SPEC-005 — Prithvi spike](specs/005-prithvi-spike.md) | Chờ đầu vào | ML/runtime + GIS/data | HLS fixture thực, profile/hardware/budget G0 tương ứng; job/resolver đủ dùng | Khóa fixture/profile rồi đo backbone thật + decoder kỹ thuật | Chưa có tensor fixture thực hoặc benchmark |
| [SPEC-006 — Workflow nghiệp vụ](specs/006-landcover-workflow.md) | Chưa bắt đầu | Workflow/UI/review/report + QA | G0 đóng, G1 phần phụ thuộc đạt, model pack SPEC-008 | Nhận pack có evaluation rồi kiểm luồng tới reviewed report/PDF | Chưa có workflow/evaluation G2 |
| [SPEC-007 — Nền tảng G1](specs/007-g1-platform-validation.md) | Chưa bắt đầu | GIS/viewer/native/report + QA | SPEC-001/003/004/009; fixture/CRS/hardware; SPEC-005 khi đo cùng AI | Chuẩn bị fixture và kiểm CRS/viewer/PDF/bundle theo phạm vi được phép | Chưa có kiểm chứng nền tảng/native |
| [SPEC-008 — Training/model pack](specs/008-training-evaluation-model-pack.md) | Chờ đầu vào | GIS/data + ML + reviewer độc lập + packaging | Nhãn/split/profile/gate/budget; SPEC-005 giúp sàng lọc, promotion chạy lại G2 | Phân công người thực, chuẩn bị nhãn/split/recipe và checkout training | Mới có spec; chưa dataset/checkpoint/pack nghiệp vụ |
| [SPEC-009 — Importer/resolver](specs/009-importer-worker-resolver.md) | Thực hiện một phần, còn kiểm acceptance | Backend/storage + GIS/provider + native + QA | Kiểu nền SPEC-001, launcher SPEC-003; tích hợp SPEC-004 | Policy/grant/native reads/extraction/bootstrap fixture có kiểm; còn DB/live provider/driver và ma trận đầy đủ | [Task 8](evidence/backend-pre-g0-2026-11-08/task-8-report.md), [Task 9](evidence/backend-pre-g0-2026-11-08/task-9-report.md); [25 ca runtime](importer-resolver-security.md) chưa nghiệm thu toàn bộ |
| [SPEC-010 — Ubuntu foundation](specs/010-ubuntu-foundation.md) | A-01–A-04 có code/test portable; A-05 baseline đạt, B-01 đang làm | Native/Rust + backend/storage + QA | Kiểu SPEC-001, phần nền SPEC-003/004/009 và executor tương ứng | Tiếp tục B–E, bổ sung Ubuntu 24.04/Windows và native acceptance | [Checkpoint 11/11](evidence/ubuntu-foundation-2026-11-11/progress.md); 010.1–010.3 chưa hoàn tất |

**Tổng quan lúc khởi tạo:** chỉ SPEC-000 hoàn tất phạm vi tài liệu; SPEC-001 có một phần mã đang dừng, SPEC-002/005/008 đang chờ đầu vào, các task triển khai khác chưa bắt đầu. G0–G4 chưa có gate nào được ghi đạt.

## Mốc chi tiết cần theo dõi

### SPEC-000 — Tài liệu và điều hướng

- [x] 000.1 Bộ docs/ADR/specs, chuyển vào Artchitect và kiểm liên kết — bằng chứng baseline ở bảng trên.
- [x] 000.2 Bổ sung training/model pack, execution owner và resolver/security sau review — bằng chứng bổ sung ở bảng trên.
- [x] 000.3 Tạo tracker, nối roadmap/index/hướng dẫn cập nhật và kiểm tài liệu — kết quả ghi tại mục bằng chứng khởi tạo bên dưới.
- [x] 000.4 Vẽ lại kiến trúc desktop chi tiết ngày 09/11/2026 — [8 sơ đồ và diễn giải](platforms/windows/desktop-architecture-diagrams.md), [kiểm cấu trúc và giới hạn](specs/000-documentation-baseline.md#vẽ-lại-kiến-trúc-desktop-ngày-09112026).
- [x] 000.5 Phát triển tài liệu Ubuntu 22.04/24.04 LTS ngày 10/11/2026 — ADR-012, architecture/guide/UB-01–20 và đồng bộ nguồn/spec; [kiểm cấu trúc](evidence/ubuntu-2026-11-10/results.json), [bàn giao](evidence/ubuntu-2026-11-10/review.md). Chỉ hoàn tất tài liệu; runtime Ubuntu chưa chạy.
- [x] 000.6 Sắp xếp tài liệu theo thư mục chủ đề và cập nhật mục lục/liên kết — [kiểm/bàn giao](evidence/docs-organization-2026-11-10/review.md), [kết quả](evidence/docs-organization-2026-11-10/results.json); chỉ hoàn tất phạm vi tài liệu.
- [x] 000.7 Hoàn thiện SPEC-010/native profile/interface để làm đầu vào gen code Ubuntu; [review/kiểm tài liệu](evidence/spec010-2026-11-10/review.md) đạt, chưa triển khai code.
- [x] 000.8 Lập plan Superpowers chi tiết cho SPEC-010/AI gen code; 5 phần/26 task/133 bước và catalog/handoff; [self-review/kiểm tài liệu](evidence/ubuntu-plan-2026-11-10/review.md) đạt, chưa thực thi code.

### SPEC-001 — Contracts

- [x] 001.1 Hoàn thiện run/revision/evaluation/metrics/report và RPC/public registry; sửa cách gọi affine — [bằng chứng](evidence/codegen-2026-11-08/task-1-report.md).
- [x] 001.2 Đồng bộ typed access context/start ID/hash với SPEC-009, fixture và test; chưa thay native I/O acceptance.
- [x] 001.3 Sinh JSON Schema, kiểm missing/stale artifact, 51 test nền qua và [review độc lập PASS](evidence/codegen-2026-11-08/task-2-review-report.md); sau API DTOs chạy lại 55 tests và artifact checks đều pass ở [bàn giao cuối](evidence/codegen-2026-11-08/handoff.md).

### SPEC-002 — G0

Đã ghi nhận G0-D01–D07: AOI linh hoạt (vẽ/footprint import/Shapefile), bộ 7 lớp IDs 0–6 với `-1` ignore, T=3 nghiệp vụ và T=1 spike; cùng các quyết định chia đợt, chỉ số, nguồn mở và mục tiêu RAM/VRAM. AOI kiểm định, QC/crosswalk/nhãn độc lập, thời gian frame và các đầu vào còn lại chưa chốt; các mốc dưới vẫn chưa đủ điều kiện đánh dấu.

- [ ] 002.1 Xác nhận feature/AOI/class schema, nguồn/nhãn/license/split và người thực hiện/người duyệt.
- [ ] 002.2 Thử đọc HLS band/QA có quyền; có coverage ngày/tháng/composite 2–3 năm và manifest có hash.
- [ ] 002.3 Chốt CRS/điểm chuẩn/tolerance, hardware/workload, ngưỡng tuyệt đối/coverage và ngân sách/điểm dừng; ghi quyết định G0.

G0-D09 ghi [bộ tiêu chí nghiệm thu](domain/acceptance-criteria.md) đã được người dùng cung cấp; G0-D10 xác nhận máy GPU mới dùng riêng training/benchmark và giữ mục tiêu desktop trước đó. 002.3 còn chờ khóa sampling/metric/CI/coverage protocol, operation/điểm chuẩn, máy thực/CPU SLO và số vòng/lịch/chi phí thực. [Đối chiếu kỹ thuật](evidence/2026-11-08-acceptance-review.md) không thay bằng chứng đo model/coverage/benchmark.

Đã cụ thể hóa nhóm nguồn ảnh/nhãn thành quy tắc X–Y, phân vai weak/giải đoán/thực địa và kiểm thời gian/lưới/ignore/split theo [SPEC-002](specs/002-g0-evidence.md#nhóm-3--nguồn-ảnh-và-đóng-gói-input-x), ghi nhận G0-D08. [Báo cáo đối chiếu](evidence/2026-11-08-input-label-review.md) chỉ xác minh tài liệu; còn nguồn/quyền/nhãn/split thực và người duyệt, không đánh dấu 002.1/002.2 hoàn tất.

### SPEC-003 — Shell

- [ ] 003.1 Dựng shell/API/session, health/capabilities và handoff token đúng ranh giới.
- [ ] 003.2 Kiểm execution owner liên process/session, instance khác project, normal exit/crash và worker còn sống.
- [ ] 003.3 Lưu kết quả Windows/lifecycle/Host/Origin/token/Unicode theo acceptance.

Phần nền của 003.1/003.3 đã kiểm: metadata API/session, private pipe dev process, DTO/client sinh, React state/error/retry và Vite build. [Bằng chứng chi tiết](specs/003-desktop-shell.md#bàn-giao-phần-nền-ngày-08112026). Giữ các checkbox toàn mốc chưa hoàn tất vì chưa có native Tauri handoff/lifecycle, owner/Job Object/cross-session/WebView2/Unicode native acceptance. Không chuyển pipe dev process test thành shell crash test.

### SPEC-009 — Importer/resolver

- [ ] 009.1 Cấp bootstrap/context cho worker fixture; kiểm managed input và external registered input hợp lệ.
- [ ] 009.2 Hiện thực policy và chạy IMP-01–11, NET-01–06, RES-01–08, ca dương và sentinel ngoài staging.
- [ ] 009.3 Tích hợp context/start/candidate với SPEC-004, chạy native/process cases và lưu bằng chứng.

09/11/2026: managed/external registered reads, hash/identity, reparse/hardlink,
grant revocation, ZIP rollback và worker bootstrap đã kiểm với file/process thật.
[Bàn giao](evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md) giữ các mốc
tổng thể mở vì chưa đủ DB/driver/provider và toàn bộ IMP/NET/RES acceptance.

### SPEC-010 — Ubuntu foundation

- [ ] 010.1 Shared interfaces/Windows factory, private ledger và runner đã có code/test portable. Baseline Ubuntu 22.04/Debian: 207 Python pass, 67 Windows skip; chưa đủ Ubuntu 24.04/Windows native regression.
- [ ] 010.2 B-01 Rust/session/runtime paths đang triển khai; creator-bound socket, pidfd/owner/journal/FD bootstrap và native acceptance còn chờ B–C.
- [ ] 010.3 Linux I/O, publisher và fixture process→SQLite integration; chưa triển khai.

010.1–010.2 đang làm, chưa hoàn tất; 010.3 chưa triển khai. Không đánh hoàn tất từ mốc tài liệu 000.7 hoặc chỉ một test shared types. Acceptance chi tiết và suite 010-T01–09 ở SPEC-010; G0–G4 giữ trạng thái.

### SPEC-004 — Job/publish

- [ ] 004.1 Có queue/attempt/token/lease và SQLite migration/repository qua worker fixture thật.
- [ ] 004.2 Kiểm cancel/retry/stale attempt, race publish, crash/reconcile và resolver/candidate khác project/attempt.
- [ ] 004.3 Kiểm quyền tài nguyên liên project, worker cũ/compute release, GC/pin/restore và lưu integration log.

09/11/2026: IPC/coordinator và process→staging→publisher đã kiểm bằng fixture;
repository/Alembic/backup/restore/GC và native→SQLite composition có source/test
nhưng các tests DB skip do thiếu dependency. [Kết quả tổng thể](evidence/backend-pre-g0-2026-11-08/final-results.json)
ghi 192 Python pass/25 DB skip; chưa đóng các checkbox acceptance.

### SPEC-005 — Spike Prithvi kỹ thuật

- [ ] 005.1 Khóa HLS/preprocess/metadata/tensor/grid fixture thực và revision backbone/decoder kỹ thuật.
- [ ] 005.2 Kiểm export/runtime/output tolerance; đo CPU cold/warm/RAM/temp và NVIDIA nếu chọn pack.
- [ ] 005.3 Ghi kết luận khả thi kỹ thuật/phạm vi chưa kiểm; không nghiệm thu F1 từ decoder ngẫu nhiên.

### SPEC-008 — Model nghiệp vụ

- [ ] 008.1 Khóa dataset/nhãn/split có duyệt và kiểm leakage trước chipping.
- [ ] 008.2 Review recipe/environment/seed/budget; training và chọn checkpoint bằng validation.
- [ ] 008.3 Test độc lập, per-class metrics/coverage và RF đối chứng; quyết định gate đúng thẩm quyền.
- [ ] 008.4 Convert/benchmark đúng checkpoint, kiểm license/hash/runtime và bàn giao model pack cho SPEC-006.

### SPEC-007 — Kiểm nền tảng G1

- [ ] 007.1 Kiểm CRS/điểm chuẩn/ranh UTM, mask/grid/area và fixture GIS phù hợp.
- [ ] 007.2 Kiểm viewer/auth/Range/codec/WASM/state/tài nguyên, draft PDF tiếng Việt và native bundle.
- [ ] 007.3 Tổng hợp bằng chứng cùng SPEC-003/004/005/009; chỉ kết luận G1 khi đủ phần phụ thuộc.

### SPEC-006 — Workflow G2

- [ ] 006.1 Nhận model pack SPEC-008, chạy HLS → snapshot → Prithvi nghiệp vụ → revision/review → metrics/PDF.
- [ ] 006.2 Kiểm representation/review/provenance, export/runtime cuối, gate tuyệt đối/coverage/CPU budget và recovery.
- [ ] 006.3 Lưu golden output/evaluation/e2e report và quyết định G2; không dùng synthetic fixture để đóng nghiệp vụ.

## Dependency và việc đang chờ

Kiểu nền SPEC-001 → launcher SPEC-003 → resolver SPEC-009 → tích hợp job SPEC-004 → spike/nền tảng SPEC-005/007. Phần schema/start/context đầy đủ nghiệm thu cùng SPEC-009 rồi chạy lại suite SPEC-001; không đòi các spec hoàn tất vòng lẫn nhau để bắt đầu.

SPEC-002 thu thập đầu vào song song các task nền tảng được phép trước gate. Nhãn/recipe/training SPEC-008 chuẩn bị song song G1 khi đủ đầu vào tương ứng; không đợi toàn UI/viewer hoàn tất. SPEC-006 cần G0, các phần G1 phụ thuộc và pack SPEC-008 đạt điều kiện.

| Mã chờ | Nội dung | Ảnh hưởng / bước xử lý |
| --- | --- | --- |
| WAIT-01 | Đã gỡ: người dùng yêu cầu thực thi code ngày 08/11/2026 | Tiếp tục theo dependency và gate; không tự đóng G0 |
| WAIT-02 | Đã chốt cách tạo AOI, bộ 7 lớp và T profile; còn AOI kiểm định/thời gian frame, QC/crosswalk/nhãn độc lập, dữ liệu/quyền, gate/hardware/budget và nhân sự | Hoàn thiện hồ sơ SPEC-002 theo decision record; chưa có ngày cam kết |
| WAIT-03 | Chưa có nhãn/split/recipe/checkpoint và test nghiệp vụ | SPEC-008 chịu trách nhiệm sản xuất đầu vào, không giao ngầm cho SPEC-006 |
| WAIT-04 | ADR-011 còn đề xuất; có tests Windows cùng session nhưng chưa đủ phạm vi acceptance | Hoàn thiện review/fix và kiểm xuyên session, recovery, integration; không coi ctypes fixture là toàn bộ G1 |
| WAIT-05 | Còn thiếu toolchain/MSVC và harness xuyên session trên Windows; Rust/Cargo Ubuntu Cloud đã cài và Cargo check pass | Chặn Rust/Tauri build, WebView2 và acceptance xuyên session; không chặn viết source hoặc tests ctypes/process có sẵn; [Task 7](evidence/backend-pre-g0-2026-11-08/task-7-report.md) |
| WAIT-06 | Lượt cài sạch Windows trước đây bị HTTP 403; cài Python dependency mới trong Ubuntu Cloud đã thành công, không còn là blocker chung của Cloud | Dùng interpreter/package đã có để kiểm, ghi version thực; chưa kết luận cài mới sạch/offline pack |

G3 installer/máy sạch/offline/upgrade và G4 PHY/provider/server được theo dõi ở roadmap; chưa có spec thực thi riêng. Chỉ thêm task có ID/spec sau khi xác định nhu cầu và đầu vào, không tạo task solver trống hoặc tự cam kết lịch.

## Cách cập nhật sau mỗi phiên

1. Chọn SPEC và mốc con đang làm; ghi người thực/người duyệt khi được phân công, ngày cập nhật và dependency còn thiếu. Không gán vai trò dự kiến như nhân sự đã nhận việc.
2. Cập nhật trạng thái ở bảng chính, checkbox đã kiểm và lý do chờ/dừng. Khi có deliverable chưa kiểm thì ghi Chờ kiểm tra.
3. Muốn đóng task: chạy kiểm đúng acceptance, lưu lệnh/môi trường/kết quả/log/artifact thực, thêm link ở tracker và spec; đồng bộ trạng thái gate/phạm vi ở roadmap khi bị ảnh hưởng.
4. Thêm dòng lịch sử ghi ngày, task, thay đổi/kết quả và bằng chứng. Giữ lịch sử, không sửa kết quả cũ thành test đã chạy mới. Nếu tracker/spec/roadmap khác nhau thì kiểm evidence và sửa đồng bộ, không tự chọn trạng thái lạc quan hơn.

## Lịch sử cập nhật

Ngày 11/11/2026 — môi trường build Ubuntu: đã cài/kiểm toolchain và dependency trên Ubuntu 22.04.5 Docker, Cargo check/native-link/frontend pass; Python 155 pass/64 skip/1 error DB. Sinh Cargo.lock, thêm placeholder icon và sửa 2 lỗi compiler ở main.rs. [Lệnh, versions, logs và giới hạn](evidence/ubuntu-build-environment-2026-11-11/handoff.md). Chưa tạo binary/installer, chưa có systemd user manager/24.04/Windows acceptance; không đóng 010.1 hay gate.

Ngày 11/11/2026: tiếp tục A-01, thêm Protocol I/O và kiểu ExternalRegistration; 3 tests shared pass trên Debian, Windows I/O 7 skip, storage 78 tests có 1 lỗi DB đã biết và 22 skip. [Bàn giao tiếp nối](evidence/2026-11-10-ubuntu-source-review.md#tiếp-tục-a-01). Factory, registry, deadline và native acceptance còn thiếu; không đóng mốc.

Ngày 11/11/2026, đồng bộ tài liệu với `d4e0060`: bỏ phương án khảo sát cũ, dùng SPEC-010/profile và plan A–E; A-01 partial, A-02–E-05 chưa bắt đầu. Kiểm 6 suite Python trên Debian: 218 tests, 153 pass, 64 skip, 1 error `CursorResult` tại `test_repository.py:288`. [Báo cáo cập nhật và lệnh tái hiện](evidence/2026-11-10-ubuntu-source-review.md#đối-chiếu-lại-ngày-11112026-tại-d4e0060). Không đổi code/test, không đóng mốc hoặc gate.

Rà soát lại sau đồng bộ `0abe24d`, ngày 10/11/2026: [báo cáo source/tests lịch sử](evidence/2026-11-10-ubuntu-source-review.md). Phương án khảo sát cũ đã bỏ ngày 11/11/2026; hiện dùng SPEC-010/profile và plan A–E. Đã cài DB extra và chạy sáu suite: 152 pass/64 Windows-only skip/1 error ở phép chuyển `CursorResult` thành dict trong test DB; đọc lại DB xác nhận trạng thái dữ liệu mong đợi. UI 7 tests/typecheck/build và schema/client/pip checks pass. Lỗi test được ghi nhận, chưa sửa code. U1–U5 vẫn là kế hoạch; chưa nghiệm thu native Ubuntu/installer hoặc đóng gate. Ghi chú khảo sát baseline cũ bên dưới giữ giá trị lịch sử theo source cũ.

Khảo sát nhánh `feat/ubuntu-installer` ngày 10/11/2026: đã lập phương án khảo sát Ubuntu 22.04/24.04 với mốc U1–U5 và ma trận kiểm (hồ sơ cũ, đã bỏ ngày 11/11/2026; không dùng thay plan A–E). Chỉ hoàn tất khảo sát/lập phương án; các mốc triển khai chưa bắt đầu. Native build, installer, lifecycle và máy sạch Ubuntu chưa được kiểm. Chạy lại baseline trên Debian 13: contracts 57, integration 14, architecture 2, catalog 9, storage 19 và UI 7 tests đều pass; schema/client checks, pip check, typecheck và frontend build pass (exit 0). Log tại `/workspace/geoai-onboarding/ubuntu-plan-baseline.log`; không dùng kết quả Debian để đóng SPEC-003/007 hoặc gate. Chỉ thay tài liệu trong đợt khảo sát.

| Ngày | Task | Thay đổi | Bằng chứng |
| --- | --- | --- | --- |
| 10/11/2026 | SPEC-000 / 000.8; SPEC-010 plan | Hoàn tất plan Superpowers cho AI thực hiện từng task: 5 phần, 26 task/133 bước, interface catalog/prompt/handoff, self-review và coverage9suites. Chỉ đóng tài liệu; task code vẫn chưa bắt đầu | [Hồ sơ plan](evidence/ubuntu-plan-2026-11-10/review.md), [kết quả](evidence/ubuntu-plan-2026-11-10/results.json); 416 file bảo vệ giữ hash |
| 10/11/2026 | SPEC-000 / 000.7; SPEC-010 đặc tả | Hoàn tất spec/native profile/interface Ubuntu foundation; sửa creator binding, stop race và generation recovery sau review độc lập. Chỉ đóng mốc tài liệu; 010.1–010.3 chưa triển khai | [Hồ sơ review/kiểm](evidence/spec010-2026-11-10/review.md), [kết quả](evidence/spec010-2026-11-10/results.json); 332 file bảo vệ không đổi hash, gate giữ nguyên |
| 09/11/2026 | SPEC-001/003/004/009 | Tiếp tục code theo plan dù thiếu môi trường: IPC/core, guarded repository/migration, Windows owner/process/I/O, transport/bootstrap, extraction/publisher/GC. 192 Python pass/25 DB skip, 7 DOM và build/artifact checks pass; Rust/DB/gates chưa nghiệm thu | [Bàn giao](evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md), [review cuối](evidence/backend-pre-g0-2026-11-08/task-final-review.md), [results](evidence/backend-pre-g0-2026-11-08/final-results.json) |
| 08/11/2026 | SPEC-000 / 000.3 | Hoàn tất khởi tạo/kiểm tracker SPEC-000–009 từ trạng thái tài liệu và kiểm kê hiện có; chưa tiếp tục code | Mục kiểm khởi tạo bên dưới; kiểm tài liệu đạt, không đóng gate runtime |
| 08/11/2026 | SPEC-001 / 001.1–001.3 | Yêu cầu code mới; hoàn thiện contracts/run/RPC/private context/exporter. Baseline 30 tests lỗi → 51 tests pass; schema check và review độc lập pass | [Triển khai](evidence/codegen-2026-11-08/task-1-report.md), [review](evidence/codegen-2026-11-08/task-2-review-report.md), [parent kiểm lại](evidence/codegen-2026-11-08/task-1-parent-verify.log); không đóng G0/G1 |
| 08/11/2026 | SPEC-003 foundation / SPEC-001 DTOs | Metadata API/session/dev pipe process, private handoff DTO/client, React UI/state/retry/timeout, Tauri scaffold chưa hỗ trợ native. Lượt cuối: 55+14+2 Python và 7 DOM pass; artifacts/typecheck/build pass; chưa đóng các mốc native | [Bàn giao](evidence/codegen-2026-11-08/handoff.md), [review cuối](evidence/codegen-2026-11-08/final-review-report.md); chờ Rust/MSVC/Tauri CLI/cross-session harness, resolver/job và input thực G0 |
| 08/11/2026 | SPEC-002 / ghi nhận từng phần | Ghi quyết định chia đợt, ưu tiên nguồn mở và mục tiêu máy; đồng bộ nguồn/plans và trạng thái, giữ 002.1–002.3 chưa hoàn tất | [Decision record](evidence/g0/decision-record.md), [kiểm tài liệu](evidence/2026-11-08-g0-intake-review.md); chưa đóng G0 |
| 08/11/2026 | SPEC-002 / AOI và bộ lớp | Đối chiếu AOI vẽ/ảnh import/Shapefile và IDs 0–6/-1; sửa liên kết decision record, đồng bộ roadmap/SPEC-006/008, T=3 nghiệp vụ và giới hạn crosswalk; giữ 002.1–002.3 chờ đầu vào | [Kiểm đồng bộ AOI/taxonomy](evidence/2026-11-08-aoi-taxonomy-review.md); chỉ tài liệu, chưa đóng G0 |
| 08/11/2026 | SPEC-002/008 / ảnh X và nhãn Y | Cụ thể hóa nhóm 3/4, phân vai nguồn nhãn và bốn kiểm soát dữ liệu; sửa các diễn giải dtype/thời gian/grid/ignore chưa đúng, không duyệt số chip/ngưỡng minh họa | [Đối chiếu X–Y](evidence/2026-11-08-input-label-review.md); chưa có dữ liệu/split/model được nghiệm thu |
| 08/11/2026 | SPEC-002 / tiêu chí định lượng | Ghi đủ ngưỡng bảy lớp/global, coverage, diện tích/CRS và budget/stop; xác định protocol/máy/CI còn mở, đồng bộ SPEC-006/008 và nguồn/plans | [Đối chiếu bộ ngưỡng](evidence/2026-11-08-acceptance-review.md); giữ 002.1–002.3 và các gate chưa hoàn tất |

<a id="tracker-verification"></a>

## Bằng chứng khởi tạo tracker

Ngày 08/11/2026, kiểm trực tiếp qua `python -X utf8 -` bằng stdin, exit code 0: 60 file Markdown, 531 lượt liên kết nội bộ (75 lượt có anchor), 127 bảng và code fence không phát hiện lỗi trong bộ kiểm cấu trúc hiện có; 5 block JSON parse được. Tám block Mermaid chỉ kiểm nội dung/fence, chưa render. Đối chiếu tracker xác nhận đủ 10 SPEC duy nhất và 31 ID mốc con duy nhất, không có checkbox triển khai chưa kiểm bị đánh dấu hoàn tất.

SHA-256 của cả 8 file mã/test/fixture/config trong inventory trước/sau không đổi; chỉ thêm tracker và cập nhật 5 file Markdown điều hướng/spec. Chưa gán nhân sự/deadline và không cập nhật lại số đo lịch sử của các báo cáo trước. Không chạy suite contracts/runtime/model vì đợt này chỉ tạo tài liệu theo dõi; bằng chứng này chỉ đóng mốc tài liệu 000.3, không xác nhận G0–G4.
