# Bộ lớp lớp phủ HLS 30 m — 7 lớp và mask ignore

**Ngày:** 08/11/2026. **Trạng thái:** người dùng đã chọn IDs/tên/phạm vi bảy lớp và T=3 cho model nghiệp vụ. Crosswalk/định nghĩa biên lớp dưới đây cần QC và khóa trong DatasetVersion trước training; chưa có nhãn/checkpoint/evaluation. Hồ sơ [G0](../evidence/g0/decision-record.md), [Prithvi profile](../prithvi-profile.md), [SPEC-008](../specs/008-training-evaluation-model-pack.md).

## Bảng nghiệp vụ được người dùng cung cấp

Các mô tả vật lý và dấu hiệu phổ là tiêu chí nghiệp vụ/giả thuyết nhận diện người dùng đưa ra. Không coi chúng là ngưỡng tự động đã kiểm định hoặc chiều cao/tán che được đo trực tiếp từ sáu band HLS.

| ID | Tên Việt / Anh | Đối tượng và tiêu chí người dùng đưa ra | Dấu hiệu nhận diện đề xuất trên HLS S30 | Nhãn mở đề xuất |
| --- | --- | --- | --- | --- |
| 0 | Mặt nước / Water Bodies | Sông, suối, hồ chứa, biển ven bờ, ao đầm có nước thường xuyên; tiêu chí người dùng nêu >9 tháng/năm | B8A/B11/B12 thấp; NDWI/MNDWI dương cao ổn định | ESA 80; JAXA #1, #12 |
| 1 | Cây thân gỗ / Rừng / Tree Cover / Forest | Rừng tự nhiên, rừng trồng, cây công nghiệp lâu năm khép tán như cao su/điều/cà phê; tán ≥10%, cao >5 m theo đề xuất người dùng | B8A cao, B04 thấp; NDVI/EVI cao qua mùa | ESA 10; JAXA #6, #8, #9, #10 |
| 2 | Đất canh tác hàng năm / Annual Cropland | Lúa 1–3 vụ, ngô, sắn, mía, rau màu; gieo/thu hoạch ít nhất một lần trong 12 tháng theo đề xuất người dùng | T=3 quan sát chu kỳ nước/bùn → phát triển thực vật → sau thu hoạch, nổi bật ở lúa | ESA 40; JAXA #3, #4 |
| 3 | Cây bụi & Trảng cỏ / Shrubland & Grassland | Cây bụi tái sinh, trảng cỏ, đồng cỏ chăn thả, cỏ đô thị; độ phủ ≥10% theo đề xuất người dùng | NDVI trung bình; SWIR tăng mùa khô do cỏ khô/lộ đất, khác chu kỳ ngập ruộng lúa | ESA 20, 30; JAXA #5 |
| 4 | Thực vật ngập nước / Rừng ngập mặn / Wetland & Mangroves | Rừng ngập mặn, rừng tràm ngập phèn, thực vật bán ngập cửa sông/đầm lầy | B8A có tín hiệu tán; B11/B12 chịu tác động nền ẩm/nước | ESA 90, 95; JAXA #11 |
| 5 | Đất xây dựng / Mặt không thấm / Built-up / Impervious | Khu dân cư, nhà xưởng, mái/bê tông, sân bay/cảng, đường lớn; người dùng nêu đường rộng ≥30 m | Phổ visible/SWIR và NDBI, biến thiên mùa thường nhỏ hơn cây trồng | ESA 50; JAXA #2 |
| 6 | Đất trống / Bãi bồi / Bare / Sparse Vegetation | Bãi cát/bồi, mỏ, đất san lấp chưa xây, đất bỏ hoang ít thực vật; độ phủ <10% theo đề xuất người dùng | B04/SWIR tương đối cao, NDVI thấp | ESA 60; JAXA #7 |
| -1 | Khuyết dữ liệu / Mây & Bóng mây / NoData / Cloud & Shadow | Mây, bóng mây, NoData hoặc ngoài AOI; không phải đối tượng lớp phủ | Mask band validity, HLS Fmask và AOI; ignore trong loss/evaluation | Mask từ QA, không có nhãn lớp dự đoán |

