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
