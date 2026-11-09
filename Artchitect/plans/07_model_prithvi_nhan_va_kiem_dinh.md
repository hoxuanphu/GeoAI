# Model Prithvi, mô hình toán–vật lý, nhãn và kiểm định

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Prithvi + decoder, profile HLS, mô hình toán–vật lý, dữ liệu nhãn/hiệu chuẩn, độ bất định và quality gate.

<a id="muc-8"></a>

## 8. Chiến lược model, dữ liệu nhãn và kiểm định

<a id="muc-8-1"></a>

### 8.1. Chọn phương pháp theo bài toán

| Bài toán | Baseline | Model tích hợp hoặc hướng mở rộng |
| --- | --- | --- |
| Lớp phủ/diện tích | Chỉ số phổ + RF hoặc boosting | **Prithvi-EO-2.0 + decoder phân đoạn từ bản đầu**; cùng fixture và bộ lớp để đối chứng |
| Phát hiện công trình/vật thể | Detector nhỏ phù hợp GSD | OBB khi hướng/góc xoay là cần thiết; instance khi cần tách đối tượng |
| Biến động | Đồng đăng ký + sai khác/chỉ số | Siamese/temporal model khi giảm báo động giả |
| Chuỗi thời gian | Thống kê mùa vụ, smoothing, change point | Encoder thời gian xử lý được dữ liệu thiếu |
| Sinh khối/nước/tham số vật lý | PROSAIL, FAO-56, SCS-CN/HAND, RUSLE hoặc allometry theo đúng đại lượng và dữ liệu tại [mục 8.6](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-6) | SEBAL, thủy lực 2D hoặc model lai với ML khi có đủ dữ liệu hiệu chuẩn/kiểm định; triển khai từng feature G4 |
| Phân tích đối tượng GIS | Segmentation/OBIA + quy tắc hình học, kết cấu và quan hệ | Kết hợp AI khi cải thiện chỉ tiêu nghiệp vụ |

**Prithvi-EO-2.0 là thành phần bắt buộc của bản đầu.** TerraMind và các model khác trong cẩm nang tiếp tục là ứng viên mở rộng. Tích hợp Prithvi không đồng nghĩa nó đã tốt hơn baseline trên dữ liệu địa phương; phải công bố kết quả so sánh và giới hạn áp dụng. Nghiệm thu dựa trên ngưỡng tuyệt đối của feature; baseline là đối chứng, không bắt buộc Prithvi thắng. Nếu chưa đạt quality gate thì xử lý theo quy tắc dừng ở [mục 8.5](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-5), không âm thầm thay bằng RF rồi ghi đã nghiệm thu Prithvi.

<a id="muc-8-2"></a>

### 8.2. Hồ sơ Prithvi-EO-2.0 trong bản đầu

| Nội dung | Lựa chọn thiết kế và điều kiện |
| --- | --- |
| Backbone tham chiếu | **Prithvi-EO-2.0-300M-TL**, bản có encoding thời gian và vị trí. Model card công bố Apache-2.0 [P1]. Đây là lựa chọn khởi đầu, chưa phải cam kết đạt tốc độ CPU; biến thể nhỏ hơn trong cùng họ chỉ thay sau kiểm chứng và ghi quyết định tại G1 |
| Ứng viên CPU | **Prithvi-EO-2.0-100M-TL** và **Prithvi-EO-2.0-tiny-TL (5M)** có repository chính thức [P6], [P7]. G0 lập danh sách, G1 sàng lọc kỹ thuật cùng decoder phù hợp từng backbone; model phát hành phải qua kiểm định nghiệp vụ. Số tham số không thay benchmark toàn pipeline; không suy tốc độ hoặc chất lượng GeoAI từ tỷ lệ 600M/5M |
| Ứng viên không TL | **Prithvi-EO-2.0-300M** có config không encoding tọa độ/thời gian [P8]. Chỉ bỏ yêu cầu metadata làm đầu vào encoding của model; vẫn giữ ngày/scene, CRS, QA và recipe composite trong provenance. Lợi ích TL/non-TL với bộ lớp địa phương phải đo, chưa thay mặc định 300M-TL |
| Nguồn đã đối chiếu | `ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL`, revision `63adbd39c271da4c42f447e69b1a7c91a338cdc9`. Đã đọc model card/config; chưa tải trọng số hoặc chạy benchmark [P1], [P2] |
| Mô hình nghiệp vụ | Encoder Prithvi + **UPerNet decoder/head phân đoạn** theo hướng tích hợp TerraTorch [P3]. Huấn luyện/tinh chỉnh bên ngoài desktop; có thể bắt đầu đóng băng encoder, chỉ mở thêm tham số nếu validation chứng minh cần |
| Đầu ra | Raster nhãn theo class schema, xác suất khi cần, QA/coverage; vector/thống kê là bước hậu xử lý. Trọng số MAE nền và demo reconstruction không thay thế decoder/head đã huấn luyện |
| Profile dữ liệu đầu | HLS S30 v2, surface reflectance ở 30 m, sáu kênh đúng nghĩa phổ; HLS L30 chỉ thêm khi mapping và QA đã kiểm tra [P4], [P5] |
| Band order | **Blue, Green, Red, Narrow NIR, SWIR1, SWIR2**. Tên chuẩn hóa HLS S30: `B02, B03, B04, B8A, B11, B12`; HLS L30: `B02, B03, B04, B05, B06, B07`. Adapter ánh xạ alias của provider, ví dụ `B2` tương ứng `B02` trong catalog Earth Engine. Không dùng tên `B05` như một ý nghĩa phổ chung cho cả hai sản phẩm |
| Tensor/không gian | Spike kỹ thuật `B × 6 × 1 × 224 × 224`; nghiệp vụ bảy lớp `B × 6 × 3 × 224 × 224`; patch không gian 16 × 16 theo config nền [P2]. Các chiều kênh/thời gian/không gian cố định khi export ONNX; batch 1 là điểm khởi đầu, chỉ dùng batch động hoặc batch khác sau kiểm chứng runtime/RAM. Padding, overlap, decoder upsampling và phép đưa về GridSpec phải có fixture; không resize toàn bộ AOI về 224 × 224 |
| Chiều thời gian | Spike kỹ thuật T=1; model nghiệp vụ bảy lớp dùng **T=3** với ba quan sát thật, cần fine-tune/kiểm định/export riêng. Config nền dùng 4 frame; không lặp một ảnh thành bốn quan sát giả |
| Metadata TL | Lấy acquisition date và tâm cửa sổ theo WGS84 từ metadata đã xác thực; chuyển thành encoding đúng phiên bản model. Không suy ngày/CRS chỉ từ tên file; thiếu metadata thì chặn profile TL này hoặc dùng profile thiếu metadata đã được huấn luyện/kiểm định riêng. Upstream có cơ chế bỏ metadata khi pretrain [P1], nhưng không tự chứng minh profile downstream thiếu metadata hoặc composite đạt chất lượng |
| Normalization | Chuẩn hóa scale/offset về đơn vị thống nhất với mean/std của checkpoint và quá trình fine-tune. Config nền ghi thống kê cỡ DN; nếu dùng reflectance đã scale 0,0001 phải đổi mean/std tương ứng. Ghi các hằng số thực dùng trong ModelSpec; không áp scale hai lần hoặc dùng display stretch để suy luận |
| QA và composite | Loại NoData, mây/bóng mây theo profile; quy định giá trị điền và valid mask giống khi train, loại pixel không hợp lệ khỏi loss/metrics/output. Bản đầu ưu tiên ảnh/ngày xác định; composite nhiều ngày chỉ được dùng nếu profile model quy định ngữ nghĩa thời gian, không gán một ngày giả cho TL |
| Runtime và license | PyTorch/TerraTorch làm đường tham chiếu; thử export toàn bộ encoder + decoder sang ONNX. Model pack chỉ chứa thành phần inference cần thiết, kèm license/notice của backbone, decoder, trọng số và dữ liệu huấn luyện theo điều kiện tương ứng |

