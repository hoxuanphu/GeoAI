# Đối chiếu bộ tiêu chí nghiệm thu ngày 08/11/2026

**Task:** [SPEC-002](../specs/002-g0-evidence.md), liên quan SPEC-005/006/007/008. **Múi giờ:** Asia/Bangkok. **Phạm vi:** tài liệu; G0 chưa hoàn tất, chưa tiếp tục code.

## Nội dung tiếp nhận

Đã đọc toàn bộ tệp `Pasted text.txt` đính kèm trong yêu cầu hiện tại: per-class/global metrics, coverage/số quan sát, diện tích/CI/VN-2000, cấu hình/SLA GPU, cap fine-tune và campaign/điểm dừng. Giữ nguyên các giá trị tại [tiêu chí nghiệm thu](../acceptance-criteria.md), ghi [G0-D09](g0/decision-record.md). Phân biệt số ngưỡng do người dùng cung cấp với kết quả đo, protocol còn mở và các phương án đổi profile chưa duyệt. Không chép tệp đính kèm vào kho dự án.

## Đối chiếu kỹ thuật

| Nhóm | Kết luận và cách xử lý |
| --- | --- |
| Per-class/global | Giữ đủ bảy lớp, từng PA và UA, macro F1/mIoU/OA; kiểm đồng thời, không làm tròn trước so ngưỡng. F1 và IoU từ cùng confusion matrix có quan hệ toán học, không là hai kiểm định độc lập; thiếu lớp/mẫu không được bỏ khỏi macro để pass |
| Coverage | 10% cloud/shadow không bảo đảm 90% valid khi còn fill/ngoài footprint. Coverage union/composite khác giao mask đủ T=3. Giữ ngưỡng 97%/90%, tách nhánh 2 quan sát/tháng và 1/frame; phạm vi/chọn nhánh cần khóa. Pixel imputation không thành quan sát sạch thật |
| Recipe/model | Median 60–90 ngày, S30+L30, cửa sổ 512, FP16, Prithvi-EO-1.0 và DEM là phương án nêu trong tài liệu; không tự thay S30/T=3/224/Prithvi-EO-2.0. Profile/shape/precision thay cần kiểm lại train/evaluation/export/runtime tương ứng |
| Area/CI | Tách chênh lệch bản đồ-tham chiếu ≤8% với precision CI 95%; cần probability sample/trọng số, target ontology/kỳ/miền. CI ±5%/±10–15% còn khóa mẫu số/ngưỡng cụ thể; thiếu ngưỡng lớp 3, lớp 4 không đồng nhất mangrove. Không dùng test pixel counts làm chân lý diện tích toàn AOI |
| CRS | Ghi RMSE ≤15 m/diện tích ≤0,1%; cần điểm độc lập/operation/grid/phương pháp diện tích. Không chứng minh một bộ 7 tham số áp dụng mọi VN-2000, không dùng sai khác diện tích do biến dạng phép chiếu như lỗi datum |
| Máy/SLA/budget | Người dùng trả lời: “Máy training/benchmark GPU riêng; giữ mục tiêu desktop trước đó”. Máy mới 32 GB RAM/GPU16–24 GB/SSD500 GB dùng riêng; desktop giữ ít nhất 20 GB RAM/8 GB VRAM (G0-D10). SLA GPU ≤15 phút/tile không là SLA CPU. Giữ cap 4 GPU-giờ và min_delta 0,005/patience15; 50–100 epoch/500–1.000 chip không tự tương đương 4 giờ. 3–5 vòng, 2 tuần và chi phí cần kế hoạch cụ thể trước chạy |

Đối chiếu toán học trực tiếp: IoU=0,80 cho F1=0,888889; IoU=0,75 cho F1=0,857143; IoU=0,70 cho F1=0,823529; IoU=0,68 cho F1=0,809524; IoU=0,65 cho F1=0,787879; F1=0,72 đòi IoU≥0,5625. Giữ nguyên bảng yêu cầu, không thay các số đó thành một bộ gate khác. Các quan hệ này chỉ áp từng lớp cùng cách cộng/trọng số, không áp trực tiếp cho macro F1 và mIoU.

