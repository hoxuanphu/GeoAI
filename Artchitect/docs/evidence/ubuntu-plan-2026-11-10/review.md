# Hồ sơ lập plan Ubuntu foundation — 10/11/2026

**Yêu cầu:** dùng Superpowers lập plan thật kỹ cho AI gen code có năng lực hạn chế, có thể làm từng bước. **Phạm vi:** tài liệu kế hoạch; chưa triển khai sản phẩm, chưa chạy test/build/native Ubuntu. **Trạng thái:** hoàn tất lập plan, self-review và kiểm tài liệu; đóng mốc tài liệu SPEC-000/000.8, không đóng mốc code.

## Đầu ra và cách dùng

[Plan tổng](../../superpowers/plans/2026-11-10-ubuntu-foundation.md) và 5 plan phần gồm 26 task; [catalog/handoff](../../superpowers/plans/2026-11-10-ubuntu-foundation/interfaces-and-handoff.md) giữ signatures, dependency, prompt giao AI và mẫu bằng chứng. Mỗi task có Files/Interfaces, bước test đỏ, implementation, kiểm green/regression và checkpoint/handoff; bước triển khai vẫn unchecked.

Skill áp dụng: Superpowers using-superpowers, writing-plans, brainstorming theo design/spec đã được người dùng cho hoàn thiện ở lượt trước, và verification-before-completion. Không mở lại vòng chọn kiến trúc vì user đã yêu cầu lập plan từ SPEC-010 vừa bàn giao. Writing-plans yêu cầu self-review, không dispatch subagent; phiên này không có implementer/reviewer agent hoặc runtime test được chạy.

## Self-review

| Trục | Đối chiếu/sửa trong plan |
| --- | --- |
| Spec coverage | G-01–G-16, bảng 010-T01–09 và mapping A–E; giữ scope UB-15–20/business/installer riêng |
| Step scan | Task có output kiểm được, không skeleton rỗng; hướng dẫn microcycle từng test/callable, không gen cả task một lần |
| Type consistency | Catalog thống nhất factory/owner/process/proof signatures, absolute deadline và Windows duration wrapper |
| Review Focus | UI10s/native30s, stop-before-publish token ordering, WAL epoch reader, partial FD cleanup, Unicode/alias có owner task/tests |
| Proportion | 5 phần theo subsystem cùng plan tổng/catalog; code block chủ yếu test/assertions, không chép nguyên implementation |

Các sửa từ self-review: tách low-level project lock C-02 khỏi usable WriterGuard/journal C-03 để mỗi task không còn test phụ thuộc task sau; epoch reader quan sát private coherent snapshot cả DB+WAL để không ghi sidecar project nguồn; driver integration E-01 chạy trong API child, không cấp owner cho process unittest bên ngoài. Test-only Rust feature/debug artifact tách khỏi production release; production không nhận fixture flags.

## Kiểm tài liệu

Baseline chụp 423 tracked/untracked files trước sửa, giữ dirty worktree có sẵn. [Baseline](baseline.json), [script](verify.py) và [kết quả](results.json) ghi cấu trúc/liên kết, task/suite coverage và SHA-256 bảo vệ source/schema/config/test/bằng chứng lịch sử. Không chạy lại checker lịch sử để ghi đè snapshot cũ.

Lệnh thực đã chạy: `python -X utf8 Artchitect/docs/evidence/ubuntu-plan-2026-11-10/verify.py`, exit code0, status pass/errors trống. Kiểm 148 file Markdown toàn corpus: UTF-8 strict, local links/anchors, table column counts bỏ qua dấu `|` trong code span, fence và 5 JSON examples. Parse AST thành công 15 Python snippets trong plan, không chạy chúng. Xác nhận 5 subplans, 26 ID task duy nhất/đúng thứ tự, 133 checkbox bước triển khai vẫn unchecked, đủ mapping010-T01–09 và mốc010.1–010.3 chưa tick. `git diff --check` exit code0.

**416/416 file được bảo vệ không đổi SHA-256.** Bảy file Markdown điều hướng/spec/tracker/roadmap được cập nhật theo allowlist; file mới chỉ plan Markdown và hồ sơ kiểm đợt này. Không thay source/config/schema/test/dependency hoặc hồ sơ bằng chứng lịch sử. Lần chạy đầu sửa lỗi cú pháp chính checker và tạo kết quả ban đầu; chạy lại sau khi artifacts đầy đủ đạt, không dùng kết quả lỗi làm bằng chứng hoàn tất.

## Giới hạn

Kiểm Markdown/local links/anchors/table/fence và code snippet syntax chỉ xác minh tài liệu, không chạy các test cases được mô tả trong plan. Không resolve package/crate, cài dependency, compile Rust/Tauri, chạy Linux/Cloud/WebKitGTK/SQLAlchemy/model/installer hoặc Mermaid rendering ở đợt này. Task A-01–E-05/010.1–010.3 chưa bắt đầu; ADR kỹ thuật và G0–G4 giữ trạng thái.
