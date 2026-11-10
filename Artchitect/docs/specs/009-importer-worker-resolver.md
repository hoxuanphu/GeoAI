# SPEC-009 — Importer và worker resolver có phạm vi quyền rõ

**Trạng thái:** thực hiện một phần — typed context/launch packet, policy/grant registry, inherited-handle bootstrap, Windows resolver/I/O và bounded ZIP extraction đã có source và kiểm fixture. [Bàn giao 09/11/2026](../evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md), [kết quả kiểm](../evidence/backend-pre-g0-2026-11-08/final-results.json). Chưa có live provider/driver acceptance, DB integration còn skip và Rust/Tauri launcher chưa build; các mốc runtime toàn SPEC chưa hoàn tất.
**Mục tiêu:** worker fixture nhận ID và context hợp lệ để đọc đúng input, ghi đúng staging và gửi candidate; importer/provider từ chối các đường truy cập vượt policy bằng bằng chứng cụ thể.

**Đợt làm tiếp 08–09/11/2026:** đã triển khai policy/archive inventory, context/reference và các adapter bootstrap/I/O theo [kế hoạch](../evidence/backend-pre-g0-2026-11-08/plan.md). Windows tests dùng file/handle/process thật với dữ liệu tổng hợp; trạng thái toàn SPEC chỉ đóng khi đủ các ca I/O/native/process và security acceptance liên quan.

**Bằng chứng nền ngày 09/11/2026:** policy ZIP/endpoint/stream và grant registry metadata đã có; [review policy](../evidence/backend-pre-g0-2026-11-08/task-1-review.md), [báo cáo grants](../evidence/backend-pre-g0-2026-11-08/task-2-report.md), [review grants](../evidence/backend-pre-g0-2026-11-08/task-2-review.md). Kết quả nền 32 storage và 9 catalog tests chỉ kiểm logic thuần. Đợt mở rộng đã kiểm native handle/identity, managed/external reads, extraction/rollback và publisher bằng file thật; [báo cáo I/O](../evidence/backend-pre-g0-2026-11-08/task-9-report.md), [báo cáo bootstrap/transport](../evidence/backend-pre-g0-2026-11-08/task-8-report.md). Tổng suite storage hiện 52 pass/23 DB skip; integration 54 pass/2 DB skip. Không gọi provider thực; các mốc 009.1–009.3 vẫn chưa hoàn tất.

## Dependency, người phụ trách và phạm vi

Đọc [worker resolver](../worker-resolver.md), [ma trận security](../importer-resolver-security.md), [contracts](../contracts.md), [IPC](../ipc-protocol.md), ADR-002/009/011. Cần các kiểu dùng chung SPEC-001, bootstrap shell/session tối thiểu SPEC-003; việc dispatch/publish thực được tích hợp và nghiệm thu ở SPEC-004. SPEC-009 không phụ thuộc SPEC-004 đã hoàn tất: có thể dùng launcher/worker fixture để kiểm resolver trước, sau đó chạy lại tích hợp. Tránh vòng dependency giữa hai spec.

Backend/storage phụ trách registry/context/handle/candidate; GIS/data phụ trách format/driver/sidecar và provider adapter; native engineer phụ trách bootstrap/reparse/handle Windows; QA/security reviewer phụ trách ca âm và sentinel. Người cụ thể và policy thực được ghi trong hồ sơ khi nhận task; chưa có phân công nhân sự đã xác nhận. Có thể chạy ca tổng hợp/offline trước G0; quyền provider thật/quota/dataset cần đầu vào SPEC-002, không biến test live thành điều kiện mọi unit test.

## File và interface đích

