# SPEC-004 — Job, attempt, IPC và publish local

**Trạng thái:** chưa triển khai. **Mục tiêu:** một job fixture chạy qua worker thật, hủy/retry/crash an toàn và không công bố output attempt cũ.

Input: contracts 0.1.0, environment SPEC-003, ADR-002/009. Output dự kiến: `jobs/{coordinator,protocol,publisher}.py`, `workers/main.py`, `storage/{repositories,models}.py`, Alembic initial migration, fixture worker và recovery tests. Worker fixture ghi artifact tổng hợp, không giả đã chạy Prithvi.

**Đợt làm tiếp 08–09/11/2026:** [kế hoạch backend trước G0](../evidence/backend-pre-g0-2026-11-08/plan.md) tách framing/classification và job-state core để làm bằng fixture trước native/DB. Chỉ phần đã kiểm mới được ghi hoàn tất; in-memory logic không thay SQLAlchemy/Alembic, transaction fencing hoặc filesystem publish.

Contracts phải được hoàn thiện/kiểm tra theo SPEC-001; các đường package trên nằm dưới `backend/geoai/`. Danh sách bảng/constraint/index và transaction boundary phải được review cùng initial migration, không tự coi bảng trong prose là migration đã chạy. Một publication/job, active attempt/token và chủ sở hữu lease phải được bảo vệ bằng transaction/constraint tương ứng, không chỉ if trong worker.

## Interface và bất biến

- Enqueue nhận JobSpec/idempotency key; persist queued rồi cấp attempt/generation token/lease khi nhận việc.
- Start/cancel/shutdown và events theo [protocol](../ipc-protocol.md), chỉ refs; reader/heartbeat không bị compute handler chặn.
- Worker ghi staging/candidate; publisher kiểm bytes/hash/grid/coverage/token/state, rename cùng volume rồi transaction recheck token/state/unique publication. API chỉ expose published record.
- SQLite một writer; checkpoint gắn input/model/config hash. Resume chỉ chunk/native capability phù hợp; idempotency không thay fencing.
- GC không xóa dependency có pin/lease; crash reconcile trước dọn. Không copy `.db` đang mở mà bỏ WAL.
- Nhận execution owner theo [ADR-011](../adr/ADR-011-local-execution-owner.md), writer lock/project rồi mới cấp attempt/token/dependency lease. Một job nặng hoạt động trong owner; heartbeat hết hạn không cho phép nhận lại compute khi worker cũ chưa dừng. Compute lease khác pin/checkpoint retention.
- Start/resolve theo [SPEC-009](009-importer-worker-resolver.md) và [worker resolver](../worker-resolver.md); bổ sung access context ID/hash, không để worker đọc DB/provider credential. Có thể dựng scheduler/fixture cùng bootstrap tối thiểu trước; nghiệm thu SPEC-004 cần resolver tích hợp đạt các ca liên quan, không đòi hai spec hoàn tất lẫn nhau mới bắt đầu.

## Acceptance/test phải có

`tests/integration/test_job_recovery.py`: cancel chạy, cancel muộn sau succeeded, retry/token cũ, crash worker/coordinator, resume hash không khớp, candidate thiếu file/sai checksum, race cancel/publish và crash sau rename trước commit. Test dùng process/temp directory/SQLite thật, không chỉ mock trạng thái.

`tests/integration/test_worker_transport.py`: partial read, UTF-8/LF, oversized/NaN, stderr đầy/pipe đóng, log native CRT/Win32, heartbeat khi handler bận và shutdown quá deadline. `tests/storage/test_migrations.py`: schema/constraint/index và restore/upgrade fixture cũ khi có version cũ.

Thêm các ca cùng idempotency key/khác payload bị conflict, mở hai instance cùng project không tạo hai writer, lease/GC tranh chấp, crash sau commit trước event UI và publication thiếu bytes sau restore. Checkpoint chỉ được nhận khi toàn bộ input/model/config/runtime cần thiết khớp; token cũ không được resume rồi publish dưới attempt mới nếu chưa được coordinator cấp quyền.

Thêm hai project khác nhau tranh CPU/GPU/đĩa, owner crash còn worker giữ model, đổi project trước giải phóng compute và ca GPU bị ứng dụng ngoài chiếm. Chạy RES-03/05/06/07 của [ma trận importer/resolver](../importer-resolver-security.md): stale context/replay, candidate khác project/attempt, reparse/file đổi bytes và worker cũ còn sống. Không cho phép checksum đúng thay ownership/fencing.

Chỉ hoàn tất khi chạy đủ trên Windows môi trường đích và ghi lệnh/log. Pydantic test không chứng minh transport, atomic publish hoặc chính sách khóa đã đúng. Không kéo PostgreSQL/server vào task local.