Không truy cập/kiểm lại URL hoặc các số liệu nghiên cứu bên ngoài trong đợt này. Không xác nhận bảng là “chuẩn nghiệm thu chung Việt Nam/quốc tế”, các tỷ lệ mây, benchmark model, quyền ảnh hoặc phép chuyển hợp pháp/đủ chính xác. Phạm vi kiểm là tài liệu workspace và toán học metric.

## Đồng bộ

Thêm tiêu chí nghiệm thu và nối SPEC-002/005/006/007/008, profile/domain rules/testing strategy, chỉ mục/roadmap/tracker/decision record. Cập nhật đề xuất nguồn và plans 07/12/15; sửa workload T=1 nghiệp vụ còn sót thành T=3 nghiệp vụ/T=1 spike trong nguồn và plan12. Giữ ADR-008 và các quyết định kiến trúc đã xác nhận; chưa thay CPU chính thức bằng GPU-only hoặc thêm DEM/model/profile mới. Các báo cáo cũ giữ nguyên số đo lịch sử.

## Kiểm tra

Chạy Python/PowerShell tại root GeoAI, đối chiếu inventory SHA-256 chụp đầu phiên; script kiểm tạm ngoài workspace, không thêm mã/test/config vào dự án. Lệnh thực:

```powershell
python -X utf8 'C:/Users/phuhx1/AppData/Local/Temp/geoai-acceptance-4qb5rcjc/verify_docs.py'
```

Kết quả trực tiếp sau sửa điều kiện kiểm: exit code 0, không phát hiện lỗi qua 75 Markdown, 641 liên kết nội bộ (84 có anchor), 196 bảng và 5 block JSON parse được; UTF-8/control/code fence đạt theo parser đơn giản. Kiểm đủ bảy hàng per-class với cả 28 giá trị F1/IoU/PA/UA đúng bảng cung cấp, các ngưỡng global/coverage/diện tích/tài nguyên và những điều kiện protocol quan trọng; đối chiếu đại số F1–IoU, nguồn/plans và xác nhận máy riêng không còn ghi chờ trả lời.

Đủ 10 quyết định G0-D01–D10, tám ID lớp 0–6/-1 và 31 mốc tracker duy nhất; chỉ 000.1–000.3 được checked. Inventory: sửa 16 Markdown, thêm hai Markdown (tiêu chí và báo cáo này), không xóa file; cả 8 file mã/test/fixture/config giữ nguyên hash. Lần kiểm đầu báo thiếu cụm “chưa có ngưỡng diện tích” vì tài liệu dùng “Chưa” viết hoa; đã sửa phép tìm kiểm tra không phân biệt hoa/thường, không sửa nội dung/ngưỡng để làm đạt.

Hoàn tất phạm vi ghi nhận/đối chiếu tài liệu. Chưa chạy contracts, model/evaluator, phép đo coverage/CI/CRS, training hoặc benchmark; không render Markdown/Mermaid hoặc xác minh nguồn web. Không dùng kiểm tài liệu để xác nhận ngưỡng khả thi hoặc gate runtime đạt.

## Việc còn chờ

Giữ 002.1–002.3 và các mốc triển khai chưa hoàn tất: còn input/nguồn/quyền/nhãn/AOI thực, sampling/support/metric/CI/coverage protocol, ngưỡng diện tích còn khoảng/thiếu lớp, máy thực/CPU SLO, operation/điểm chuẩn và campaign/chi phí/người duyệt. Phạm vi máy training/benchmark riêng đã được xác nhận; không thay yêu cầu desktop từ quyết định này. Không tạo benchmark/manifest/evaluation giả để đóng gate.
