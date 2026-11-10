# Hợp đồng trao đổi — bản dự thảo 0.1.0

Đọc khi tạo/đổi dữ liệu trao đổi. Cơ sở: [hợp đồng thiết kế v1.4](../plans/05_hop_dong_du_lieu_va_versioning.md). [Package Pydantic](../../backend/geoai/contracts) đã có common/geography/models/runs/rpc/access, public exports và registry trong [SPEC-001](specs/001-contracts-baseline.md). Pydantic là nguồn trường/kiểu; [JSON Schema](../../schemas/contracts-v0.1.0.json) sinh bằng exporter. [Bằng chứng](evidence/codegen-2026-11-08/task-1-report.md) và [review](evidence/codegen-2026-11-08/task-2-review-report.md) chỉ xác nhận validation metadata dự thảo, không thay kiểm runtime/quyền/gate.

## Quy ước chung

[SPEC-010](specs/010-ubuntu-foundation.md) dự kiến thêm private `LinuxOwnerLedger` khi triển khai, với layout trong [native profile](platforms/ubuntu/ubuntu-native-profile.md). Model này chưa có trong Pydantic/schema hiện hành; phải thêm source/registry/fixture/exporter/tests cùng task contracts trước sử dụng. Profile control shell dùng hằng byte native và SessionDescriptor hiện có, không tạo public RPC hoặc nới capabilities Literal false bằng tài liệu.

- Mọi record lưu lâu dài có `schema_version = "0.1.0"` và `created_at`; thời gian phải có timezone và được chuẩn hóa UTC. Kiểu giá trị lồng như CrsRef/AttemptKey không lặp metadata record.
- Từ chối version khác và trường không biết. ID nội bộ gồm chữ/số, dấu chấm/gạch/gạch dưới/hai chấm; asset ID có namespace provider. ID không phải URL, đường dẫn hay credential.
- Hash SHA-256 là 64 ký tự hex chữ thường. ContentIdentity phân biệt hash, version provider và ETag chỉ là hint; không tự coi ETag là hash.
- Số phải hữu hạn; NoData NaN được biểu diễn bằng chuỗi `"nan"`, không bằng JSON NaN. Coverage dùng **fraction từ 0 đến 1**, không phần trăm.
- Pydantic `frozen` chặn gán thuộc tính nhưng không biến mọi dict lồng thành bất biến sâu. Bất biến sau publish phải do snapshot serialization, hash, quyền ghi và storage thực hiện.
- Credentials/signed URLs nằm trong resolver/session, không trong hợp đồng bền vững. Schema giới hạn trường, ID và kiểu; không thể phát hiện mọi secret giấu trong chuỗi/parameters. Boundary importer và logging còn phải lọc/redact theo policy.

## Records

| Contract | Khóa và dữ liệu chính | Ràng buộc đáng chú ý |
| --- | --- | --- |
| AssetRef | `asset_id`, provider/collection/profile, scene/asset key, processing level, acquisition range, CrsRef, footprint, bands, QA, license, identity | Namespace provider, không có download_url; band name duy nhất |
| GridSpec | `grid_id`, CrsRef, affine 6 phần tử, width/height, pixel interpretation, data_kind, resampling, dtype/NoData, vertical datum | Affine không suy biến; categorical chỉ nearest/mode |
| TransformSpec | `transform_id`, source/target CrsRef, operation, grids/hash, area of use, tolerance, PROJ/database version | Khóa operation và tài nguyên; kiểm độ chính xác thực thuộc geoprocessing |
| InputSnapshot | snapshot/project ID, AOI WGS84, asset IDs, band mapping, QA, acquisition range, temporal selection, mosaic recipe, grid/transform/dependencies, retention | Composite cần recipe; không tự pin mọi snapshot |
| ModelSpec | model/backbone/decoder identity, task/product, tensor, band order, normalization, metadata policy, GSD, classes, runtime/precision, licenses/evaluation, readiness | Đúng số band/mean/std; std dương; segmentation nghiệp vụ cần decoder đã huấn luyện và evaluation |
| PhysicalModelSpec | physical_model/method ID/version/kind, implementation hash, biến/đơn vị, parameter profile, grid/time/datum/biên, solver, calibration/evaluation, uncertainty, resume capability | PHY-06 cần solver version; mode nghiệp vụ cần evaluation; không giả backbone |
| DatasetVersion | dataset ID, label asset IDs, class schema, split/phương pháp, license, hash | Chia trước chipping; schema không tự chứng minh không rò rỉ không gian |
| JobSpec | job/project/workflow/version, snapshot/grid, execution kind, model/physical/parameter refs, parameters, compute policy/budget, idempotency key | ML cần model ref; physical cần PhysicalModelSpec ref; hybrid cần cả hai |
| RunManifest | run/job/attempt, snapshot, hashes, grid/transforms, model/physical refs, runtime thực, fallback, coverage, artifact/checksum, physical provenance | Candidate có thể thiếu artifact; published phải có artifact, job/attempt khớp; physical có provenance riêng |
| ResultRevision | revision/run/parent, edit assets, representation, class schema, author/reason, review state/by/at | Reviewed cần người/thời gian; sửa tạo revision mới chưa duyệt ở service |
| EvaluationRecord | evaluation/dataset/split/target model, kind, metrics, baseline ref, gate ID/decision, limitations | Technical không được ghi pass gate nghiệp vụ; pass nghiệp vụ phải có gate ID |
| MetricsSnapshot | metrics/revision/run, representation, AOI, coverage, metrics, unit/method refs | Service kiểm revision/representation có thẩm quyền và methods đúng |
| ReportContext | context/revision, representation, metrics snapshot, AOI/acquisition range, coverage/evaluation, template/style/font versions, report kind và review snapshot | Official cần reviewed snapshot; service kiểm lại revision thực, không tin client tự khai reviewed |