Sáu kênh quang học không được thay bằng SAR VV/VH, DEM hoặc RGB lặp kênh. Sentinel-2 L2A, ảnh độ phân giải khác hoặc kênh thiếu phải qua một profile adaptation có dữ liệu huấn luyện/kiểm định riêng. Đổi tên band hoặc resample 10 m thành 30 m không tự tạo sản phẩm HLS tương đương. Bộ lớp 7 lớp và crosswalk được version hóa tại [landcover taxonomy](../docs/landcover-taxonomy.md); nhãn mở không thay test độc lập.

Điều kiện hoàn tất tích hợp: UI chọn được feature Prithvi đã sẵn sàng; worker thực thi đúng checkpoint/decoder; xuất raster địa lý và báo cáo truy nguyên được; chạy trên CPU reference và NVIDIA reference; có evaluation độc lập. Model pack chỉ có backbone hoặc một demo tái tạo ảnh chưa đáp ứng điều kiện này.

<a id="muc-8-3"></a>

### 8.3. Vòng đời model và nhãn

**DatasetVersion → split không gian/thời gian → train bên ngoài desktop → validation/chọn threshold → test độc lập → EvaluationRecord → duyệt ModelSpec → phân phối model package.**

Quy tắc giao nhận nguồn ảnh/nhãn được cụ thể hóa ở [nhóm 3/4 SPEC-002](../docs/specs/002-g0-evidence.md#nhóm-3--nguồn-ảnh-và-đóng-gói-input-x): chuỗi X có ba frame thật, nhãn Y có ngày/kỳ mục tiêu, cùng GridSpec/masks và provenance; kiểm scale/QA/TL, ignore và split trước chipping. Weak labels chỉ dùng warm-up train hoặc gợi ý sửa; nhãn giải đoán/thực địa dùng cho validation/test cần QC độc lập. Không lấy số chip hoặc tỷ lệ chính xác minh họa làm gate; provider/quyền, nhãn/split và người duyệt thực vẫn chờ G0.

G0 bắt đầu chuẩn bị/gán nhãn: chốt class schema, người duyệt, nguồn/quyền sử dụng, AOI/mùa đại diện và kế hoạch split. Việc gán nhãn chạy song song spike kỹ thuật G1; trước G2 phải có checkpoint nghiệp vụ và bộ đánh giá độc lập. Fixture kỹ thuật dùng decoder ngẫu nhiên có ID/seed/hash và trạng thái riêng, không được đưa vào danh sách model nghiệp vụ sẵn sàng.

Bổ sung đặc tả triển khai sau review ngày 08/11/2026: [SPEC-008](../docs/specs/008-training-evaluation-model-pack.md) chịu trách nhiệm tạo dataset/split có duyệt, recipe huấn luyện có version, checkpoint Prithvi + decoder, evaluation và model pack đầu vào của SPEC-006. Training nằm ngoài desktop; ML phụ trách recipe/checkpoint, GIS/data phụ trách nhãn/split và reviewer độc lập kiểm test/gate. Tên người, dữ liệu, hyperparameter và ngân sách thực phải được xác nhận trước thực thi; không coi spec được viết là đã có checkpoint hoặc chất lượng đạt. Giữ baseline thiết kế v1.4 và các gate hiện có.

Model package cần trọng số/hash, manifest, class schema, pre/postprocess version, runtime/precision đã kiểm chứng, evaluation summary và điều kiện sử dụng. Học cách mô tả package từ ArcGIS/ENVI [M2], [M7]; không cam kết import trực tiếp package của hai sản phẩm.

Desktop bản đầu nhập nhãn từ GeoPackage hoặc công cụ hiện có như QGIS/CVAT và hỗ trợ review tối thiểu. Chưa xây một hệ thống annotation đầy đủ. Nhãn phản hồi cần người duyệt; không tự chuyển mọi kết quả AI hoặc mọi sửa chữa thành ground truth.

Chia mẫu theo vùng/thời gian trước khi cắt mảnh, kiểm tra chồng lấn và quan hệ gần nhau; buffer chọn theo độ phân giải, kích thước cửa sổ và tương quan không gian. Không cố định một buffer 1–5 km cho mọi bài toán. Tham khảo cảnh báo train/accuracy overlap của Picterra [M10].

<a id="muc-8-4"></a>

### 8.4. Thước đo và điều kiện phát hành

| Loại kết quả | Thước đo cần lưu | Kiểm tra bổ sung |
| --- | --- | --- |
| Phân loại/phân đoạn | Confusion matrix, precision/recall/F1/IoU theo lớp | Lớp hiếm, vùng thiếu dữ liệu, mùa/vùng chưa thấy |
| Detection/instance | AP với IoU policy, precision/recall, count error, geometry quality | Kích thước mục tiêu, đối tượng sát nhau và đường nối giữa các cửa sổ |
| Biến động | F1/IoU lớp biến động, false alarms theo diện tích | Sai đồng đăng ký, mùa vụ, thời điểm nhãn |
| Hồi quy | MAE/RMSE/bias, sai số theo khoảng giá trị | Kiểm chứng thực địa, khoảng dự báo nếu được hiệu chuẩn |
| Diện tích | Diện tích bản đồ; ước tính điều chỉnh sai số nếu đủ thiết kế lấy mẫu | Coverage, đơn vị và khoảng tin cậy đúng phương pháp |

Định nghĩa metrics trong mã và tài liệu phải thống nhất: precision = TP/(TP+FP), recall = TP/(TP+FN), F1 là trung bình điều hòa. Không thay kiểm định độc lập bằng training loss hay overall accuracy. Không coi confidence của model là xác suất đã hiệu chuẩn hoặc khoảng tin cậy thống kê.

Mỗi feature có ngưỡng chất lượng riêng do chủ nghiệp vụ chốt trước nghiệm thu; chưa có căn cứ đặt một F1 chung cho mọi ngành. Khi thay runtime/FP16/INT8 phải đo sai khác chất lượng so với bản tham chiếu. Drift về phổ, sensor/baseline, coverage hay phân bố lớp chỉ là tín hiệu kiểm tra, chưa tự chứng minh model đã sai hoặc đủ điều kiện tự retrain.

<a id="muc-8-5"></a>

### 8.5. Quy tắc nghiệm thu và điểm dừng thử nghiệm

Bộ giá trị người dùng cung cấp ngày 08/11/2026 được ghi tại [tiêu chí nghiệm thu](../docs/acceptance-criteria.md): bảy lớp/global, coverage, diện tích/CI/CRS, tài nguyên và điểm dừng. Máy GPU mới đã xác nhận dùng riêng training/benchmark, giữ mục tiêu desktop trước đó; protocol/sampling, máy thực, CPU SLO và các khoảng lựa chọn còn cần khóa tại SPEC-002. Ghi ngưỡng chưa là gate đạt. Giữ S30/T=3/224 cho nghiệp vụ và T=1 spike; recipe S30+L30/median, cửa sổ 512, DEM hoặc đổi model phải kiểm riêng, không dùng để bỏ qua quality gate.

G0 phải chốt trước khi tinh chỉnh: ngưỡng tuyệt đối theo lớp/vùng của feature, coverage tối thiểu, ngân sách CPU, số vòng thử tối đa và trần thời gian/chi phí, người chịu trách nhiệm và mốc quyết định. Giá trị cụ thể do chủ nghiệp vụ/chủ dự án phê duyệt trong hồ sơ G0; chưa có các giá trị này thì chưa hoàn tất G0. Không đặt một số vòng hoặc ngưỡng F1 tùy ý cho mọi dự án.

| Kết quả | Quyết định |
| --- | --- |
| Prithvi đạt ngưỡng tuyệt đối, coverage và ngân sách; RF tốt hơn trên một số chỉ tiêu | Có thể nghiệm thu nếu các gate khác đạt; công bố kết quả cả hai trên cùng test split và giới hạn áp dụng, không tuyên bố Prithvi vượt baseline |
| Prithvi chưa đạt và còn ngân sách thử | Điều chỉnh nhãn/model/profile dựa trên validation, ghi từng vòng và chi phí; không dùng test độc lập để lặp chọn cấu hình |
| Hết số vòng, thời gian hoặc chi phí mà vẫn chưa đạt | Dừng mở rộng thử nghiệm theo kế hoạch hiện tại. Chủ dự án quyết định hoãn, thu hẹp feature/AOI/mùa/bộ lớp để kiểm định lại, hoặc phê duyệt thay đổi yêu cầu/phạm vi bằng hồ sơ quyết định |

Phát hành thử nghiệm có công bố giới hạn không đồng nghĩa nghiệm thu feature nghiệp vụ. Đặt RF làm mặc định hoặc cho phép chọn một Prithvi chưa đạt chỉ được xét trong phạm vi thay đổi đã được phê duyệt và gắn trạng thái rõ; không tự thỏa yêu cầu Prithvi dùng cho phân tích ngay bản đầu. Không hạ gate hồi tố để hợp thức hóa kết quả: mọi thay đổi gate có version, lý do, người chốt và kế hoạch đánh giá độc lập mới trước nghiệm thu.

<a id="muc-8-6"></a>

### 8.6. Danh mục mô hình toán–vật lý và mức ưu tiên

Mô hình vật lý mô tả quan hệ truyền bức xạ, trao đổi năng lượng hoặc bảo toàn khối lượng/động lượng. Chỉ số phổ, SCS-CN, RUSLE và allometry là phương pháp chỉ số/bán thực nghiệm; HAND là mô tả địa hình theo mạng thoát nước. Phân biệt các loại này trong metadata và báo cáo để không gắn mức giải thích vật lý vượt quá phương pháp thực dùng.

| ID / phương pháp | Đại lượng và dữ liệu bắt buộc | Vị trí trong lộ trình |
| --- | --- | --- |
| GEO-01 — chỉ số phổ, diện tích và coverage | Reflectance HLS đã QA; grid/AOI và raster nhãn; NDVI/EVI/NDMI/MNDWI đã được người dùng chọn cho đợt đầu | G0 còn chốt policy/QA/tolerance và cách thống kê; G1 kiểm tra công thức/đơn vị; G2 dùng đo/thống kê cho feature đầu |
| PHY-01 — PROSAIL (PROSPECT + SAIL) | Phản xạ lá/tán và nghịch đảo LAI/chlorophyll; phổ, đáp ứng phổ cảm biến, góc chiếu/nhìn, tham số tán/đất, số đo thực địa | Ứng viên G4 cho nông nghiệp/thảm thực vật [F1] |
| PHY-02 — FAO-56 Penman–Monteith | ET0 và ETc tham chiếu cây trồng; khí tượng, bức xạ, áp suất/độ cao, Kc và giai đoạn sinh trưởng khi tính ETc | Ưu tiên khảo sát G4 khi có nguồn khí tượng/hiệu chuẩn [F2] |
| PHY-03 — cân bằng năng lượng bề mặt theo SEBAL | ET thực từ bức xạ thuần, nhiệt đất, nhiệt hiện và nhiệt ẩn; cần dữ liệu nhiệt/LST, khí tượng, albedo, emissivity và độ nhám | G4 có điều kiện dữ liệu nhiệt và kiểm định năng lượng/ET; chọn thuật toán/solver cụ thể trước triển khai [F3] |
| PHY-04 — SCS Curve Number (SCS-CN) | Độ sâu dòng chảy trực tiếp của trận mưa; mưa tích lũy, nhóm đất thủy văn, sử dụng đất, điều kiện ẩm và CN đã hiệu chuẩn | Ưu tiên khảo sát G4 cho mưa–dòng chảy theo lưu vực [F4] |
| PHY-05 — HAND | Cao độ so với điểm thoát nước nhận dòng; DEM đã xử lý thủy văn, hướng dòng, mạng sông; mực nước tương ứng nếu lập kịch bản | G4 để sàng lọc nhạy cảm ngập, chưa phải mô phỏng diễn biến lũ [F5] |
| PHY-06 — hệ phương trình nước nông 2D | Độ sâu, vận tốc, thời gian ngập; DEM/bathymetry, lưới, điều kiện đầu/biên, nhám và công trình | G4 theo dự án thủy lực riêng; adapter solver đã kiểm chứng và giấy phép phù hợp [F6] |
| PHY-07 — RUSLE | Mất đất trung bình dài hạn do xói mòn tấm/rãnh nhỏ; R, K, LS, C, P và nguồn kiểm định | G4 cho quản lý đất/lưu vực; không đồng nhất mất đất sườn dốc với bùn cát tại cửa ra [F7] |
| PHY-08 — allometry Chave 2014 và quy đổi carbon | Sinh khối trên mặt đất của cây/ô mẫu; đường kính, chiều cao, khối lượng riêng gỗ, diện tích ô và hệ số carbon có nguồn | G4 cho rừng phù hợp miền hiệu lực, cần kiểm kê thực địa; bản đồ diện rộng qua mô hình được kiểm định riêng [F8] |

Danh mục trên là các phương pháp dự kiến có hồ sơ kỹ thuật, không phải cam kết đã đóng gói hoặc chạy đủ tám model. G4 chọn từng feature theo dữ liệu/nhu cầu; mỗi lựa chọn phải đạt ngưỡng tuyệt đối, ngân sách thử và quy tắc dừng tương tự [mục 8.5](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-5). Nhu cầu triển khai sớm hơn phải cập nhật phạm vi/gate, không mặc định thêm toàn bộ dependency chuyên ngành vào core.

<a id="muc-8-7"></a>

### 8.7. Phương trình, đơn vị và giới hạn áp dụng

<a id="muc-8-7-1"></a>

#### 8.7.1. GEO-01 — chỉ số phổ và phép đo diện tích

Với `rho` là surface reflectance đã scale/offset đúng, cùng grid/ngày và mask hợp lệ:

```text
NDVI  = (rho_NIR - rho_Red)   / (rho_NIR + rho_Red)
EVI   = 2.5 * (rho_NIR - rho_Red) / (rho_NIR + 6*rho_Red - 7.5*rho_Blue + 1)
NDMI  = (rho_NIR - rho_SWIR1) / (rho_NIR + rho_SWIR1)
MNDWI = (rho_Green - rho_SWIR1) / (rho_Green + rho_SWIR1)
```

Mapping HLS theo [mục 8.2](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-2); các chỉ số không có đơn vị. Mẫu số gần 0 theo tolerance của profile, mây/NoData hoặc band không hợp lệ tạo invalid mask, không tự trả 0. Không mặc định một ngưỡng chỉ số đúng cho mọi mùa/vùng; chỉ số là đặc trưng/chẩn đoán hoặc baseline đã kiểm định, không tự là LAI, độ sâu nước hay độ ẩm đất tuyệt đối. Công thức có thể dùng trực tiếp reflectance, không dùng display stretch.

EVI ở đây là bản ba band, hệ số G=2,5, C1=6, C2=7,5, L=1; hằng số L yêu cầu reflectance đã scale/offset về đơn vị không thứ nguyên, không dùng DN chưa scale. HLS S30 dùng NIR B8A, Red B04, Blue B02; L30 khi được hỗ trợ dùng B05/B04/B02 tương ứng. Giữ công thức và mask/tolerance trong profile có version, không tự chuyển EVI sang EVI2 hoặc clip mọi chỉ số về [-1,1] để che giá trị bất thường. Cần fixture số học, scale/mask và band mapping trước nghiệm thu; chưa có số đo kiểm định GeoAI.

Diện tích lớp `k` trên vùng quan sát hợp lệ: `A_k = sum_i(a_i × v_i × I(label_i = k))`, với `a_i` là diện tích phần ô nằm trong AOI tính bằng m² theo ellipsoid hoặc CRS phù hợp, `v_i` là valid mask. Coverage bằng diện tích có quan sát hợp lệ chia diện tích AOI; báo riêng diện tích không quan sát. Nếu dùng raster hóa biên theo tâm pixel thay diện tích giao chính xác thì phải ghi phương pháp và kiểm tra sai số biên. Đổi m² sang ha bằng chia 10.000. Đây là diện tích bản đồ; ước lượng điều chỉnh sai số và khoảng tin cậy cần thiết kế lấy mẫu kiểm định riêng.

<a id="muc-8-7-2"></a>

#### 8.7.2. PHY-01 — truyền bức xạ lá/tán PROSAIL

PROSPECT mô tả quang học lá; SAIL mô tả truyền bức xạ trong tán. Dạng forward: `rho(lambda) = F_PROSAIL(theta, geometry, soil)`, với `theta` gồm LAI, cấu trúc lá, chlorophyll, nước/chất khô lá, phân bố góc lá và tham số hotspot theo đúng biến thể. Bộ mặc định để khảo sát là PROSPECT-D + 4SAIL; implementation và giấy phép được khóa khi làm feature [F1].

So sánh với band cảm biến phải tích phân phổ qua spectral response function: `rho_b = integral(rho(lambda) × SRF_b(lambda)) / integral(SRF_b(lambda))`. Nghịch đảo bằng LUT hoặc tối ưu có ràng buộc: tối thiểu hóa sai khác phổ có trọng số sai số cộng prior/regularization; lưu miền tham số, cách tìm nghiệm và tiêu chí hội tụ. LAI có đơn vị m² lá/m² đất; chlorophyll thường là microgram/cm² lá theo profile, không tự đổi đơn vị.

Sáu band HLS không đủ để tự do suy đồng thời mọi tham số của PROSAIL. Phải cố định/đặt prior cho tham số không nhận dạng được, đánh giá độ nhạy và kiểm định LAI/chlorophyll bằng đo thực địa độc lập. Tán thưa, cấu trúc rừng phức tạp, nền đất và góc quan sát có thể làm giả định tán đồng nhất không phù hợp. HLS đã xử lý khí quyển/chuẩn hóa góc theo sản phẩm; adapter phải xác định hình học phản xạ phù hợp sản phẩm, không áp lại hiệu chỉnh hoặc dùng góc ảnh gốc một cách máy móc.

<a id="muc-8-7-3"></a>

#### 8.7.3. PHY-02 — FAO-56 Penman–Monteith

Profile bước thời gian ngày, bề mặt cỏ tham chiếu:

```text
ET0 = [0.408 × Delta × (Rn - G)
       + gamma × 900/(T + 273) × u2 × (es - ea)]
      / [Delta + gamma × (1 + 0.34 × u2)]
ETc = Kc × ET0
```

`ET0` tính bằng mm/ngày; `Rn`, `G` là MJ/m²/ngày; `T` là °C ở 2 m; `u2` là m/s ở 2 m; `es`, `ea` là kPa; `Delta` và `gamma` là kPa/°C. Phương trình và hằng số ở đây dành cho bước ngày; profile giờ có hệ số/quy tắc riêng. Nếu adapter gọi PyETo thì chuyển °C sang K theo chữ ký API, không cộng 273 hai lần [F2].

`ETc` với `Kc` đúng loại cây/giai đoạn và điều kiện chuẩn mô tả nhu cầu thoát hơi cây trồng; không tự bằng ET thực khi thiếu nước. Muốn mô tả stress cần mô hình nước đất/hệ số stress đã chọn và hiệu chuẩn riêng. Ghi nguồn nhiệt độ/ẩm/gió/bức xạ, độ cao/áp suất, quy tắc tổng hợp ngày và nội suy. HLS hỗ trợ loại cây/diễn biến tán khi đã kiểm định, không thay các biến khí tượng còn thiếu. So ET0 với phép tính chuẩn; kiểm định ETc bằng lysimeter hoặc quan trắc phù hợp, đồng bộ diện tích và thời gian.

<a id="muc-8-7-4"></a>

#### 8.7.4. PHY-03 — cân bằng năng lượng và SEBAL

Quan hệ đóng năng lượng bề mặt: `Rn - G = H + LE`, các thông lượng cùng đơn vị W/m² tại thời điểm tính. `LE` là nhiệt ẩn phục vụ bốc thoát hơi; `H` là nhiệt hiện. Trong SEBAL, ước tính `H` liên quan đến nhiệt độ bề mặt, vận chuyển khí động, độ nhám và lựa chọn điểm neo nóng/lạnh; cần khóa quy tắc neo, hiệu chỉnh ổn định khí quyển và kiểm tra hội tụ [F3].

ET trong khoảng thời gian được suy từ tích phân `LE` chia nhiệt hóa hơi: với năng lượng MJ/m² và nhiệt hóa hơi MJ/kg, kết quả kg/m² tương đương mm nước. Không lấy một ảnh nhiệt tức thời rồi nhân thẳng thành ET ngày; cách ngoại suy theo ngày phải có giả định và kiểm định riêng.

HLS S30 sáu band không cung cấp kênh nhiệt. Feature này cần nguồn nhiệt/LST phù hợp như sản phẩm Landsat thermal đã QA, khí tượng và các tham số bề mặt; ghi GSD gốc và thời điểm của từng nguồn. Resample LST thô về 30 m không tạo phép đo nhiệt thật ở 30 m. Kiểm định ET với eddy covariance/lysimeter hoặc cân bằng nước độc lập có xử lý sai số và chênh lệch footprint; phần dư cân bằng bằng 0 do tính LE từ phương trình không tự chứng minh ET đúng.

<a id="muc-8-7-5"></a>

#### 8.7.5. PHY-04 — mưa–dòng chảy SCS-CN

Profile trận mưa, đơn vị mm:

```text
S  = 25400/CN - 254
Ia = lambda × S
Q  = 0                                  khi P <= Ia
Q  = (P - Ia)^2 / (P - Ia + S)           khi P > Ia
```

`P` là mưa tích lũy, `Q` là độ sâu dòng chảy trực tiếp, `S` là khả năng giữ nước, `Ia` là tổn thất ban đầu; `CN` trong khoảng `(0, 100]`. Giá trị `lambda = 0.2` là quan hệ khởi đầu truyền thống, không phải hằng số đúng cho mọi lưu vực; thay lambda phải hiệu chuẩn lại CN tương ứng [F4]. CN cần loại sử dụng đất, nhóm đất thủy văn, điều kiện ẩm và tỷ lệ không thấm theo bảng có nguồn. Lớp phủ Prithvi chỉ cung cấp một phần đầu vào, không xác định CN duy nhất.

Với nhiều tiểu vùng, tính thể tích `sum(Q_i × area_i / 1000)` theo m³ rồi tổng hợp; phải khai báo nếu dùng CN tổng hợp vì quan hệ phi tuyến cho kết quả khác. SCS-CN dự báo lượng dòng chảy dư của sự kiện, chưa tạo hydrograph, đỉnh lưu lượng hay mực ngập; muốn có các đại lượng đó cần mô hình chuyển mưa–dòng chảy theo thời gian/routing và dữ liệu kiểm định bổ sung. Kiểm tra `0 <= Q <= P`, ca mưa dưới tổn thất ban đầu và CN=100, đối chiếu thể tích dòng chảy sự kiện từ trạm đo sau xử lý baseflow phù hợp.

<a id="muc-8-7-6"></a>

#### 8.7.6. PHY-05/06 — HAND và thủy lực nước nông 2D

HAND tại ô `i`: `HAND_i = z_i - z_d(i)`, trong đó `d(i)` là ô mạng thoát nước nhận dòng từ `i` theo routing địa hình, không phải sông gần nhất theo khoảng cách Euclid [F5]. Khóa phương pháp xử lý depression, hướng dòng D8 hoặc phương pháp tương đương, ngưỡng tạo mạng sông, DEM và datum đứng. DEM làm phẳng/sửa dòng phải giữ riêng cùng recipe và vùng sửa; cầu/đê/cống và đô thị có thể làm routing DEM sai thực tế.

Nếu có chiều cao nước `h_r` so với cùng đáy tham chiếu của reach nhận dòng, `max(0, h_r - HAND_i)` chỉ là độ sâu kịch bản gần đúng sau kiểm tra kết nối thủy lực và datum. Không dùng một mực nước chung cho toàn tỉnh hoặc gọi kết quả này là mô phỏng vận tốc/thời gian lũ. HAND tự nó mô tả địa hình; kiểm định kịch bản bằng dấu vết/mực nước hoặc bản đồ ngập quan trắc đồng thời.

Khi nghiệp vụ cần diễn biến độ sâu/vận tốc, chọn solver nước nông 2D giải hệ bảo toàn khối lượng và động lượng. Dạng minh họa trên đáy cố định, bỏ qua các hạng bổ sung như Coriolis/khuếch tán rối:

```text
dh/dt + div(h × u) = r - f + q
d(h × u)/dt + div(h × u ⊗ u + 0.5 × g × h^2 × I)
  = -g × h × grad(zb) - tau_b/rho_w + s_m
```

`h` là độ sâu m; `u` là vector vận tốc m/s; `zb` là cao độ đáy m; `r`, `f`, `q` là nguồn/hao nước theo độ sâu m/s; `tau_b` là ứng suất đáy, `rho_w` là khối lượng riêng nước; `s_m` là nguồn động lượng nhất quán với dòng vào/ra. Đặc tả solver phải ghi đầy đủ các hạng thực dùng, đóng ma sát (ví dụ Manning với nhám có đơn vị), sơ đồ số, bước thời gian/CFL, wetting–drying, lưới và điều kiện biên [F6].

Tích hợp qua adapter một solver đã kiểm chứng; không tự viết solver thủy lực tổng quát trong bản đầu. Cần terrain/bathymetry, mưa hoặc hydrograph/mực nước biên, điều kiện đầu, công trình và nhám đã hiệu chuẩn. Kiểm tra lake-at-rest, khối lượng, độ sâu không âm, độ nhạy lưới/bước thời gian; kiểm định độc lập mực nước, hydrograph và footprint ngập. Budget CPU cho solver được đo riêng; không suy từ benchmark Prithvi.

<a id="muc-8-7-7"></a>

#### 8.7.7. PHY-07 — xói mòn đất RUSLE

`A = R × K × LS × C × P`, với `A` là mất đất trung bình dài hạn, chọn hệ SI để báo bằng tấn/ha/năm. `R` là độ gây xói mòn mưa, `K` là tính dễ xói của đất, `LS` là chiều dài/độ dốc sườn, `C` là che phủ/quản lý, `P` là biện pháp bảo tồn [F7]. `LS/C/P` không có đơn vị; đơn vị R và K phải là bộ tương thích để tích cho đúng đơn vị A, không trộn hệ US customary với SI.

R cần dữ liệu cường độ/năng lượng mưa hoặc quan hệ địa phương đã kiểm định; tổng mưa năm đơn thuần không tự là R. K cần thuộc tính đất, LS cần DEM và phương pháp chiều dài dòng chảy/ngưỡng giới hạn, C/P cần sử dụng đất và thực hành quản lý có nguồn. Chỉ số NDVI hoặc lớp phủ có thể hỗ trợ C sau hiệu chuẩn, không suy P chỉ từ ảnh.

RUSLE mô tả xói mòn tấm và rãnh nhỏ do mưa/dòng chảy mặt; không tự dự báo trượt lở, xói lòng/bờ sông hoặc bùn cát cửa ra. Muốn chuyển mất đất sườn dốc thành sediment yield cần mô hình phân phối/vận chuyển và dữ liệu mới. Kiểm định với ô đo xói mòn hoặc quan trắc phù hợp cùng khoảng thời gian; báo độ nhạy R/K/LS/C/P và độ bất định, không gọi mọi raster RUSLE là đo đạc mất đất thực tế.

<a id="muc-8-7-8"></a>

#### 8.7.8. PHY-08 — sinh khối và carbon rừng

Ứng viên allometry cho cây nhiệt đới trong miền hiệu lực của Chave 2014, có chiều cao [F8]:

```text
AGB_tree_kg = 0.0673 × (rho_wood × D^2 × H)^0.976
AGB_plot_Mg_ha = sum(AGB_tree_kg) / (1000 × plot_area_ha)
C_aboveground_Mg_ha = f_C × AGB_plot_Mg_ha
```

`D` là đường kính thân theo quy trình kiểm kê, đơn vị cm; `H` là chiều cao cây m; `rho_wood` là g/cm³; AGB là khối lượng khô trên mặt đất. Nếu adapter dùng package trả Mg/cây thì không chia 1.000 lần nữa. Phải kiểm tra loài/kiểu rừng và khoảng kích thước áp dụng; rừng trồng đặc thù, cây bụi hoặc cây ngoài miền hiệu lực có thể cần phương trình địa phương. `f_C` có nguồn, phiên bản và độ bất định phù hợp, không gán một tỷ lệ carbon cho mọi sinh cảnh.

HLS không đo trực tiếp D, H hay khối lượng riêng gỗ từng cây. Dữ liệu kiểm kê tạo nhãn ô mẫu; sau đó mới dùng hồi quy/ML hoặc đặc trưng Prithvi kết hợp dữ liệu phù hợp để lập bản đồ diện rộng, với split độc lập theo ô/vùng và khớp diện tích/thời điểm. DEM mặt đất không phải chiều cao cây; cần đo H, mô hình D–H đã kiểm định hoặc dữ liệu canopy thích hợp.

Trữ lượng carbon trên mặt đất không đại diện tất cả bể carbon và không tự là lượng hấp thụ/phát thải. So sánh hai thời điểm phải cùng phạm vi/bể/phương pháp và truyền sai số; hệ số 44/12 chỉ đổi khối lượng C thành CO2 tương đương về hóa học, không tự tạo tín chỉ hay mức giảm phát thải đã xác minh.

<a id="muc-8-8"></a>

### 8.8. Tích hợp mô hình vật lý, hiệu chuẩn và độ bất định

Workflow dùng chung: **snapshot nguồn → kiểm tra biến/đơn vị/grid/thời gian → chuẩn hóa → chạy phương pháp đã đăng ký → kiểm tra miền hiệu lực/cân bằng/hội tụ → artifact và uncertainty → review → báo cáo**. `geoprocessing` chuẩn bị dữ liệu; `analytics` chứa phép tính/adapter; `domains` chọn phương pháp/tham số; `jobs/compute` cấp ngân sách. NumPy/SciPy có thể phục vụ đại số, LUT, tối ưu và lấy mẫu; dependency chuyên ngành/solver chỉ đóng gói cùng feature đã kiểm chứng.

`PhysicalModelSpec` và parameter snapshot phải ghi nguồn phương trình, đơn vị, giá trị/range, cách hiệu chuẩn, hash code/solver, dữ liệu calibration/validation/test, support domain và cách xử lý ngoài miền. Phân biệt tham số đo, tham số lấy từ tài liệu và tham số đã fit. Không tự mặc định số 0 cho forcing thiếu, không clip kết quả vật lý vô lý rồi bỏ dấu vết; trả quality flag hoặc chặn tùy profile. Profile đơn giản như chỉ số phổ không cần solver/điều kiện biên, các trường không áp dụng phải thể hiện rõ.

Khi ghép AI với vật lý, lưu cả model AI và mô hình vật lý: ví dụ lớp phủ → bảng CN/C/P đã hiệu chuẩn; ô kiểm kê → allometry → hồi quy bản đồ AGB. Sai số lớp phủ và bảng hệ số phải truyền xuống kết quả. Đầu ra mô hình vật lý chưa kiểm định không tự trở thành ground truth; dùng dữ liệu tổng hợp từ PROSAIL để huấn luyện phải công bố simulation-to-real gap và kiểm định bằng quan trắc thật. Physics-informed loss/PINN là hướng nghiên cứu riêng, chưa là dependency bắt buộc.

Ước lượng độ bất định bằng phân tích độ nhạy và Monte Carlo có seed, số mẫu, phân phối/range cùng tương quan đầu vào được ghi rõ. Với gần tuyến tính, có thể dùng `Var(y) ≈ J × Sigma × J^T`; không giả định mọi input/pixel độc lập. Sai số cấu trúc model, tham số và quan trắc được báo riêng khi có thể. Chỉ công bố khoảng bất định khi có giả định thống kê đủ cơ sở và kiểm tra độ phủ trên dữ liệu độc lập; dải min–max của kịch bản không được gọi là khoảng tin cậy.

<a id="muc-8-9"></a>

### 8.9. Kiểm chứng và cổng phát hành cho mô hình toán–vật lý

| Nhóm kiểm chứng | Bằng chứng bắt buộc trước phát hành feature tương ứng |
| --- | --- |
| Công thức/đơn vị | Ví dụ chuẩn độc lập cho diện tích/chỉ số, ET0, SCS-CN và allometry; kiểm chuyển °C/K, mm/m, kg/Mg và diện tích ô; tolerance theo độ chính xác đầu vào |
| Địa lý/thời gian | DEM/datum đứng, lưới, footprint và múi giờ/kỳ tích lũy khí tượng khớp; không tạo chi tiết giả bằng resampling hoặc ghép dữ liệu lệch thời điểm |
| Forward/inverse | PROSAIL so phổ với reference và kiểm nhận dạng tham số; solver kiểm hội tụ/lưới, bảo toàn và ca chuẩn; benchmark số học không thay validation thực địa |
| Hiệu chuẩn/kiểm định | Tách calibration/validation/test theo vùng, mùa hoặc sự kiện; không dùng test để chọn tham số; lưu baseline đơn giản, MAE/RMSE/bias và chỉ tiêu chuyên ngành phù hợp |
| Ngập/dòng chảy | SCS-CN kiểm thể tích, HAND kiểm topology/mực nước/kết nối, solver 2D kiểm khối lượng/độ sâu/vận tốc; quan trắc và dự báo phải cùng đại lượng |
| Uncertainty/miền hiệu lực | Đánh giá độ nhạy, sai số đầu vào/tham số, xử lý ngoài miền và mức tin cậy của khoảng báo cáo; dữ liệu thiếu vẫn thể hiện coverage/quality flags |
| Vận hành | Fixture CPU/offline, version solver và giấy phép, ngân sách RAM/đĩa/thời gian, cancel/resume theo capability; không mặc định mọi solver hỗ trợ checkpoint theo mảnh |

G0–G2 của bản đầu áp dụng GEO-01 cùng Prithvi và RF/boosting. Khi mở feature PHY ở G4, lập hồ sơ dữ liệu/đại lượng, ngưỡng nghiệm thu và ngân sách thử trước; kiểm chứng kỹ thuật, hiệu chuẩn rồi test độc lập trước phát hành. Trạng thái reviewed của chuyên gia không thay việc feature/model đạt quality gate.

---

**Tài liệu liên quan:**

- [Phạm vi bản đầu và luồng sử dụng](03_pham_vi_ban_dau_va_luong_su_dung.md)
- [Hợp đồng dữ liệu và versioning](05_hop_dong_du_lieu_va_versioning.md)
- [Dữ liệu đa nguồn và chuẩn hóa địa lý](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md)
- [Runtime CPU/NVIDIA và hiệu năng](12_runtime_cpu_nvidia_va_hieu_nang.md)
- [Lộ trình và cổng nghiệm thu](15_lo_trinh_va_cong_nghiem_thu.md)

[M2]: https://doc.esri.com/en/arcgis-pro/latest/help/analysis/image-analyst/deep-learning-models-in-arcgis.html
[M7]: https://www.nv5geospatialsoftware.com/docs/ConfigureONNXModel.html
[M10]: https://docs.picterra.ai/detectors/detector-insights/
[P1]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL/raw/63adbd39c271da4c42f447e69b1a7c91a338cdc9/README.md
[P2]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL/raw/63adbd39c271da4c42f447e69b1a7c91a338cdc9/config.json
[P3]: https://raw.githubusercontent.com/NASA-IMPACT/Prithvi-EO-2.0/main/configs/sen1floods11.yaml
[P4]: https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSS30_v002
[P5]: https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSL30_v002
[P6]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-tiny-TL/tree/335eadc2c45ad5abe7bd307223e1c48c5b60c41b
[P7]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-100M-TL/tree/2c84e383194986040f883cc43d7869002c425e1b
[P8]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M/tree/9eb1b1102806593963daa333bcc491b1c6f8562f
[F1]: https://github.com/jgomezdans/prosail
[F2]: https://github.com/woodcrafty/PyETo/blob/master/pyeto/fao.py
[F3]: https://doi.org/10.1016/S0022-1694(98)00253-4
[F4]: https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/canopy-surface-infiltration-and-runoff-volume/infiltration/scs-curve-number-loss-model
[F5]: https://doi.org/10.1016/j.jhydrol.2011.03.051
[F6]: https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.6/theoretical-basis-for-one-dimensional-and-two-dimensional-hydrodynamic-calculations/2d-unsteady-flow-hydrodynamics
[F7]: https://www.ars.usda.gov/southeast-area/oxford-ms/national-sedimentation-laboratory/watershed-physical-processes-research/docs/revised-universal-soil-loss-equation-106-description-of-rusle106c/
[F8]: https://github.com/cran/BIOMASS/blob/master/R/computeAGB.R
