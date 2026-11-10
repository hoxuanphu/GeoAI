# Bàn giao đặc tả Ubuntu foundation — 10/11/2026

**Yêu cầu:** hoàn thiện spec trước khi gen code. **Trạng thái:** hoàn tất phạm vi đặc tả sau review và kiểm tài liệu; không triển khai runtime/schema hoặc chạy Linux trong đợt này. Mốc tài liệu SPEC-000/000.7 hoàn tất; các mốc triển khai 010.1–010.3 chưa bắt đầu.

## Đầu ra

- [SPEC-010](../../specs/010-ubuntu-foundation.md): target/phạm vi/dependency, file/interface, luồng fixture, lỗi, mốc và suite 010-T01–09.
- [Native profile v1](../../platforms/ubuntu/ubuntu-native-profile.md): namespace/unit, creator-bound socket, challenge/descriptor, FD kế thừa, pidfd stop, journal và cleanup/recovery.
- [Interface adapter](../../platforms/ubuntu/ubuntu-adapter-interfaces.md): root/reader/owner/process/guard contract, identity và snapshot Linux, stop-then-copy publish.
- Đồng bộ ADR-012, kiến trúc/nguồn/plans, contracts/resolver, SPEC-003/004/009, ma trận UB, indexes/roadmap/tracker; không tự đánh ADR Accepted hoặc UB pass.

## Review độc lập

Lượt đọc độc lập dùng fresh-context agent `spec010_builder_review`, vai trò Linux desktop/runtime engineer; chỉ đọc, không sửa file. Phạm vi là ba tài liệu spec/profile/interface và code guards/repository liên quan. Reviewer tìm thấy ba khoảng trống ảnh hưởng correctness:

| Finding | Sửa trong spec | Bằng chứng kiểm tương lai |
| --- | --- | --- |
| StopUnit(name) có race đổi invocation sau check | Cấm app stop theo tên; giữ supervisor pidfd, signal đúng process; ESRCH không fallback | 010-T05, UB-07/08 |
| Ledger mới ghi đè generation cũ trước DB reconcile | Journal giữ generation gắn project/root/owner/epoch/native identity; append trước claim, native observer kiểm OS lại, thiếu binding thì recovery có giới hạn rõ | 010-T04, UB-06/08/12 |
| UID + echo challenge không chứng minh đúng shell tạo unit | Trusted native wrapper truyền creator PID/start/boot không chứa secret; supervisor kiểm peer kernel identity đúng creator | 010-T03, UB-04/05 |

Reviewer đọc lại các sửa đổi và kết luận không còn khoảng trống correctness quan trọng trong phạm vi đó; chưa xác nhận implementation, hiệu năng hoặc Linux runtime. Self-review bổ sung deadline copy/delete, epoch max qua Job/Attempt/DependencyLease, tránh LOCK_UN trên FD chia sẻ và tách private ledger khỏi schema đã có.

## Kiểm tài liệu và giới hạn

Baseline worktree có thay đổi sẵn; [snapshot trước sửa](baseline.json) ghi SHA-256 của 416 file tracked/untracked cùng trạng thái Git ban đầu. Không dùng Git HEAD làm baseline thay thế các thay đổi có sẵn.

Lệnh kiểm: `python -X utf8 Artchitect/docs/evidence/spec010-2026-11-10/verify.py`, exit code 0; [script](verify.py) và [kết quả máy đọc](results.json). Kiểm 139 file Markdown toàn `Artchitect/` và README/AGENTS root: UTF-8 strict, liên kết cục bộ/anchor, fence, số cột bảng (bỏ qua dấu `|` trong code span) và 5 ví dụ JSON đều hợp lệ. Đủ 9 ID suite 010-T01–09 duy nhất, đúng thứ tự; 010.1–010.3 vẫn chưa đánh dấu hoàn tất. `git diff --check` exit code 0.

Đối chiếu hash xác nhận **332/332 file được bảo vệ không đổi**, gồm 145 file ngoài `Artchitect/` và 187 file bằng chứng có sẵn; không thêm file sản phẩm. Những file mới chỉ gồm ba tài liệu spec/profile/interface và hồ sơ kiểm của đợt này. Lần kiểm đầu phát hiện chỉ mục bằng chứng cũ đã bị thêm dòng; đã trả file đó về đúng hash baseline rồi kiểm lại đạt. Các hồ sơ/log/kết quả lịch sử được giữ nguyên.

Chưa parse/render Mermaid hoặc kiểm URL ngoài bằng script. Không chạy unittest sản phẩm, native build, Ubuntu/Cloud/WebKitGTK, SQLAlchemy/GIS/model/GPU/installer trong đợt spec. Các file/method/suite/ledger trong spec là deliverable triển khai tương lai; riêng ledger cần source Pydantic/registry/fixture/exporter trong task code trước sử dụng. Chỉ nghiệm thu phạm vi đặc tả, không đóng SPEC-010 implementation hoặc G0–G4.