Trường có thể đối chiếu tại [contracts package](../../backend/geoai/contracts). Các nhóm run/review/report được diễn giải bên dưới. Cấu trúc 0.1.0 chưa được G1/G2 xác nhận tương thích pipeline/installer. Public RPC không nhận URI/path tùy ý; location trong context private chưa tự chứng minh có quyền I/O.

## Kiểu giá trị và cách diễn giải

| Kiểu | Trường/miền giá trị | Ngữ nghĩa |
| --- | --- | --- |
| Identifier | Chuỗi 1–256 ký tự, mẫu `^[A-Za-z0-9][A-Za-z0-9._:-]*$` | Không tự chứng minh record tồn tại hoặc có quyền; generation token phải do coordinator cấp, không lấy từ client |
| TimeRange | `start`, `end`: thời gian có offset, chuẩn hóa UTC, start ≤ end | Acquisition range khác thời gian chạy/lập báo cáo; cùng timestamp hợp lệ cho một cảnh |
| CrsRef | `format`: authority/wkt2/projjson; `definition`, `revision`, `axis_order`, `unit` | Geometry AOI/footprint vẫn luôn longitude/latitude WGS84; CRS raster mô tả grid gốc |
| AttemptKey | `job_id`, `attempt_id`, `generation_token` | So khớp đủ ba trường; token không phải idempotency key hoặc credential truy cập API |
| ResourceBudget | `cpu_threads` > 0, `ram_bytes` > 0; `temporary_bytes`, `vram_bytes` ≥ 0 | Integer, không nhận boolean; bytes, không GB ngầm định; vram mặc định 0 cho CPU |
| ArtifactRef | `asset_id`, `sha256`, `size_bytes`, `media_type` | Byte count ≥ 0 và hash thực; worker gửi ref chưa đủ điều kiện công bố |
| ContentIdentity | `kind`: sha256/provider_version/etag_hint; `value` | Provider version phải có khả năng resolve phiên bản; etag_hint không bảo đảm tái lập |
| StructuredError | `code`, `message`, `retryable` | Miền code theo IPC; không có stack trace/raw provider response chứa secret trên wire |

Tập enum dự thảo: `readiness=technical/business`; `temporal_selection=single_date/composite/time_series`; `retention_profile=references/offline_pinned`; `review_state=unreviewed/reviewed`; `publication_state=candidate/published`; `representation=raster/vector`; `report_kind=draft/official`. Trạng thái chạy job thuộc coordinator, không trộn với readiness, publication hoặc review.

`retention_profile` ghi ý định khi tạo snapshot; pin/unpin và byte availability hiện tại nằm ở storage record riêng. Bỏ pin không sửa InputSnapshot lịch sử. Các dict mở như `parameters`/metrics không cho phép NaN/Infinity; workflow phải có profile tham số có kiểu trước khi thực thi, không chạy expression/script từ JSON.

## Nhóm contracts run/review/report

