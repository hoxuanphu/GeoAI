# Bàn giao tài liệu Ubuntu — 10/11/2026

**Phạm vi:** phát triển tài liệu Ubuntu 22.04 LTS và Ubuntu 24.04 LTS theo yêu cầu người dùng; không triển khai Linux. **Trạng thái:** hoàn tất phạm vi tài liệu sau kiểm trực tiếp; kỹ thuật trong ADR-012 vẫn đề xuất, runtime Ubuntu chưa triển khai/kiểm.

## Đầu ra

- [ADR-012](../../adr/ADR-012-ubuntu-desktop.md): yêu cầu OS đã xác nhận, adapter/packaging còn đề xuất; quan hệ ADR-001/006/011 và phương án/điều kiện kiểm.
- [Kiến trúc Ubuntu](../../ubuntu-desktop-architecture.md): ba sơ đồ, supervisor/cgroup/UID owner, crash/recovery, FD/context/native I/O, publish/durability và XDG.
- [Guide môi trường và đóng gói](../../ubuntu-development-and-packaging.md): preflight, Python riêng, dependency/ABI, `.deb`, offline/upgrade/uninstall và nguồn upstream đã đối chiếu.
- [Ma trận UB-01–20](../../ubuntu-validation-matrix.md): ca kiểm hai LTS, task/dependency và các lớp bằng chứng; toàn bộ ca runtime vẫn chưa chạy.
- Đồng bộ nguồn tổng hợp/kiến trúc/plans, docs/indexes, SPEC-003/004/009 và [mốc 000.5](../../task-tracker.md). Giữ schema và G0–G4.

## Môi trường và cách kiểm

Thực hiện trên workspace Windows/PowerShell ngày 10/11/2026, múi giờ Asia/Bangkok. Baseline Git ban đầu sạch; lưu SHA-256 của các file được Git theo dõi ngoài `Artchitect/` trước sửa tại [protected-baseline.json](protected-baseline.json). Không cài thêm dependency.

Chạy từ root repo:

```powershell
python -X utf8 Artchitect/docs/evidence/ubuntu-2026-11-10/verify-docs.py
git diff --check
```

[Script kiểm](verify-docs.py) đọc UTF-8 strict; kiểm local inline/reference link và anchor, code fence/JSON và bảng Markdown; đối chiếu đủ 20 ID UB, ba diagram mới, liên kết ADR/spec/nguồn và hash file bảo vệ. Script không chạy Bash/preflight/apt/build/test Linux trong guide. [Kết quả trực tiếp và danh sách file kiểm](results.json) ghi status/exit code và số lượng quan sát được; các lần chạy lại sau cập nhật handoff dùng cùng script.

| Phép kiểm | Kết quả trong đợt tài liệu |
| --- | --- |
| UTF-8, file/link/anchor, fence và bảng Markdown | Pass theo `results.json`; chỉ kiểm file Markdown thay đổi/thêm trong đợt này |
| Ma trận và sơ đồ | Đủ UB-01–20 duy nhất, đúng thứ tự; ba diagram Ubuntu được kiểm dưới dạng text, chưa parse/render |
| `git diff --check` | Exit code 0 |
| Phạm vi và dữ liệu bảo vệ | 145 file ngoài `Artchitect/` trong inventory có SHA-256 trước/sau giống nhau; không thay mã/schema/test/config sản phẩm |

[Lượt kiểm đầu](initial-results.json) báo hai link thiếu do bộ kiểm tách sai reference destination có khoảng trắng trong `<...>`. Đã đối chiếu file đích có thật, sửa parser đọc đầy đủ destination và chạy lại pass; không sửa/xóa link tài liệu để tránh lỗi. Khi review nội dung, đã làm rõ instance mới không được dừng owner hợp lệ để giành quyền, manager phải xác nhận nhóm cũ dọn xong sau supervisor exit, và API health khác unit start thành công.

## Review nội dung và phần còn mở

Đối chiếu với architecture/contracts/IPC/resolver/ADR-011 và profile Prithvi: worker chỉ event/candidate, coordinator là đường ghi metadata, owner/writer/fencing/pin-lease độc lập; CPU và NVIDIA kiểm riêng, T=3 và decoder không đổi. Không thêm field schema, giá trị ngân sách, quality threshold, AOI hoặc deadline giả. Các lựa chọn x86_64, `.deb`, supervisor/user service và `openat2` được ghi là đề xuất của đợt tài liệu.

Phần implementation còn cần review/chốt ADR-012, namespace protocol và FD handoff cụ thể, executor hai LTS, resolve dependency/lock thật, adapter/process/I/O/SQLite integration và toàn bộ UB-01–20. G3 cần spec phát hành riêng cùng máy sạch/offline/upgrade; các hồ sơ G0/GIS/model/hardware/budget vẫn mở theo dependency. Không còn coi ADR/thiết kế là chưa có tài liệu, nhưng chúng chưa Accepted hoặc được nghiệm thu runtime.

## Giới hạn

Không có Mermaid CLI/parser sẵn trong probe (`mmdc` không có; package `apps/desktop/node_modules/mermaid` không tồn tại). Chỉ kiểm fence/loại sơ đồ/cấu trúc văn bản, **chưa parse/render Mermaid tự động hoặc kiểm bố cục ảnh**. Không suy cú pháp đúng từ số diagram.

Không chạy suite runtime vì chỉ thay tài liệu và công cụ kiểm tài liệu. Không có test/build/Cloud/Linux/desktop/WebKitGTK/DB/GIS/Prithvi/GPU/installer được thực hiện trong đợt này. Đọc tài liệu Tauri/systemd/XDG/man-pages và package index không là bằng chứng GeoAI chạy trên Ubuntu. Các báo cáo ngày trước và bằng chứng Windows giữ nguyên phạm vi lịch sử.