NDWI/NDBI trong bảng là dấu hiệu tham khảo do người dùng nêu, chưa bổ sung chúng vào bộ chỉ số đầu ra đã chốt NDVI/EVI/NDMI/MNDWI. Phải khóa công thức/phiên bản trước khi dùng; tên NDWI có nhiều biến thể. MNDWI dương hoặc NDBI dương không tự là luật phân loại đúng cho mọi vùng/mùa.

## Ngữ nghĩa cần giữ để dữ liệu không mâu thuẫn

- Lớp 1 là **tree cover có thể gồm rừng và cây lâu năm**, không là kết luận rừng theo pháp luật/kiểm kê. HLS 30 m không trực tiếp chứng minh chiều cao >5 m hay độ che phủ tán; cần dữ liệu tham chiếu phù hợp. Các ngưỡng ≥10%, >5 m và >9 tháng trong bảng là đề xuất người dùng, chưa xác nhận là trích nguyên văn tương đương ở cả WorldCover và JAXA.
- Rừng rụng lá/cao su có mùa rụng lá; NDVI cao ổn định không là điều kiện bắt buộc cho mọi pixel lớp 1. Mẫu hình ruộng lúa không áp cho mọi cây trồng hàng năm; mía/sắn có chu kỳ dài, cần quy tắc cửa sổ 12 tháng, vụ chuyển năm và bỏ hóa trước khóa nhãn.
- Đất sau thu hoạch thuộc đơn vị canh tác của kỳ tham chiếu không được tự đổi sang lớp 6 chỉ vì một ảnh NDVI thấp. Cây bụi/cỏ, đất trống và thửa canh tác cần ontology theo kỳ thời gian, không chỉ ngưỡng tức thời.
- Lớp 4 là thành phần bản đồ lớp phủ bảy lớp ngay đợt đầu. Workflow giám sát đất ngập nước/ngập lụt chuyên biệt vẫn ở đợt sau. Tán rừng có thể che tín hiệu nước phía dưới; SWIR thấp không tự chứng minh rừng bị ngập. Rừng tràm không có crosswalk mở đầy đủ chỉ từ ESA 90/95 hoặc JAXA #11.
- Đường rộng ≥30 m là đối tượng người dùng muốn nhận diện, không phải bảo đảm mọi đường như vậy có pixel thuần/được phát hiện. Pixel HLS 30 m hỗn hợp cần quy tắc dominance/purity và QC, chưa tự đặt tỷ lệ chấp nhận.

Đề xuất quy tắc loại trừ để review nhãn: thực vật ngập nước được xác nhận thuộc lớp 4 thay vì lớp 1/3; mặt nước không có thảm thực vật chi phối thuộc lớp 0; cây thân gỗ/cây lâu năm thuộc lớp 1 thay vì 2; thửa canh tác xét cả kỳ tham chiếu trước lớp 6. Đây là quy tắc vận hành đề xuất, cần người duyệt nhãn khóa cùng DatasetVersion; không áp thứ tự ghi đè theo mã ID hay theo mức SWIR đơn lẻ. Thiếu bằng chứng, nhãn xung đột hoặc lớp ngoài ontology phải để ignore/pending review, không ép về lớp gần nhất.

## Crosswalk nguồn mở có phiên bản

Đã đối chiếu tên/mã WorldCover 2021 v200 và JAXA **2020VNM_v23.09** ngày 08/11/2026. JAXA v21.09 là bộ sản phẩm khác, có cấu trúc lớp khác; không dùng mã dưới đây cho mọi bản JAXA. Bản đồ mở là nhãn tham khảo/weak labels có sai số, không tự thành ground truth độc lập.