Tên trường sau được định kiểu trong `runs.py` và kiểm cùng fixture/test SPEC-001. Danh sách nhóm trường dùng cùng metadata `schema_version`, `created_at` của record, không thay thế schema được sinh.

### JobSpec và RunManifest

| Record / nhóm trường | Kiểu và điều kiện |
| --- | --- |
| JobSpec — danh tính | `job_id`, `project_id`, `workflow_id`, `workflow_version`, `input_snapshot_id`, `grid_id`, `idempotency_key`: chuỗi ID/version không rỗng |
| JobSpec — thực thi | `execution_kind`: ml/physical/hybrid/gis; `model_ids`, `physical_model_ids`, `parameter_snapshot_ids`: danh sách ID; `parameters`: JSON object hữu hạn |
| JobSpec — tài nguyên | `compute_policy`: cpu/auto hoặc `gpu:<id>` theo registry thiết bị; `resource_budget`: ResourceBudget. CPU chạy CPU, auto chọn capability đã kiểm, GPU chỉ định không âm thầm về CPU |
| RunManifest — provenance chung | `run_id`, `job_id`, `attempt`, `input_snapshot_id`, `input_sha256`, `pipeline_sha256`, `config_sha256`, `grid_id`, `transform_ids`, `model_ids`, `physical_model_ids` |
| RunManifest — runtime | `runtime` gồm `runtime_id`, `backend`, `runtime_version`, `precision`; khi GPU phải có device/driver provenance từ runtime, không lấy tên người dùng nhập làm bằng chứng |
| RunManifest — kết quả | `used_fallback`, `fallback_reason` khi có; `coverage_fraction` [0,1]; `artifacts`: ArtifactRef[]; `quality_flags`: string[]; `publication_state` |
| RunManifest — vật lý | `physical_provenance` khi có PhysicalModelSpec: parameter snapshot IDs/hash, forcing và điều kiện đầu/biên IDs/hash, solver version/hash khi dùng, calibration/evaluation/uncertainty refs và diagnostics phù hợp phương pháp |

`execution_kind=ml` cần ít nhất một model; physical cần PhysicalModelSpec; hybrid cần cả hai; gis không tạo model giả cho phép đo GEO-01. Ràng buộc từng phương pháp về parameter/forcing/biên do profile kiểm. `JobSpec.job_id` là danh tính record, vì vậy `start.job_spec_id` cùng giá trị với `attempt.job_id` trong draft này.

JobSpec cố định ý định; RunManifest ghi cấu hình thực dùng. Mỗi attempt mới có danh tính riêng, worker trả candidate mới; coordinator tạo bản manifest published sau kiểm tra, không sửa file candidate đã được hash. Published cần ít nhất một artifact, `attempt.job_id` khớp `job_id`, mọi checksum/byte đã kiểm; `used_fallback=true` cần lý do. Service đối chiếu reference với JobSpec và không nhận runtime chưa được kiểm tương thích.

Parameter snapshot/calibration/forcing profile là khái niệm thiết kế trong v1.4, **chưa có schema tổng quát hoàn chỉnh**. Feature PHY cụ thể phải đặc tả và sinh schema cho profile của nó trước khi nhận payload thực; không coi một dict tự do có hash là đủ provenance vật lý. Không kéo toàn bộ profile PHY vào SPEC-001 hoặc bản đầu khi chưa chọn feature G4.

Giới hạn triển khai draft SPEC-001: `PhysicalModelSpec` và `JobSpec` vẫn mô tả thiết kế physical/hybrid, nhưng `RunManifest` từ chối `physical_model_ids` không rỗng và chỉ nhận `physical_provenance=null` cho tới khi có profile provenance có kiểu cho feature đã chọn. Không nhận dictionary provenance tự do, kể cả candidate. `RuntimeProvenance` có `device_id`/`driver_version` bắt buộc cùng nhau khi khai báo GPU (backend `cuda`, `tensorrt`, `onnxruntime_cuda` hoặc có device ID); service phải kiểm backend/device thực và capability đã kiểm định. Evaluation/MetricsSnapshot nhận các metric số hữu hạn; per-class là mapping lớp → mapping metric → số. Cấu trúc metric khác cần profile có kiểu riêng. RPC success giữ JSON hữu hạn cho negotiation; payload có `accepted` phải là acknowledgement chỉ chứa boolean `accepted`.

