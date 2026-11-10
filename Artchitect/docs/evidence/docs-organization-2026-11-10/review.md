# Bàn giao sắp xếp tài liệu — 10/11/2026

**Phạm vi:** người dùng chọn nhóm tài liệu theo thư mục chủ đề. Công việc chỉ sắp xếp và điều hướng tài liệu; không thay yêu cầu, thiết kế, schema, mã sản phẩm hoặc trạng thái gate. **Trạng thái:** hoàn tất phạm vi sắp xếp tài liệu sau kiểm trực tiếp.

## Tổ chức

- `platforms/windows/` và `platforms/ubuntu/`: sơ đồ Windows; kiến trúc, đóng gói và ma trận kiểm Ubuntu.
- `domain/`: AOI, bộ lớp và tiêu chí nghiệm thu HLS.
- `guides/`: hướng dẫn phát triển và chiến lược kiểm thử; `project/`: thiếu sót/nguyên nhân.
- [Mục lục chính](../../README.md) có đường đọc theo công việc; các nhóm và [bằng chứng](../README.md) có chỉ mục riêng.
- 10 đường dẫn cũ có trang tương thích và anchor cũ, dẫn tới bản chính theo chủ đề. Các file mà `AGENTS.md` yêu cầu đọc trực tiếp vẫn tại đường dẫn bắt buộc, giữ nội dung.

[Danh sách ánh xạ](moves.json) ghi đường dẫn cũ/mới. Các thay đổi chưa commit tại đầu lượt được chụp hash trong `baseline.json`; không giả worktree ban đầu sạch. Các file evidence hiện có, snapshot JSON, log và [script kiểm Ubuntu](../ubuntu-2026-11-10/verify-docs.py) được giữ nguyên. Script cũ gắn với cấu trúc tại thời điểm đó; muốn tái hiện cần checkout tương ứng, còn cấu trúc hiện tại dùng script kiểm của đợt này.

## Kiểm và giới hạn

Trên Windows/PowerShell, ngày 10/11/2026, chạy từ root repo:

```powershell
python -X utf8 Artchitect/docs/evidence/docs-organization-2026-11-10/verify.py
```

[Kết quả kiểm](results.json) ghi pass, lệnh và số lượng quan sát được; script cũng chạy `git diff --check`. Kiểm UTF-8, file/link Markdown cục bộ, anchor và code fence trong `Artchitect/`, README và AGENTS; kiểm 17 đường dẫn tài liệu bắt buộc. Sau khi đảo phép đổi đường dẫn, hash của nội dung 10 tài liệu đã chuyển khớp baseline; 27 file Markdown khác chỉ thay liên kết. 295 file bảo vệ gồm mã/config/test và các hồ sơ evidence có trước giữ nguyên hash.

Lượt kiểm đầu phát hiện trang tương thích thừa dòng trống cuối file và bộ so sánh hash chưa xét đường dẫn có tiếng Việt được URL-encode. Đã sửa dòng cuối và bổ sung so sánh hai biểu diễn URL tương đương, sau đó chạy lại pass; không bỏ qua kiểm nội dung.

Phép kiểm không render Mermaid, không kiểm URL ngoài. Không chạy Linux, desktop, GIS, model hoặc benchmark trong đợt sắp xếp. Các khẳng định runtime và gate tiếp tục theo bằng chứng tương ứng; cấu trúc tài liệu mới không thay việc nghiệm thu.
