# Kiểm tra bộ tài liệu AI/dev ngày 08/11/2026

**Task:** [SPEC-000](../specs/000-documentation-baseline.md). **Múi giờ ghi nhận:** Asia/Bangkok (UTC+07:00).
**Trạng thái:** đạt các phép kiểm tài liệu nêu dưới đây và hoàn tất phạm vi SPEC-000; không phải bằng chứng pass schema/runtime hoặc G0–G4.

## Phạm vi

Chỉ sửa Markdown theo yêu cầu tiếp tục viết tài liệu, chưa code. Cơ sở đề xuất v1.4/kiến trúc 1.1; không thay yêu cầu Prithvi từ bản đầu, gate tuyệt đối hoặc trạng thái G0.

Kiểm toàn bộ Markdown trong `Artchitect/docs/`, README/AGENTS ở root, `Artchitect/kien_truc_he_thong.md`, bản đề xuất tổng hợp và bộ `Artchitect/plans/`. Không kiểm lại nguồn chuyên gia hoặc các đề xuất lịch sử độc lập như tài liệu đã được chấp thuận.

## Phép kiểm thực hiện

- Đọc UTF-8 nghiêm ngặt, tìm ký tự thay thế/lỗi điều khiển; kiểm cặp code fence và số cột bảng Markdown.
- Resolve liên kết Markdown nội bộ/định nghĩa link và anchor tới file thực; path deliverable tương lai phải ghi bằng code span, không link tới file chưa tồn tại. Không gọi website để kết luận external URL còn hoạt động.
- Parse JSON trong các code block `json`; chỉ kiểm cú pháp, không khẳng định schema/ràng buộc liên record.
- Kiểm số lượng/chủ đề ADR-001–010 và mục bắt buộc; đối chiếu sổ quyết định trong bản tổng hợp, plans và index ADR.
- So SHA-256 các file không phải Markdown thuộc code/test/fixture/config với inventory đầu đợt; kiểm không thêm/xóa file loại này.
- Review thủ công nguồn thiết kế, trạng thái, gate, dependency, trường/đơn vị và race IPC; phân biệt rõ đặc tả với implementation.

## Kết quả

Kiểm tra bằng `python -X utf8 -`, chương trình kiểm nhận qua PowerShell here-string/stdin, chỉ dùng thư viện chuẩn `pathlib`, `re`, `json`, `urllib.parse`, `hashlib`; không thêm script triển khai vào workspace. Đã đọc output và exit code 0. Kiểm cấu trúc dùng parser đơn giản cho các link/fence/bảng đang có trong bộ này, không phải một trình phân tích CommonMark đầy đủ.

| Phép kiểm | Kết quả |
| --- | --- |
| Phạm vi Markdown | 53 file đọc UTF-8; không phát hiện ký tự thay thế/control bất thường |
| Liên kết nội bộ | 425 lượt resolve; không có file/anchor đích thiếu; 73 lượt có anchor |
| Bảng/code fence | 111 bảng khớp số cột; không có fence chưa đóng |
| Ví dụ JSON | 5 code block parse được, từ chối NaN/Infinity; chưa validate bằng Pydantic |
| Mermaid | 8 block không rỗng, fence đầy đủ; chưa kiểm render/syntax bằng engine Mermaid |
| ADR | 10 hồ sơ đủ sáu mục; mã và các dòng sổ quyết định nguồn/plans nhất quán sau chuẩn hóa link |
| Giữ nguyên mã | 8 file không phải Markdown có SHA-256 trước/sau trùng nhau; không thêm/xóa file loại này trong phạm vi kiểm kê |

Inventory giữ nguyên gồm `backend/geoai/__init__.py`, `backend/geoai/contracts/{common,geography,models}.py`, `tests/contracts/test_contracts.py`, `tests/fixtures/contracts/workflow.json`, `pyproject.toml`, `.gitignore`. Không kiểm kê lại các package đã cài trong `venv` hoặc cache Python như mã sản phẩm.

Review nội dung đã đối chiếu: Prithvi + decoder nghiệp vụ bắt buộc, RF chỉ đối chứng và gate tuyệt đối; G0 còn thiếu đầu vào; tách G1 technical/G2 business; affine đúng thứ tự; pin/availability tách snapshot bất biến; coordinator duy nhất publish và fencing/cancel race; review/representation/report có provenance; GEO-01 bản đầu và PHY chọn từng feature G4. Phát hiện comment affine sai và fixture một band chưa đủ workflow được ghi vào SPEC-001, giữ mã nguyên theo yêu cầu.

Bàn giao mới/bổ sung gồm hướng dẫn dev, ma trận kiểm tra, SPEC-000/007, chi tiết contracts/IPC, kiểm kê trạng thái và điều hướng ADR từ bản tổng hợp/kiến trúc/plans. Không thay thuật toán/feature hoặc tự phê duyệt ngưỡng; các task code chỉ có đặc tả.

## Giới hạn

Không viết/sửa mã, không chạy tiếp suite contracts/exporter/build/runtime. Các file run/RPC/public exports/exporter/schema sinh ra còn thiếu theo SPEC-001. Không kiểm render Mermaid bằng trình dựng, UI/WebView2, CRS/PROJ/GDAL, model/solver hoặc installer. Không có dữ liệu/nhãn/ngưỡng/ngân sách đã được duyệt để đóng G0, không có bằng chứng G1–G4. Hoàn tất tài liệu không làm các gate này đạt.

## Kiểm tra sau di chuyển tài liệu

Ngày 08/11/2026, theo yêu cầu người dùng, chuyển 31 file từ thư mục tài liệu ở root sang `Artchitect/docs/`; không giữ thư mục cũ hoặc tạo bản sao. Đã hiệu chỉnh 65 liên kết tương đối và các đường dẫn tài liệu trong AGENTS/README, đề xuất, kiến trúc, plans, specs và cây thư mục codebase.

Kiểm lại cùng phạm vi 53 file Markdown tại vị trí mới bằng bộ kiểm cấu trúc chạy trực tiếp qua `python -X utf8 -`, exit code 0: 425 liên kết nội bộ (73 lượt có anchor), 111 bảng, 5 block JSON và 10 hồ sơ ADR không có lỗi trong các phép kiểm đã nêu. Tám block Mermaid chỉ kiểm fence/nội dung không rỗng, chưa render. Đối chiếu inventory xác nhận đủ 31 file đã chuyển, thư mục cũ không còn, tám file mã/test/fixture/cấu hình giữ nguyên SHA-256 và không thêm/xóa file loại này.