### Revision, evaluation, metrics và report

| Record / nhóm trường | Kiểu và điều kiện |
| --- | --- |
| ResultRevision — lineage | `revision_id`, `base_run_id`; `parent_revision_id` tùy chọn, không tự trỏ; `edit_asset_ids`; `representation`; `class_schema_id` |
| ResultRevision — tác giả/duyệt | `author_id`, `reason`, `review_state`; reviewed bắt buộc `reviewed_by`, `reviewed_at` có timezone; unreviewed không mang metadata duyệt của bản cũ |
| EvaluationRecord — phạm vi | `evaluation_id`, `dataset_id`, `split_id`, `target_model_id`; `kind`: technical/business; `metrics`, `per_class_metrics` số hữu hạn; `baseline_evaluation_id` tùy chọn |
| EvaluationRecord — quyết định | `gate_id` khi đánh giá gate, `gate_decision`: not_assessed/pass/fail; `limitations`: string[]. Technical không được pass gate business; business pass cần gate version được duyệt và bằng chứng có thẩm quyền |
| MetricsSnapshot | `metrics_snapshot_id`, `run_id`, `revision_id`, `representation`, `aoi` WGS84, `coverage_fraction`, `metrics`, `unit`, `method_ids` |
| ReportContext — dữ liệu | `report_context_id`, `revision_id`, `representation`, `metrics_snapshot_id`, `aoi`, `acquisition`, `coverage_fraction`, `evaluation_ids`, `model_ids`, `physical_model_ids` |
| ReportContext — trình bày/duyệt | `template_version`, `style_version`, `font_version`, `report_kind`, `review_state_snapshot`; official cần reviewed và backend kiểm quyền/readiness/gate thực |

Một MetricsSnapshot với `unit` chung chỉ chứa các metric cùng đơn vị; chỉ số hỗn hợp hoặc per-class có cấu trúc cần profile được version hóa, không đặt mọi số dưới `ha`. Không tính metrics từ geometry hiển thị đã simplify hoặc raster overview. ReportContext chỉ tham chiếu một revision/representation và MetricsSnapshot khớp, không chọn “latest” lúc render.

Review metadata phải được service tạo từ hành động người có quyền, không tin client tự khai reviewed. Sửa nhãn/hình học/ngưỡng tạo revision mới unreviewed; review không sửa dự đoán gốc. Với `parent_revision_id`, repository phải chặn chu trình và parent khác base run/project; schema đơn record chưa kiểm được toàn bộ lineage. Review và metrics/report là snapshot/sự kiện có lịch sử, không ghi đè PDF cũ theo trạng thái UI hiện tại.

## Kiểm tra liên record

Pydantic kiểm tra một payload; service/repository phải kiểm reference tồn tại, project membership/quyền, uniqueness, version/hash thực, model readiness và quan hệ revision/metrics/report. Schema không kiểm điểm chuẩn CRS, bytes artifact, token attempt còn hiệu lực hoặc chất lượng model. Giao dịch publish phải kiểm lại token/trạng thái/unique publication theo [IPC](ipc-protocol.md).

| Thời điểm | Chủ trì kiểm tra | Từ chối khi |
| --- | --- | --- |
| Import/resolve | Catalog + product profile + storage | Sai product/band/QA/license, đổi nội dung phiên bản, path/nguồn không được phép |
| Lập snapshot/job | Workflow/application service | Reference khác project, thiếu band/parameter/forcing, grid/ModelSpec không tương thích, capability chưa đủ |
| Start attempt | Coordinator/worker resolver | Token/lease cũ, hash/budget không khớp, tài nguyên không còn; không tự tìm scene khác để lấp |
| Publish | Coordinator/publisher + transaction repository | Sai bytes/grid/coverage/hash, hủy trước commit, token cũ, publication trùng hoặc reference không khớp |
| Review/report | Review/report application service | Sai revision/representation, metrics stale, chưa duyệt, model technical hoặc gate business chưa đủ cho official |

Chuỗi chính: `AssetRef → InputSnapshot → JobSpec → RunManifest → ResultRevision → MetricsSnapshot → ReportContext`. ModelSpec và PhysicalModelSpec tham gia JobSpec/RunManifest; DatasetVersion/EvaluationRecord chứng minh phạm vi validation.

## Contracts tạm cho resolver và hồ sơ training