| Deliverable dự kiến | Trách nhiệm |
| --- | --- |
| `backend/geoai/contracts/access.py` | Pydantic cho WorkerAccessContext/read entry/bootstrap values và import policy/record dùng chung; không chứa native I/O |
| `backend/geoai/storage/resolver.py` | Resolve ref/context, kiểm read/write scope và identity; không tạo API nhận path tự do |
| `backend/geoai/storage/importer.py` | Staging/extract/limits/inventory/register, rollback/cleanup; không kích hoạt pack trước kiểm |
| `backend/geoai/catalog/resolver.py` | Provider identity/endpoint policy, fetch/materialize có tổng deadline, quota và redaction |
| `backend/geoai/workers/bootstrap.py` | Handle descriptor tin cậy, allowlist môi trường và runtime paths trước native import |
| SPEC-001 `rpc.py`/exports/exporter/schema | Start có access_context_id/hash; schema sinh ra và fixture/test đồng bộ, chưa viết tay artifact |

Các tên file là đề xuất phạm vi triển khai, chưa tạo package rỗng. Resolver chỉ nhận ref ID + context đã xác minh từ caller tin cậy; trả handle/read descriptor hoặc staging descriptor nội bộ, không trả quyền ghi tùy ý cho UI. Importer trả AssetRef/inventory chỉ sau kiểm và đăng ký; provider resolver không gửi credential/signed URL sang worker. Không truyền ORM session qua IPC hoặc để worker đọc SQLite.

## Trình tự và acceptance

1. Hiện thực typed values, fixture draft và exporter checks liên quan cùng SPEC-001. Ghi version/profile; không giữ hai định nghĩa schema khác nhau ở docs/frontend.
2. Kiểm một managed input và một external registered input hợp lệ từ bootstrap/context đến worker fixture; thiếu context/hash hoặc project/attempt mismatch bị từ chối trước accepted.
3. Kiểm archive/path/driver/network theo từng ID trong ma trận. Policy/limit phải có trước xử lý; thiếu cấu hình là từ chối có lý do. Resolver không cấm mọi external input để đạt test âm.
4. Ghi staging riêng theo attempt; coordinator registry chỉ nhận candidate ID thuộc vùng được cấp. Tích hợp SPEC-004 kiểm cancel/retry/crash/lease/commit và candidate cross-project/cross-attempt.
5. Chạy Windows native/process cases, kiểm sentinel ngoài vùng ghi, redaction/log và cleanup sau timeout/thiếu đĩa/cancel; ghi phần chưa hỗ trợ, không fallback im lặng cho VRT/reparse/network.

## Test phải có khi triển khai

| Test dự kiến | Bao phủ |
| --- | --- |
| `tests/contracts/test_access_context.py` | Context/start schema, IDs/hash/version/unknown fields/budget, typed round-trip; không thay kiểm I/O |
| `tests/storage/test_importer_security.py` | IMP-01–11 bằng fixture archive/file nhỏ, ca dương và sentinel/hash ngoài staging |
| `tests/catalog/test_resolver_network_policy.py` | NET-01–06 bằng endpoint/DNS/redirect giả lập có kiểm soát, stream quota/deadline và credential redaction |
| `tests/integration/test_worker_access_context.py` | RES-01–08 với process/handle/file thật, bootstrap/replay/identity/candidate và owner recovery liên quan |
| SPEC-004 integration suite | Dispatch/publish/fencing/lease đúng khi resolver từ chối hoặc worker cũ còn sống; không chỉ mock if trạng thái |

Các tên suite ở bảng là đích acceptance, không phải toàn bộ đã được nghiệm thu. Kiểm hiện có nằm trong `tests/contracts/test_contract_extensions.py`, `tests/storage/test_{windows_io,worker_io,extraction,publisher_io}.py` và `tests/integration/test_{native_owner,native_process,worker_transport,job_recovery}.py`; policy/network logic có các suite riêng. [Bàn giao](../evidence/backend-pre-g0-2026-11-08/handoff-2026-11-09.md) ghi phạm vi file/handle/process đã chạy và DB/Rust/provider còn chờ; chưa bao phủ trọn IMP/NET/RES. Lệnh thực/OS/pass/skip/log nằm trong [kết quả kiểm](../evidence/backend-pre-g0-2026-11-08/final-results.json). Báo cáo nghiệm thu G1 dự kiến `Artchitect/docs/evidence/g1/`; không lưu secret/dữ liệu khách hàng. G1 cần bằng chứng SPEC-003/004/005/007/009; test security không chứng minh chất lượng Prithvi hay installer G3.
