# SDD ledger — plan: Artchitect/docs/development-guide.md

Ngày: 08/11/2026, Asia/Bangkok. Yêu cầu hiện tại: thực thi code theo docs bằng Superpowers. Gate G0 chưa đạt.

## Rulings và preflight

- Ruling: yêu cầu code mới thay phạm vi chỉ tài liệu cũ; giữ nguyên dependency/gate — trực tiếp từ yêu cầu người dùng — không suy G0 đạt.
- Ruling: workspace không có Git; làm tại chỗ, không init repository hoặc tạo worktree giả — baseline inventory SHA-256 thay commit — không có rollback qua Git.
- Ruling: thiết kế và thứ tự đã có trong development-guide/specs; thực thi chúng, không thiết kế lại kiến trúc.

| Task/interface | Producer → consumer | Đối chiếu |
| --- | --- | --- |
| SPEC-001 nội bộ | Pydantic → exports → exporter/fixtures | Thiếu run/RPC/exports/exporter; baseline 30 tests thất bại, cần hoàn thiện |
| SPEC-001/009 | Start/context schema → resolver | Không tạo dependency vòng; định kiểu context trước, I/O/native sau |
| SPEC-001/003 | Contracts → API routes/client | Chỉ thực hiện khi bộ kiểu nền qua test |
| SPEC-003/009/004 | Launcher → context resolver → job/publish | Cần owner/native/toolchain; không gán schema test thành process acceptance |
| SPEC-005/008/006 | G0/input/profile/budget → model/training/business | Chờ đầu vào thực, không tạo dữ liệu hay gate giả |
| SPEC-007 | Shell/job/resolver → platform validation | Chỉ phần có dependency được kiểm; không đóng G1 từ foundation |

## Tiến độ

- Task 1: complete — SPEC-001 contracts, context types, RPC, exporter; parent chạy lại 51 tests PASS và schema --check PASS.
- Task 2: complete — review độc lập PASS, không có finding chặn; [report](task-2-review-report.md). Reviewer chạy thêm 30 probe ranh giới, tách với 51 test lưu trong suite.
- Task 3: complete trong phạm vi nền có thể kiểm — API/session/UI shell và scaffold Tauri; [triển khai](task-3-report.md), [review cuối PASS](final-review-report.md). SPEC-003 toàn task vẫn partial; native launcher/owner và tích hợp resolver/job chờ toolchain/harness.
- Task 4: complete — [bàn giao](handoff.md), lock npm, lượt kiểm agent chính toàn bộ pass; [88 source/config/docs hashes](final-inventory.json), [60 Markdown/447 links/16 anchors/5 JSON blocks](final-docs-check.json) không lỗi. Spec/roadmap/tracker/README đã đồng bộ; không có file baseline mất hoặc thay đổi test/fixture cũ ngoài task.

Baseline: [inventory](baseline-inventory.json), [contracts log](contracts-baseline.log). Không có runtime GIS/AI/solver.

Ruling: phần PHY chưa chọn profile có kiểu thì RunManifest không nhận physical refs/provenance; PhysicalModelSpec/JobSpec vẫn mô tả thiết kế — không cho dict tự do giả đủ bằng chứng — bổ sung profile cùng spec G4 sau này. Native resolver và quyền thực của context vẫn thuộc SPEC-009.

Ruling: thực hiện API/session/UI độc lập của SPEC-003 trong môi trường hiện có; native launcher/owner/Job Object chưa thể build/test do thiếu Rust/MSVC và harness xuyên session — không dựng launcher nhận job nặng chưa được kiểm — SPEC-003 giữ trạng thái chưa hoàn tất, SPEC-009/004 tích hợp chờ launcher.