| Lớp GeoAI | ESA WorldCover 2021 v200 | JAXA Vietnam 2020 v23.09 | Điều kiện chuyển nhãn |
| --- | --- | --- | --- |
| 0 | 80 Permanent water bodies | #1 Water; #12 Aquaculture có điều kiện | Ao nuôi có thể tháo cạn/luân canh; chỉ chuyển #12 khi đáp ứng định nghĩa mặt nước của kỳ tham chiếu, còn lại review/ignore |
| 1 | 10 Tree cover | #6 Woody Crops/Orchards; #8 Evergreen Forest; #9 Deciduous Forest; #10 Plantation Forest | Không suy tất cả là rừng pháp lý; điều kiện chiều cao/tán và wetland phải đối chiếu riêng |
| 2 | 40 Cropland | #3 Rice; #4 Other Crops | Xác nhận canh tác hàng năm và kỳ tham chiếu, không coi mọi nhãn crops chắc chắn đáp ứng quy tắc 12 tháng |
| 3 | 20 Shrubland; 30 Grassland | #5 Grass/Shrub | Loại trừ thửa canh tác tạm bỏ hóa và thực vật ngập nước đã xác nhận |
| 4 | 90 Herbaceous wetland; 95 Mangroves | #11 Mangrove Forest | Các mã này chưa phủ hết rừng tràm/wetland có cây gỗ; cần nhãn bổ sung độc lập |
| 5 | 50 Built-up | #2 Urban/Built-up | QC hỗn hợp và khác thời điểm; không mặc định toàn bộ ô “urban” là bề mặt không thấm thuần |
| 6 | 60 Bare / sparse vegetation | #7 Barren | Kiểm mùa/kỳ canh tác và bãi bồi/nước biến động |
| ignore | 70 Snow and ice; 100 Moss and lichen; NoData/mã lạ | NoData/mã lạ hoặc lớp không tương thích | Giữ mask/nguồn lý do, không chuyển thành lớp 0/6 |

WorldCover 2020 v100/2021 v200, JAXA 2020 và ảnh HLS năm khác không được ghép nhãn tự động mà bỏ qua biến động. Ghi source/year/version/hash/license và kết quả QC cho từng vùng. Căn lưới 10 m → HLS 30 m dùng categorical nearest/mode hoặc aggregation theo policy đã khóa; không bilinear mã lớp. Tính purity/hỗn hợp, alignment và ranh lớp trên grid đích; ngưỡng purity chưa được chốt, không biến đa số pixel thành chân lý.

Không dùng cùng WorldCover/JAXA đã tạo train labels làm test truth rồi công bố độ chính xác độc lập. Nhãn đánh giá cần xác nhận từ ảnh/khảo sát/nguồn độc lập phù hợp thời gian, giữ split theo vùng/thời gian trước chipping và kiểm cả nguồn sinh nhãn chung. Đồng thuận giữa hai bản đồ mở cũng chưa thay ground truth.