[WorkerAccessContext](worker-resolver.md) là metadata quyền runtime theo worker/project/attempt, không là snapshot bền vững để export. Pydantic ở `contracts/access.py`; private registry/exporter và RPC start đã đồng bộ cùng SPEC-001. `access_context_id`/`access_context_sha256` bắt buộc trong start draft; context private có location được đăng ký, không mở field path tùy ý cho UI. Native bootstrap/resolver và kiểm quyền thực còn ở SPEC-009.

[SPEC-008](specs/008-training-evaluation-model-pack.md) dùng DatasetVersion/EvaluationRecord/ModelSpec đã có khái niệm, đồng thời phải định kiểu recipe/training/pack manifests khi triển khai. Chuỗi hồ sơ phải khóa dataset/split/preprocess/recipe/checkpoint/runtime/hash, không suy quan hệ chỉ từ tên file. Tách evaluation model/pack khỏi acceptance tích hợp của SPEC-006; thiếu gate/nguồn/kiểm runtime thì không promote business.

Draft private `WorkerLaunchPacket` carries exact context/job/snapshot JSON,
typed `StartParams`, trusted root registrations and optional `FixtureOutput`
through one inherited handle. `FixtureOutput` binds the attempt staging ID,
absolute staging root, relative artifact path and candidate `RunManifest`; its
single artifact must match the fixed synthetic fixture bytes. These types live
only in `PRIVATE_CONTEXT_MODELS` and are absent from public RPC/client payloads.
The Windows worker/publisher mechanism check is recorded in
[Task 8 evidence](evidence/backend-pre-g0-2026-11-08/task-8-report.md); it is
not a GIS/model validator or database transaction proof.

## DTO metadata API và private session handoff

SPEC-003 bổ sung `contracts/api.py`: `HealthResponse`/`CapabilitiesResponse` thuộc registry public wire; capabilities chỉ công bố health/capabilities metadata, các cờ inference/native launcher/execution owner/project writer đều false. Không dùng technical metadata ready làm bằng chứng model hay owner sẵn sàng.

`SessionDescriptor` là DTO IPC private tạm thời, thuộc `PRIVATE_CONTEXT_MODELS`, có loopback base URL/port và session token. TypeScript sinh từ Pydantic, không khai báo kiểu trao đổi riêng bằng tay. Token chỉ giữ trong bộ nhớ/handoff pipe tin cậy; không persist/log, không đưa vào snapshot/project/export và không dùng query/URL để truyền token. DTO/private registry trong schema mô tả cấu trúc, không chứa token thực. Runtime native handoff chưa nghiệm thu; bootstrap pipe dev chỉ phục vụ kiểm metadata API.

## Version và sinh artifact

1. Thay đổi không tương thích với schema đã phát hành phải tăng major theo v1.4, có migration/fixture đọc cũ và review. `0.1.0` hiện chỉ là draft chưa phát hành; thay trường trong giai đoạn này vẫn phải ghi rõ trong spec/PR và đồng bộ consumer/fixture, không giả định tương thích ngầm hoặc tự coi draft là API sản phẩm.
2. Chỉnh Pydantic và test/fixture trước; chạy `python -m unittest discover -s tests/contracts -v` với `PYTHONPATH=backend`.
3. Chạy `python tools/export_contract_schemas.py`; kiểm `--check` để phát hiện artifact cũ. JSON Schema chỉ biểu diễn được một phần validator liên trường, consumer vẫn phải tuân ngữ nghĩa này.
4. Routes FastAPI metadata ở SPEC-003 dùng Pydantic, sinh [OpenAPI](../../schemas/openapi-v0.1.0.json) và [TypeScript client](../../apps/desktop/src/generated/api.ts) bằng `python tools/export_api_client.py`; kiểm `--check` tương tự, không viết lại type frontend bằng tay.

Ví dụ cấu trúc ở [fixture workflow](../../tests/fixtures/contracts/workflow.json). Đây là tập payload tổng hợp đã qua suite contracts, chưa phải workflow có thể chạy: chỉ có một asset blue, không đủ sáu band của ModelSpec; hash/normalization/tolerance/coverage là số giả. Fixture không thay ảnh HLS/nhãn/checkpoint hoặc hồ sơ G0. [Fixture RPC](../../tests/fixtures/contracts/rpc-workflow.json) và [private context](../../tests/fixtures/contracts/worker-access-context.json) kiểm cấu trúc start/context, không thay handshake hoặc I/O thực.
