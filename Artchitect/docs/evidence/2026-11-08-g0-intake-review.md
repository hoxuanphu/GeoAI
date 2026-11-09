# Kiểm tài liệu ghi nhận yêu cầu G0 ngày 08/11/2026

**Task:** [SPEC-002](../specs/002-g0-evidence.md), ghi nhận yêu cầu từng phần. **Múi giờ:** Asia/Bangkok (UTC+07:00). **Giới hạn:** chỉ tài liệu; G0 chưa đạt, không tiếp tục code.

## Phạm vi và bằng chứng quyết định

[Decision record](g0/decision-record.md) giữ sáu phát biểu/lựa chọn trực tiếp của người dùng: mục tiêu nghiệp vụ đa độ phân giải; AOI/thời gian chưa rõ; mục tiêu nguồn toàn cầu và máy ít nhất 20 GB RAM/8 GB VRAM; chia đợt; ưu tiên nguồn mở; bốn chỉ số NDVI/EVI/NDMI/MNDWI trước. Hồ sơ phân biệt yêu cầu, cấu hình dự kiến và phần chưa biết; không suy quyền ảnh/nhãn hoặc tính đủ tài nguyên từ các câu trả lời.

Đồng bộ đề xuất nguồn trước, rồi các plans chịu ảnh hưởng: phạm vi (03), nguồn ảnh (06), GEO-01/EVI (07), hardware (12), lộ trình (15) và lịch sử (17); cập nhật kiến trúc hệ thống, architecture/profile/physical-models, SPEC-002/006, roadmap/index/tracker. Những plans khác giữ nguyên vì không đổi quyết định thuộc chủ đề của chúng. Đây là bổ sung baseline v1.4/kiến trúc 1.1, không đánh dấu một bản sản phẩm đã phát hành.

G0-D01–D05 ghi yêu cầu có xác nhận; mốc 002.1–002.3 còn thiếu đầu vào và giữ unchecked. Chưa thay quyết định đã chấp thuận tại ADR-008; chưa thêm ADR thay thế. Không tạo dataset/workload/coverage manifest giả hoặc file rỗng để mô phỏng hồ sơ đầy đủ.

## Kiểm tra

Chạy bộ kiểm read-only qua `python -X utf8 -` bằng PowerShell stdin: UTF-8/control, fence, cột bảng, JSON, liên kết nội bộ/anchor; kiểm ADR, đồng bộ nguồn/plans và các ID security acceptance. Kiểm riêng đợt này đối chiếu đoạn bổ sung G0/EVI, trạng thái tracker và SHA-256 inventory trước/sau. Parser Markdown đơn giản chỉ áp dụng cấu trúc hiện có; Mermaid chỉ kiểm fence/nội dung, chưa render.

Kết quả chạy và đọc output, exit code 0: 62 Markdown, 554 lượt liên kết nội bộ (75 lượt có anchor), 130 bảng, 5 block JSON parse được và 8 block Mermaid có fence/nội dung. Kiểm 11 ADR, 7 đoạn bổ sung review trước và 25 ID security acceptance vẫn đạt. Chín đối chiếu bổ sung G0/EVI giữa nguồn và sáu plans chịu ảnh hưởng đều khớp; đủ sáu phát biểu người dùng và năm ID G0-D01–D05. Tracker giữ đủ 31 mốc duy nhất, chỉ 000.1–000.3 đã checked; G0 vẫn chưa hoàn tất.

Kiểm tra đích ban đầu đòi đúng chuỗi “G0 chưa đạt” nên báo thiếu ở roadmap đang dùng “G0 chưa hoàn tất”; đã sửa điều kiện kiểm để nhận cả hai cách ghi tương đương, không đổi trạng thái gate. Đối chiếu SHA-256 xác nhận hai cẩm nang vẫn giống nhau. Inventory trước/sau: 16 Markdown được sửa và 2 Markdown mới; không xóa file, cả 8 file mã/test/fixture/config giữ nguyên hash. Bộ kiểm chỉ xác minh tài liệu, không xác nhận contracts, provider, model, solver, CRS hoặc Windows runtime đã chạy đúng.

## Phần chưa nghiệm thu

Không chạy test contracts/runtime/model; không tải ảnh/trọng số hoặc kiểm credential/license live. Chưa có AOI/thời gian, bộ lớp, nhãn/split, đường đọc band/QA thực, coverage 2–3 năm, máy tham chiếu/workload, CRS/tolerance, gate/budget hoặc người phụ trách thực. Bốn công thức chỉ số được đặc tả để triển khai và kiểm sau; chưa có output GeoAI thực. Chi tiết còn thiếu ở decision record và SPEC-002.