Vai trò nguồn nhãn, quy tắc cặp mẫu X–Y, kỳ tham chiếu và bằng chứng giao nhận theo [nhóm 3/4 SPEC-002](../specs/002-g0-evidence.md#nhóm-4--nhãn-y-nguồn-tham-chiếu-và-split). Weak labels nguyên bản giới hạn cho warm-up train hoặc gợi ý sửa; nguồn giải đoán/thực địa cũng phải có QC/người duyệt và quyền dùng. Pixel bị bỏ vì nhãn không chắc chắn phải có lý do và báo tỷ lệ theo lớp/vùng; không loại mọi biên để làm đẹp điểm kiểm định.

## Ignore, Fmask và raster nhãn

Bảy lớp học là IDs **0–6**, head có 7 kênh logits cho bản đồ mục tiêu; `-1` là `ignore_index` của nhãn training, không phải kênh thứ tám. Lớp 0 là nước hợp lệ, không phải background/NoData. Đề xuất lưu raster phân loại/nhãn theo signed Int16 để biểu diễn 0–6 và -1 trực tiếp; nếu encoder/export dùng UInt8/255 thì phải có mapping round-trip và metadata NoData rõ, không ghi -1 vào UInt8. Dtype/mapping cuối cần khóa trong profile và test, không đổi schema/code ở đợt tài liệu này.

HLS S30 v2 có Fmask bit 1 cloud, bit 2 adjacent cloud/shadow, bit 3 shadow, bit 4 snow/ice, bit 5 water; bits 6–7 aerosol; bit 0 được catalog ghi reserved/unused. Đọc theo đúng product/provider version và nhận diện fill trước bit decoding. **Không mask bit 5 chỉ vì khác 0**, vì như vậy xóa lớp nước; không dùng toàn byte Fmask khác 0 như cloud mask. Policy aerosol/adjacency/snow/fill cụ thể phải khóa theo profile, không tự đặt threshold hoặc dùng Fmask water bit làm nhãn test độc lập.

Mask cuối còn gồm band validity, ngoài footprint/AOI, thiếu frame hợp lệ theo policy T=3 và label ignore. Fmask không biểu diễn hết mọi mây sót hoặc mọi pixel ngoài AOI; QA chỉ giảm rủi ro, cần QC. Coverage quan sát tính từ ảnh/QA độc lập với coverage nhãn; thiếu nhãn không có nghĩa thiếu ảnh. Loss/metrics phân loại bỏ nhãn -1, báo số mẫu valid/ignored theo lớp; vùng ảnh invalid không tính diện tích phân loại và không tự thành nước. Mỗi chỉ số phổ có valid mask theo band/công thức, không mặc định mask training chính là mask thống kê chỉ số.

## Profile thời gian đã xác nhận

Bảng người dùng cung cấp nêu “T=3 mốc” để nhận diện chu kỳ cây trồng; tài liệu áp profile đa thời gian này cho model bảy lớp. T=1 giữ cho spike kỹ thuật theo baseline hiện có. Tensor nghiệp vụ dự kiến `B × 6 × 3 × 224 × 224`, metadata ngày/tọa độ đúng từng frame; T=1 chỉ dùng kiểm cơ chế/export sơ bộ. Cần thử positional embeddings/temporal aggregation/decoder, fine-tune và export T=3 riêng, không coi checkpoint pretrain 4 frame hoặc benchmark T=1 đã chứng minh T=3 chạy đúng.

Ba frame là ba thời điểm quan sát thật có thứ tự thời gian trên cùng grid, không lặp một ảnh cho đủ shape. Chưa chốt lịch theo vùng/vụ, khoảng cách frame, single-date/composite policy, valid observations tối thiểu theo pixel và fallback. Thiếu dữ liệu phải chặn/báo thiếu hoặc dùng profile thay thế đã được duyệt/kiểm, không âm thầm hạ T=1 rồi công bố kết quả T=3. Có ba ảnh không đủ để chứng minh nước >9 tháng/năm; tiêu chí dài hạn cần chuỗi bổ trợ/nhãn theo kỳ đủ dài. Mỗi frame composite nếu được chọn cần recipe/source dates và metadata policy được model chấp nhận.

## Nguồn đã đọc và giới hạn kiểm chứng

- [ESA WorldCover data access](https://esa-worldcover.org/en/data-access): năm/version, link manual và CC-BY-4.0/attribution; [catalog WorldCover v200](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200): tên/mã 11 lớp. Chưa đọc toàn bộ PDF manual để xác nhận từng ngưỡng vật lý trong bảng người dùng.
- [JAXA Vietnam 2020 v23.09](https://www.eorc.jaxa.jp/ALOS/en/dataset/lulc/lulc_vnm_v2309_e.htm): 12 lớp, 10 m, mainland Vietnam và năm tham chiếu 2020; [v21.09](https://www.eorc.jaxa.jp/ALOS/en/dataset/lulc/lulc_vnm_v2109_e.htm) là sản phẩm khác. Phạm vi này không là nhãn toàn thế giới.
- [JAXA download/data use](https://www.eorc.jaxa.jp/ALOS/en/dataset/lulc_e.htm): cần đăng ký; trang ghi miễn phí cho mục đích phi thương mại và yêu cầu liên hệ cho mục đích thương mại. Chưa có xác nhận quyền sử dụng thực tế của dự án, không mặc định miễn phí thương mại/phân phối lại.
- [HLS S30 v002 catalog](https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSS30_v002): band/Fmask bit table. Website HLS NASA trả HTTP 403 trong lần truy cập, nên không tuyên bố đã đọc hướng dẫn NASA trực tiếp trong đợt này. Catalog chỉ xác minh tài liệu, không là live asset-read test.

Chưa tải raster nhãn/ảnh/trọng số hoặc đo quality gate. Bảng user cung cấp chưa kèm tài liệu cụ thể cho “HLS Seasonality/Paddy Rice Mapping/Mangrove Study”; các cụm này chưa là trích dẫn đã xác minh. Việc kế thừa bộ lớp không chứng minh các mô tả phổ là quy luật định lượng hoặc model đã đạt từng lớp.

[Báo cáo đồng bộ AOI/bộ lớp](../evidence/2026-11-08-aoi-taxonomy-review.md) ghi kiểm tài liệu hiện tại; đợt này không kiểm lại nguồn web, license hoặc raster thực. Các đối chiếu nguồn nêu trên là ghi nhận đã có trong baseline.
