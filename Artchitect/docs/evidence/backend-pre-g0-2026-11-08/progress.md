# SDD ledger — plan: Artchitect/docs/evidence/backend-pre-g0-2026-11-08/plan.md

- Task 1: in_progress — policy/archive inventory và endpoint/stream logic thuần; agent import_policy, TDD. Baseline 55 contracts +14 integration +2 architecture pass.
- Task 2: pending — context/grant/reference/candidate scope thuần.
- Task 3: pending — IPC framing và classification.
- Task 4: pending — job state/idempotency/fencing/checkpoint rules thuần.
- Task 5: pending — review/verification/docs/handoff.

Ruling: tiếp tục trong workspace không Git, baseline source/hash và suite trước sửa được lưu cùng folder. Không lặp lại foundation đã hoàn tất ở codegen-2026-11-08. Chỉ owner/native/DB/live/model acceptance thực sự thiếu dependency mới ghi chờ; logic thuần đủ spec sẽ được triển khai.

Task1 review round1 (09/11/2026): reviewer kiểm lại 57 contracts/15 storage/9 catalog/2 architecture và artifacts pass, nhưng probe tìm reserved-device aliases và ZIP envelope (prefix/concat/trailing/EOCD metadata) còn lọt. Đã giao implementer viết regression RED và sửa; chưa ghi Task1 hoàn tất. [Report triển khai](task-1-report.md); native/transport/extraction không thuộc kết luận unit tests.
