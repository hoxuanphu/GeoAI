# Kế hoạch backend trước G0 — 08/11/2026

Yêu cầu: ghi lại thiếu sót/nguyên nhân và hoàn thiện trước những phần có thể. Thiết kế ràng buộc: SPEC-009/004, architecture, contracts, worker-resolver, importer-resolver-security và IPC hiện có. G0 vẫn chưa đạt; không thêm API/job nặng hoặc bật capability native/owner/writer/inference.

## Task và kết quả cần kiểm

1. Policy/importer: Pydantic policy/inventory + kiểm archive ZIP offline không ghi filesystem, kiểm tên Windows/duplicate/link/quota/deadline/cancel/hash; policy endpoint/redirect/DNS/stream thuần nếu đủ spec. Không gọi provider hoặc parser GIS, không activate pack/AssetRef.
2. Resolver: kiểm bytes context/hash và binding với trusted launch/project/owner/attempt/job/snapshot/budget; registry thuần bất biến/one-use/revoke, resolve ref allowlist/candidate scope. Không mở file/path hoặc giả quyền OS/native.
3. IPC: framing UTF-8/LF có giới hạn và strict JSON, encode/decode/correlation/error classification theo JSON-RPC. Kiểm partial/oversized/nonfinite/batch/method/params; chưa launch worker hoặc redirect native handles.
4. Job core: state transitions/idempotency intent digest/attempt fencing/cancel/retry/checkpoint compatibility thuần. Không thay SQLAlchemy/Alembic bằng DB khác; không nhận if trong bộ nhớ làm DB transaction hoặc publish bytes đã kiểm.
5. Review, chạy kiểm toàn bộ phần backend liên quan, sinh/check schema, inventory/hash và đồng bộ thiếu sót/spec/tracker/roadmap. Phần native/live/DB/model còn chờ được ghi riêng.

## Preflight và rulings

| Cặp/interface | Đối chiếu | Ruling |
| --- | --- | --- |
| Task 1 ↔ contracts/exporter | Pydantic canonical; policy limits phải explicit | Giữ draft 0.1.0, sửa fixture/docs/test/schema cùng task |
| Task 1 ↔ Task 2 | Tên/path metadata khác quyền native | Chỉ xử lý strings/bytes và IDs; không claim confinement/handle |
| Task 2 ↔ Task 3 | Start/context IDs/hash/budget phải khớp | Parse RPC không tự cấp quyền, resolver vẫn kiểm grant riêng |
| Task 2/3 ↔ Task 4 | Generation token khác idempotency/request ID | Logic thuần giúp kiểm điều kiện; DB/publish phải kiểm lại transaction khi tích hợp |
| Toàn bộ ↔ SPEC-003/G0 | Native/input còn thiếu | Các cơ chế thuần chạy fixture; không bật production dispatch hoặc đóng gate |
| Task 4 ↔ ADR-002 | SQLAlchemy/Alembic chưa có | Không tự đổi thiết kế DB; core thuần trước, DB còn chờ resolve và tích hợp |

Workspace chưa có Git; dùng baseline/hash, không init/commit hoặc worktree giả. TDD trước production, reviewer độc lập sau task. Các agent thực hiện tuần tự để tránh xung đột schema/shared files. Policy và budget test chỉ là fixture. Handoff không tuyên bố đạt IMP/NET/RES native hoặc toàn bộ SPEC-004/009 từ unit tests.

## Mở rộng theo yêu cầu 09/11/2026

Người dùng yêu cầu bỏ qua thiếu sót môi trường và tiếp tục gen đầy đủ code. Không thử cài toolchain/dependency thêm; thiếu môi trường chỉ chặn phép kiểm phụ thuộc nó, không chặn viết implementation và test. Các task 1–4 vẫn là foundation có review; tiếp sau đó triển khai adapter thật trong phạm vi pre-G0 được SPEC-003/004/009 cho phép. Không tự bỏ dependency dữ liệu/nghiệp vụ của SPEC-005/006/008, không đóng gate bằng code chưa chạy.

6. Repository SQLAlchemy/Alembic: schema, migration, SQLite WAL, intent/idempotency, attempt fencing/cancel/publication transaction, dependency leases và recovery/backup. Test dùng SQLite thật qua SQLAlchemy khi có dependency; thiếu dependency báo chưa chạy, không thay bằng sqlite3 repository khác.
7. Native Windows lifecycle: owner lock theo SID xuyên session, writer lock, Job Object và suspended process assignment/handle allowlist; native launcher/handoff và shutdown có deadline. Ghi rõ Rust build/cross-session harness chưa chạy; không bật capability dựa vào source code.
8. Worker process transport: bootstrap handle tin cậy, binary serialized protocol writer/native stdout redirection, bounded stdout/stderr readers, correlation, heartbeat/cancel trong khi handler bận, shutdown/terminate và kiểm process thật. Handler fixture chỉ chứng minh cơ chế, không giả model/GIS.
9. Storage I/O: handle-based Windows reads/staging/candidate identity, bounded archive extraction, hash verification, immutable publish/DB registration và reconcile. Dùng policy/registry đã kiểm; từ chối kiểu/nguồn chưa hỗ trợ. Không bật provider live hoặc parser GIS khi chưa có adapter/policy/đầu vào đủ.
10. Chạy các kiểm khả dụng, review cuối, đồng bộ trạng thái: phân biệt đã chạy pass, code đã viết/chưa chạy và đầu vào nghiệp vụ còn chờ. Lưu thiếu sót/nguyên nhân mới theo bằng chứng.

Ruling: code adapter có dependency chưa cài vẫn được triển khai và compile/syntax-check trong phạm vi công cụ có sẵn; không ghi test phụ thuộc dependency là pass hay xóa điều kiện nghiệm thu. Thứ tự 6–9 có thể điều chỉnh để tránh vòng import; architecture vẫn ràng buộc storage không import jobs.
