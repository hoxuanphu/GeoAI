# Đối chiếu nguồn ảnh X và nhãn Y ngày 08/11/2026

**Task:** [SPEC-002](../specs/002-g0-evidence.md), đồng bộ đầu vào [SPEC-008](../specs/008-training-evaluation-model-pack.md). **Múi giờ:** Asia/Bangkok. **Phạm vi:** tài liệu; chưa đóng G0, chưa tiếp tục code.

## Nguồn yêu cầu và đánh giá

Đã đọc toàn bộ tệp đính kèm `Pasted text.txt` do người dùng cung cấp trong phiên này. Nội dung đề nghị cụ thể hóa nhóm 3 nguồn ảnh và nhóm 4 nhãn/kiểm định bằng tensor sáu band/đa thời gian, QA/TL metadata, ba loại nguồn nhãn và bốn kiểm soát thời gian/lưới/ignore/split. Ghi nhận yêu cầu và giới hạn tại [G0-D08](g0/decision-record.md); tệp đính kèm không được chép vào kho dự án.

| Nội dung cung cấp | Đánh giá và cách tiếp nhận |
| --- | --- |
| Cặp X–Y khớp pixel và thời gian | Đúng về yêu cầu căn chỉnh; với T=3 cần định nghĩa ngày/kỳ mục tiêu Y và kiểm biến động, không bắt mọi frame cùng ngày với một nhãn hoặc coi cùng năm là đủ |
| Sáu band S30, reflectance, QA/TL | Phù hợp profile hiện có; scale chỉ một lần theo product/adapter, QA riêng từng frame, Fmask không bảo đảm phát hiện mọi sương mù. Ngày TL cần hỗ trợ lịch năm nhuận và encoding theo revision, không giới hạn cứng 1–365 |
| T=1–4, chip 512 và Prithvi 1.0/2.0 | Không dùng làm profile chung. GeoAI giữ T=3/224 cho nghiệp vụ, T=1/224 cho spike; mọi shape/backbone khác cần kiểm riêng. Đã sửa dòng T=1 nghiệp vụ còn sót trong đề xuất nguồn và làm rõ shape ở plan 07 |
| Nhãn int8/uint8 có -1 | UInt8 không chứa -1. Giữ đề xuất Int16 hoặc mapping UInt8/255 ↔ -1 có test/metadata; dtype cuối chưa khóa |
| Weak, giải đoán và thực địa/chuyên ngành | Tiếp nhận phân vai weak cho warm-up/gợi ý sửa, validation/test cần tham chiếu độc lập có QC. Không suy bản đồ chính thức hoặc ảnh VHR nhìn được là nhãn đúng/quyền dùng đã có |
| Phủ kín 100%, 70–85%, >95%, 30% khó nhận diện, 300–500 chip | Chưa có bằng chứng áp dụng cho dự án. Không biến thành coverage, tỷ lệ ignore, chất lượng nhãn, số mẫu hoặc gate đã được duyệt |
| Khớp tuyệt đối lưới HLS gốc và mode/majority | Cần khớp grid phân tích đã chọn; qua tile/múi có thể warp về grid đích. Nearest/mode/majority hoặc rasterize theo policy; không nội suy liên tục mã lớp. Grid giống nhau chưa tự bảo đảm đăng ký địa lý nguồn đúng |
| Model tự bỏ qua -1 và split theo xã/huyện | Phải cấu hình loss/mask và metrics rõ, kiểm batch toàn ignore. Chia block/group trước chipping và kiểm overlap/cửa sổ T=3/buffer; khác địa giới chưa tự bảo đảm độc lập |

Không kiểm lại các URL/bài báo bên ngoài trong đợt này, không xác nhận số liệu dẫn nguồn. Trong nội dung cung cấp, nhãn link ghi WorldCover v200 nhưng URL trỏ v100; không kế thừa nhầm version đó, giữ taxonomy dùng [WorldCover v200](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200). Liên kết so sánh model hoặc model card repo bên thứ ba không tự là cấu hình chính thức cho GeoAI; model/profile tiếp tục theo revision đã ghi trong Prithvi profile.

## Tài liệu cập nhật

SPEC-002 có nhóm 3/4, quy tắc X–Y, bốn kiểm soát và bảng giao nhận/duyệt/bằng chứng dự kiến. SPEC-008, Prithvi profile và taxonomy tham chiếu policy này; decision record, roadmap và tracker ghi yêu cầu mới nhưng giữ các mốc G0 chưa hoàn tất. Đồng bộ đề xuất nguồn và plan 07; không thay yêu cầu Prithvi hoặc quyết định ADR đã xác nhận, không sửa schema/code/test/config.

## Kiểm tra

Đã chạy Python/PowerShell tại root GeoAI, đối chiếu inventory SHA-256 chụp trước sửa. Script kiểm tạm nằm ngoài workspace, không thêm mã kiểm/test vào dự án. Lệnh thực:

```powershell
python -X utf8 'C:/Users/phuhx1/AppData/Local/Temp/geoai-xy-labels-cll6ifob/verify_docs.py'
```

Kết quả trực tiếp: exit code 0, không phát hiện lỗi qua 73 Markdown, 606 liên kết nội bộ (83 có anchor), 191 bảng và 5 block JSON parse được; UTF-8/control/code fence đạt theo parser cấu trúc đơn giản. Đối chiếu đủ IDs lớp 0–6/-1, tám quyết định G0-D01–D08, bốn kiểm soát X–Y và 31 mốc tracker duy nhất; chỉ 000.1–000.3 đã checked. Các mục nhóm 3/4/giao nhận, target period, dtype/ignore, năm nhuận có trong SPEC-002. Ba đoạn shape/thời gian/quy tắc giao nhận của đề xuất nguồn và plan 07 khớp nhau.

Inventory trước/sau: sửa 9 Markdown, thêm báo cáo này, không xóa file; hash cả 8 file mã/test/fixture/config giữ nguyên. Hoàn tất phạm vi đối chiếu/cụ thể hóa tài liệu; giữ SPEC-002/008 chờ đầu vào và G0 chưa hoàn tất. Không chạy suite contracts, phép kiểm cặp raster/tensor/loss thực hoặc runtime/model; không render Markdown/Mermaid hay xác minh URL/số liệu bên ngoài. Không lấy kiểm Markdown làm bằng chứng dữ liệu/model đã đạt.

## Còn chờ

Nhóm 3/4 mới có quy tắc giao nhận: còn provider/collection/quyền và thử đọc band/QA thực; AOI/ngày/kỳ nhãn/lịch ba frame, nguồn nhãn/license/QC có duyệt, split/buffer/số mẫu/người thực hiện/người duyệt; CRS/tolerance, workload/hardware, gate/budget/điểm dừng. Không tạo dataset manifest/label-plan chứa dữ liệu giả, không chạy training hoặc tuyên bố hoàn tất 002.1–002.3/008.1.
