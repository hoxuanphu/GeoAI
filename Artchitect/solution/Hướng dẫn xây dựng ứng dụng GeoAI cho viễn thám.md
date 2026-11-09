# Hướng dẫn xây dựng ứng dụng GeoAI cho viễn thám

Nov 8, 2026 · @Phú Hồ Xuân

## 1. Giới thiệu và cách dùng tài liệu

Một ứng dụng GeoAI viễn thám thành công phụ thuộc vào ba thứ theo thứ tự: bài toán được định nghĩa rõ, dữ liệu và nhãn phù hợp với khu vực áp dụng, rồi mới đến mô hình. Tài liệu này đi theo đúng thứ tự đó, từ năng lực và nhu cầu, qua dữ liệu và mô hình, đến kiến trúc hệ thống và lộ trình triển khai.

**GeoAI** là việc áp dụng trí tuệ nhân tạo (học máy, học sâu, mô hình nền tảng) vào dữ liệu không gian địa lý. Trong viễn thám, đầu vào là ảnh quang học đa phổ và siêu phổ, ảnh radar SAR, LiDAR, ảnh UAV và các lớp dữ liệu phụ trợ (địa hình, khí tượng, bản đồ nền). Điểm khác biệt so với thị giác máy tính thông thường: ảnh có nhiều kênh phổ ngoài RGB, có hệ tọa độ, có chiều thời gian, và có ý nghĩa vật lý (phản xạ, tán xạ ngược, nhiệt độ).

**Cách dùng tài liệu khi xây dựng ứng dụng:**

1. Chọn bài toán và điền bảng yêu cầu ở mục 3.
2. Chọn nguồn ảnh và quy trình tiền xử lý ở mục 4.
3. Chọn hướng mô hình: vật lý (mục 5), học máy cổ điển (mục 6), học sâu (mục 7) hoặc tinh chỉnh mô hình nền tảng (mục 8).
4. Lấy dataset công khai để tiền huấn luyện hoặc benchmark (mục 9), sau đó xây dataset riêng cho khu vực của bạn (mục 10).
5. Huấn luyện và đánh giá đúng cách (mục 11).
6. Đóng gói thành hệ thống theo kiến trúc mục 12, dùng công cụ ở mục 13 và lộ trình ở mục 14.
7. Rà soát rủi ro, giấy phép và vận hành ở mục 15.

Lĩnh vực này thay đổi nhanh, đặc biệt là mô hình nền tảng. Thông tin trong tài liệu chính xác tại ngày ghi ở đầu trang; hãy kiểm tra phiên bản mới của thư viện và mô hình trước khi triển khai.

## 2. Năng lực của GeoAI trong viễn thám

Mọi ứng dụng GeoAI viễn thám đều ghép từ khoảng 14 năng lực cơ bản dưới đây. Khi thiết kế sản phẩm, hãy xác định rõ ứng dụng cần những năng lực nào và đầu ra của từng năng lực có dạng gì (raster, vector hay số liệu), vì điều đó quyết định cách gán nhãn, chọn mô hình và lưu trữ.

| Năng lực | Đầu vào điển hình | Đầu ra | Ví dụ |
| --- | --- | --- | --- |
| Phân loại cảnh (scene classification) | Mảnh ảnh 64–512 px | Một hoặc nhiều nhãn cho cả mảnh | Lọc ảnh có bãi khai thác cát, sàng lọc ảnh nhiều mây |
| Phân đoạn ngữ nghĩa (semantic segmentation) | Ảnh đa phổ, SAR, hoặc kết hợp | Raster nhãn theo pixel | Bản đồ lớp phủ, mặt nước, vùng cháy |
| Phát hiện đối tượng (object detection) | Ảnh độ phân giải cao (≤ 1 m) hoặc SAR | Hộp bao thẳng hoặc hộp xoay (OBB) + nhãn | Tàu, máy bay, xe, bồn dầu |
| Phân đoạn thực thể (instance segmentation) | Ảnh độ phân giải cao | Đa giác từng đối tượng | Footprint nhà, thửa ruộng, ao nuôi |
| Phát hiện biến động (change detection) | Cặp hoặc chuỗi ảnh đã đồng đăng ký | Raster biến động nhị phân hoặc theo loại | Mất rừng, xây dựng mới, thiệt hại sau bão |
| Phân tích chuỗi thời gian | Chuỗi ảnh nhiều thời điểm | Nhãn theo pixel/thửa, ngày sự kiện | Phân loại cây trồng, lịch gieo sạ và thu hoạch |
| Hồi quy tham số sinh-địa-vật lý | Ảnh + dữ liệu đo đạc mặt đất | Raster giá trị liên tục kèm độ bất định | Sinh khối, chiều cao tán, độ ẩm đất, LAI, độ mặn |
| Trích xuất cấu trúc tuyến | Ảnh độ phân giải cao, DEM | Đồ thị đường (polyline + nút) | Đường giao thông, sông suối, đường bờ |
| Nâng cao chất lượng ảnh | Ảnh độ phân giải thấp, ảnh có mây, SAR nhiễu | Ảnh đã cải thiện | Siêu phân giải Sentinel-2 từ 10 m lên 2,5 m, loại mây, khử speckle |
| Hợp nhất đa nguồn (data fusion) | Quang học + SAR + DEM + khí tượng | Đặc trưng hoặc ảnh hợp nhất | Bản đồ lúa trong mùa mưa, SAR sang ảnh quang học |
| Phân tích siêu phổ | Ảnh hàng trăm kênh | Nhãn hoặc tỷ lệ thành phần (abundance) | Khoáng sản, chất lượng nước, sâu bệnh cây |
| Xử lý đám mây điểm LiDAR | Đám mây điểm 3D | Nhãn theo điểm, DSM/DTM | Phân loại mặt đất, cây, công trình |
| Phân đoạn theo lời nhắc (promptable) | Ảnh + điểm, hộp hoặc cụm từ | Mặt nạ đối tượng | Gõ “greenhouse” để trích xuất mọi nhà kính |
| Thị giác-ngôn ngữ | Ảnh + câu hỏi tự nhiên | Câu trả lời, chú thích, vùng được chỉ | “Có bao nhiêu tàu trong cảng?”, tìm kiếm ảnh bằng văn bản |

Ngoài ra còn một năng lực mới nổi từ 2025: **vector nhúng Trái Đất (Earth embeddings)** tính sẵn cho toàn cầu. Mỗi pixel 10 m được mô tả bằng một vector 64–128 chiều tóm tắt cả năm dữ liệu đa cảm biến, nên chỉ cần một bộ phân loại nhẹ và ít nhãn là đã lập được bản đồ (xem mục 8).

Các năng lực thường được xâu chuỗi. Ví dụ một ứng dụng giám sát xây dựng sai phép dùng: loại mây → phát hiện biến động trên Sentinel-2 để khoanh vùng nghi vấn → phân đoạn thực thể trên ảnh độ phân giải cao để lấy footprint → đối chiếu với dữ liệu cấp phép.

## 3. Bài toán ứng dụng và cách xác định yêu cầu

Một bài toán GeoAI chỉ được coi là định nghĩa xong khi trả lời được: đối tượng nhỏ nhất cần thấy là bao nhiêu mét, cần cập nhật bao lâu một lần, và sai số bao nhiêu thì người dùng chấp nhận. Ba con số này quyết định nguồn ảnh, chi phí và loại mô hình.

### 3.1. Bài toán theo lĩnh vực

| Lĩnh vực | Bài toán cụ thể | Năng lực chính | Dữ liệu phù hợp |
| --- | --- | --- | --- |
| Nông nghiệp | Bản đồ diện tích lúa theo vụ, lịch gieo sạ, dự báo năng suất, hạn và xâm nhập mặn | Chuỗi thời gian, phân đoạn, hồi quy | Sentinel-1 (xuyên mây), Sentinel-2, HLS, dữ liệu thống kê |
| Lâm nghiệp và carbon | Cảnh báo mất rừng, ước lượng sinh khối/carbon cho tín chỉ, cháy rừng | Biến động, hồi quy, phân đoạn | Sentinel-1/2, Landsat, GEDI, NISAR L-band |
| Đô thị và địa chính | Mở rộng đô thị, xây dựng sai phép, cập nhật bản đồ nền, đảo nhiệt | Thực thể, biến động, trích xuất đường | Ảnh VHR (≤ 0,5 m), UAV, Landsat nhiệt |
| Thiên tai | Bản đồ ngập nhanh, sạt lở, thiệt hại sau bão, sụt lún | Phân đoạn, biến động, InSAR | Sentinel-1, NISAR, ảnh VHR thương mại, DEM |
| Biển và ven biển | Tàu không phát AIS (IUU), dầu tràn, xói lở bờ, ao nuôi thủy sản | Phát hiện, phân đoạn, biến động | Sentinel-1, Sentinel-2, dữ liệu AIS |
| Tài nguyên, môi trường | Khai thác cát/khoáng sản trái phép, chất lượng nước, rác thải | Phát hiện, hồi quy, siêu phổ | Sentinel-2, PlanetScope, EnMAP/PRISMA |
| Hạ tầng và năng lượng | Kiểm kê điện mặt trời, gió; hành lang tuyến điện; đường ống | Phát hiện, phân đoạn, LiDAR | Ảnh VHR, UAV, LiDAR |
| Quốc phòng, an ninh | Giám sát mục tiêu, phát hiện thay đổi khu vực nhạy cảm | Phát hiện, biến động | SAR và quang học VHR |
| Tài chính, bảo hiểm | Bảo hiểm nông nghiệp theo chỉ số, định giá rủi ro thiên tai | Chuỗi thời gian, hồi quy | Sentinel, dữ liệu khí tượng |

### 3.2. Bảng yêu cầu cần điền trước khi làm

| Hạng mục | Câu hỏi cần trả lời | Ảnh hưởng đến |
| --- | --- | --- |
| Đối tượng nhỏ nhất | Ví dụ nhà 5 m cần ảnh ≤ 0,5 m; ruộng 1 ha dùng được ảnh 10 m | Nguồn ảnh, chi phí |
| Tần suất cập nhật | Hàng ngày, hàng tuần, theo vụ, hàng năm | Vệ tinh, hạ tầng xử lý |
| Độ trễ chấp nhận được | Thiên tai cần vài giờ; thống kê nông nghiệp chấp nhận vài tuần | Kiến trúc (stream hay batch) |
| Điều kiện thời tiết | Vùng nhiều mây mùa mưa thì bắt buộc có SAR | Cảm biến, mô hình fusion |
| Phạm vi không gian | Một huyện, một tỉnh hay toàn quốc | Lưu trữ, chi phí tính toán |
| Đầu ra | Raster, vector, báo cáo thống kê, cảnh báo | Thiết kế API, frontend |
| Ngưỡng chất lượng | Ví dụ F1 ≥ 0,85 cho lớp lúa, sai số diện tích ≤ 10% | Tiêu chí nghiệm thu |
| Dữ liệu mặt đất | Có sẵn điểm khảo sát, bản đồ cũ, thống kê không? | Chiến lược gán nhãn |
| Người dùng cuối | Chuyên gia GIS, cán bộ quản lý hay nông dân | Giao diện, mức độ diễn giải |

Nguyên tắc chọn độ phân giải: đối tượng cần chiếm ít nhất khoảng 3×3 đến 5×5 pixel để mô hình phát hiện ổn định, và nhiều hơn nếu cần đường viền chính xác.

## 4. Dữ liệu đầu vào: cảm biến, nguồn, định dạng và tiền xử lý

Với đa số ứng dụng ở vùng nhiệt đới, cặp Sentinel-1 + Sentinel-2 miễn phí là nền tảng; ảnh thương mại độ phân giải cao chỉ cần khi đối tượng nhỏ hơn khoảng 30 m. Trên Sentinel-1, chòm vệ tinh đã được thay mới: [Sentinel-1A kết thúc hoạt động ngày 30/6/2026, Sentinel-1C và 1D đảm nhiệm cho thập kỷ tới](https://dataspace.copernicus.eu/news/2026-6-30-copernicus-sentinel-1a-satellite-end-operations-after-12-years-service). Dữ liệu radar L-band của NISAR cũng đã mở: [bản phát hành công khai đầu tiên bắt đầu ngày 20/7/2026, toàn bộ hồ sơ khoa học dự kiến có trước cuối 2026](https://www.earthdata.nasa.gov/data/alerts-outages/nisar-l-band-data-now-publicly-available).

### 4.1. Cảm biến và nguồn ảnh

| Cảm biến | Loại | Độ phân giải không gian | Chu kỳ lặp | Chi phí | Phù hợp cho |
| --- | --- | --- | --- | --- | --- |
| Sentinel-2 (2B, 2C) | Quang học 13 kênh | 10 / 20 / 60 m | \~5 ngày | Miễn phí | Lớp phủ, nông nghiệp, nước, cháy |
| Sentinel-1 (1C, 1D) | SAR băng C, VV+VH | \~5×20 m (IW) | 6 ngày với 2 vệ tinh | Miễn phí | Ngập lụt, lúa, tàu, InSAR |
| Landsat 8/9 | Quang học + nhiệt | 30 m (nhiệt 100 m) | 8 ngày với 2 vệ tinh | Miễn phí | Chuỗi dài từ 1984, nhiệt độ bề mặt |
| HLS (Harmonized Landsat Sentinel-2) | Quang học đã đồng bộ | 30 m | 2–3 ngày | Miễn phí | Chuỗi thời gian dày, đầu vào của Prithvi |
| NISAR | SAR băng L (NASA) + S (ISRO) | \~3–10 m tùy chế độ | 12 ngày | Miễn phí (L qua ASF, S qua Bhoonidhi) | Sinh khối rừng, độ ẩm, biến dạng bề mặt |
| MODIS / VIIRS | Quang học, nhiệt, đèn đêm | 250–1000 m | Hàng ngày | Miễn phí | Cháy, đèn đêm, quy mô lớn |
| GEDI | LiDAR không gian, điểm đo thưa | Vết đo \~25 m | Không liên tục | Miễn phí | Nhãn chiều cao tán, sinh khối |
| EnMAP, PRISMA | Siêu phổ \~230 kênh | 30 m | Theo đặt chụp | Miễn phí cho nghiên cứu | Khoáng sản, chất lượng nước |
| Copernicus DEM GLO-30 | Mô hình số độ cao | 30 m | Tĩnh | Miễn phí | Đặc trưng địa hình, hiệu chỉnh SAR |
| PlanetScope | Quang học 8 kênh | \~3 m | Hàng ngày | Thương mại | Giám sát dày đặc, thửa nhỏ |
| Maxar WorldView/Legion, Pléiades Neo | Quang học VHR | 0,3–0,5 m | Theo đặt chụp | Thương mại | Nhà, xe, tàu, hạ tầng |
| ICEYE, Capella, Umbra | SAR băng X | < 1 m | Theo đặt chụp | Thương mại | Giám sát nhanh mọi thời tiết |
| VNREDSat-1 | Quang học | 2,5 m toàn sắc, 10 m đa phổ | Theo đặt chụp | Liên hệ VNSC | Nguồn trong nước |

Vệ tinh radar LOTUSat-1 của Việt Nam (băng X, \~1 m) đã chế tạo xong nhưng lịch phóng bị lùi; [phía Nhật Bản đặt mục tiêu phóng năm 2027](https://news.tuoitre.vn/japan-aims-for-2027-launch-of-vietnams-lotusat-1-earth-observation-satellite-103260504134743019.htm). Kiến trúc ứng dụng nên để sẵn đầu nối cho nguồn này.

### 4.2. Nơi truy cập dữ liệu

| Nền tảng | Có gì | Cách truy cập |
| --- | --- | --- |
| Copernicus Data Space Ecosystem | Toàn bộ Sentinel, Copernicus DEM | STAC API, openEO, Sentinel Hub, JupyterLab |
| Microsoft Planetary Computer | Sentinel-1 RTC, Sentinel-2 L2A, Landsat, HLS, DEM dạng COG | STAC API + `pystac-client` |
| AWS Open Data (Earth Search) | Sentinel-2 COG, Landsat, Copernicus DEM | STAC API, đọc trực tiếp từ S3 |
| Google Earth Engine | Kho dữ liệu lớn nhất, có sẵn vector nhúng AlphaEarth | Python/JavaScript API, xử lý trên mây |
| NASA Earthdata / ASF DAAC | HLS, NISAR, GEDI, Sentinel-1 lưu trữ | Earthdata Search, `asf_search`, `earthaccess` |
| ISRO Bhoonidhi | NISAR S-band, EOS-04 | STAC API, giao diện web |

### 4.3. Định dạng chuẩn nên dùng

- **Cloud-Optimized GeoTIFF (COG):** GeoTIFF có cấu trúc tile và overview, đọc được từng phần qua HTTP. Dùng cho mọi raster đầu vào và đầu ra của mô hình.
- **STAC (SpatioTemporal Asset Catalog):** chuẩn mô tả và tìm kiếm ảnh theo không gian, thời gian, thuộc tính. Nên dùng cho cả ảnh nguồn lẫn sản phẩm dự đoán của bạn; extension `ml-model` mô tả mô hình.
- **Zarr + xarray:** lưu khối dữ liệu nhiều chiều (x, y, thời gian, kênh), phù hợp chuỗi thời gian lớn.
- **GeoParquet / FlatGeobuf:** lưu vector (footprint, thửa ruộng) dung lượng lớn, đọc nhanh hơn Shapefile nhiều.
- **PMTiles / vector tiles:** phục vụ vector lên bản đồ web không cần máy chủ tile.

### 4.4. Tiền xử lý

**Ảnh quang học:**

1. Dùng sản phẩm phản xạ bề mặt (Sentinel-2 L2A, Landsat Collection 2 Level-2) thay vì tự hiệu chỉnh khí quyển.
2. Che mây và bóng mây: lớp SCL của Sen2Cor, s2cloudless, Fmask, hoặc mô hình học sâu huấn luyện trên CloudSEN12. Với vùng nhiệt đới, bước này quyết định chất lượng nhiều hơn mô hình.
3. Đưa về cùng hệ tọa độ và lưới pixel (UTM 48N/49N cho Việt Nam), resample kênh 20 m về 10 m.
4. Tổng hợp theo thời gian (median theo tháng hoặc theo vụ) để có ảnh không mây.
5. Chuẩn hóa theo đúng thống kê mà mô hình đã tiền huấn luyện sử dụng. Lưu ý Sentinel-2 từ baseline 04.00 (01/2022) có offset -1000 trong giá trị DN.

**Ảnh SAR (Sentinel-1 GRD):**

1. Áp file quỹ đạo chính xác, loại nhiễu nhiệt và nhiễu biên.
2. Hiệu chỉnh bức xạ về σ⁰ hoặc γ⁰.
3. Làm phẳng địa hình (terrain flattening) và nắn chỉnh địa hình bằng DEM, ra sản phẩm RTC.
4. Lọc speckle (Lee, Refined Lee, Gamma-MAP) hoặc để mô hình tự học; chuyển sang dB.

Có thể bỏ qua các bước trên bằng cách dùng sản phẩm RTC có sẵn (ví dụ Sentinel-1 RTC trên Planetary Computer). Công cụ tự xử lý: ESA SNAP (`esa_snappy`), pyroSAR, ISCE3 cho NISAR.

**Cắt mảnh (tiling) cho huấn luyện:** mảnh 256×256 hoặc 512×512 pixel, chồng lấn 10–25% khi suy luận để tránh viền xấu, giữ giá trị NoData riêng và loại nó khỏi hàm mất mát.

## 5. Mô hình toán lý

Mô hình vật lý làm ba việc trong một ứng dụng GeoAI: chuẩn hóa dữ liệu đầu vào, tạo đặc trưng có ý nghĩa, và ràng buộc hoặc sinh dữ liệu cho mô hình học. Bỏ qua chúng thường làm mô hình học sâu tổng quát kém khi đổi mùa, đổi cảm biến hoặc đổi vùng.

| Nhóm | Mô hình / phương pháp | Dùng để làm gì | Công cụ |
| --- | --- | --- | --- |
| Truyền bức xạ khí quyển | 6S, MODTRAN, libRadtran | Hiệu chỉnh khí quyển, mô phỏng tín hiệu cảm biến | Py6S, Sen2Cor, LaSRC |
| Truyền bức xạ thực vật | PROSPECT + SAIL (PROSAIL) | Sinh dữ liệu mô phỏng để ước lượng LAI, diệp lục, hàm lượng nước | prosail (Python), ARTMO |
| Chỉ số phổ | NDVI, EVI, SAVI, NDWI, MNDWI, NDBI, NBR, NDRE | Đặc trưng đầu vào, ngưỡng đơn giản, kiểm tra chéo | spyndex, GEE |
| Tán xạ radar | Water Cloud Model, IEM, Oh, Dubois | Ước lượng độ ẩm đất, sinh khối từ SAR | Tự cài đặt, SNAP |
| Phân tích phân cực | Freeman-Durden, Yamaguchi, H/A/α | Phân biệt tán xạ bề mặt, thể tích, hai lần nảy | SNAP, PolSARpro |
| Giao thoa radar | DInSAR, PS-InSAR, SBAS | Đo sụt lún, biến dạng mức mm–cm | ISCE3, MintPy, SNAP, HyP3 |
| Tách phổ hỗn hợp | Mô hình trộn tuyến tính (LMM), NMF, VCA | Tỷ lệ thành phần trong pixel hỗn hợp | PySptools, scikit-learn |
| Biến đổi ảnh | PCA, MNF, Tasseled Cap, wavelet, Fourier | Giảm chiều, khử nhiễu, làm nổi đặc trưng | scikit-learn, PyWavelets |
| Thống kê không gian | Variogram, Kriging, Moran’s I, GWR | Nội suy dữ liệu đo, kiểm tra tự tương quan, hồi quy theo vùng | PyKrige, PySAL, mgwr |
| Chuỗi thời gian | Hồi quy điều hòa, BFAST, LandTrendr, CCDC, lọc Savitzky-Golay | Phát hiện điểm gãy, làm mượt, trích xuất phenology | GEE, bfast, TIMESAT |
| Cân bằng năng lượng bề mặt | SEBAL, METRIC, SEBS | Bốc thoát hơi nước, stress nước cây trồng | pyMETRIC, GEE |
| Hình học cảm biến | Mô hình RPC, nắn chỉnh trực giao | Đưa ảnh thô về đúng vị trí bản đồ | GDAL, OTB |

### 5.1. Một số công thức cốt lõi

Chỉ số thực vật NDVI và chỉ số nước MNDWI (ρ là phản xạ bề mặt tại kênh tương ứng):

```latex
\mathrm{NDVI} = \frac{\rho_{NIR} - \rho_{Red}}{\rho_{NIR} + \rho_{Red}}, \qquad \mathrm{MNDWI} = \frac{\rho_{Green} - \rho_{SWIR1}}{\rho_{Green} + \rho_{SWIR1}}
```

Water Cloud Model, chia tán xạ ngược thành phần thực vật và phần đất bị thực vật suy giảm (V₁, V₂ là biến mô tả thực vật, θ là góc tới, A, B là tham số hiệu chỉnh):

```latex
\sigma^0 = A V_1 \cos\theta \left(1 - \gamma^2\right) + \gamma^2 \sigma^0_{soil}, \qquad \gamma^2 = \exp\left(\frac{-2 B V_2}{\cos\theta}\right)
```

Mô hình trộn phổ tuyến tính (x là phổ pixel, M là ma trận phổ thành phần thuần, a là tỷ lệ thành phần):

```latex
\mathbf{x} = \mathbf{M}\mathbf{a} + \mathbf{n}, \qquad a_i \ge 0, \quad \sum_i a_i = 1
```

Dịch chuyển theo hướng nhìn của radar từ pha giao thoa (λ là bước sóng, khoảng 5,55 cm với Sentinel-1 và 24 cm với NISAR L-band):

```latex
d_{LOS} = -\frac{\lambda}{4\pi}\,\Delta\phi
```

### 5.2. Kết hợp vật lý với học máy

- **Vật lý làm đặc trưng:** đưa chỉ số phổ, tỷ số VH/VV, độ dốc, hướng dốc vào mô hình cùng các kênh gốc. Cách đơn giản nhất và luôn nên thử trước.
- **Mô hình vật lý sinh dữ liệu huấn luyện:** chạy PROSAIL hàng triệu lần với tham số ngẫu nhiên, rồi huấn luyện mạng nơ-ron nghịch đảo từ phổ ra LAI. Đây là cách bộ xử lý sinh-vật lý của SNAP hoạt động.
- **Mạng nơ-ron có ràng buộc vật lý (physics-informed):** thêm số hạng phạt vào hàm mất mát khi dự đoán vi phạm quy luật vật lý (ví dụ cân bằng năng lượng, giới hạn giá trị).
- **Mô hình lai (hybrid):** mạng nơ-ron học tham số của một mô hình vật lý khả vi, giữ được khả năng diễn giải.

## 6. Học máy cổ điển

Học máy cổ điển vẫn là lựa chọn đúng cho phân loại theo pixel trên ảnh 10–30 m khi có ít hơn vài nghìn mẫu nhãn. Nó cũng là cách dùng hiệu quả nhất các vector nhúng Trái Đất tính sẵn (mục 8). Luôn xây một baseline Random Forest trước khi đầu tư vào học sâu: nếu học sâu không vượt baseline rõ rệt, hãy giữ cái đơn giản.

| Thuật toán | Loại | Khi nào dùng | Lưu ý |
| --- | --- | --- | --- |
| Random Forest | Phân loại / hồi quy | Mặc định cho bản đồ lớp phủ trên GEE; bền với nhiễu và ít nhãn | Có độ quan trọng đặc trưng; không tận dụng ngữ cảnh không gian |
| XGBoost, LightGBM, CatBoost | Phân loại / hồi quy | Dữ liệu bảng nhiều đặc trưng, ước lượng năng suất, sinh khối | Thường chính xác hơn RF nhưng cần tinh chỉnh siêu tham số |
| SVM | Phân loại | Mẫu ít, đặc trưng nhiều chiều (siêu phổ) | Chậm khi mẫu lớn |
| Maximum Likelihood, k-NN | Phân loại | Baseline truyền thống, giảng dạy | Giả định phân phối chuẩn (ML) |
| K-means, ISODATA, GMM | Không giám sát | Khám phá dữ liệu, hỗ trợ gán nhãn, khi chưa có nhãn | Cụm không tự có ngữ nghĩa |
| OBIA (phân đoạn + phân loại) | Hướng đối tượng | Ảnh độ phân giải cao, cần đặc trưng hình dạng và kết cấu | SLIC, Felzenszwalb, SNIC (GEE) để tạo đối tượng |
| Gaussian Process Regression | Hồi quy | Ước lượng tham số sinh-vật lý kèm độ bất định | Khó mở rộng quá vài chục nghìn mẫu |
| MRF, CRF | Hậu xử lý | Làm mượt kết quả theo ngữ cảnh không gian | Cũng dùng sau mạng học sâu |
| Isolation Forest, One-class SVM | Phát hiện bất thường | Tìm sự kiện hiếm (khai thác trái phép, cháy) khi không có nhãn | Cần chuyên gia xác minh |

### 6.1. Đặc trưng đầu vào nên xây

- **Phổ:** các kênh phản xạ gốc và chỉ số phổ (mục 5).
- **Radar:** VV, VH (dB), tỷ số VH/VV, độ kết hợp (coherence) giữa hai lần chụp.
- **Thời gian:** thống kê theo mùa (min, max, median, phân vị), hệ số hồi quy điều hòa, ngày đạt đỉnh NDVI.
- **Kết cấu:** GLCM (contrast, entropy, homogeneity) trên cửa sổ 3×3 đến 7×7.
- **Địa hình và phụ trợ:** độ cao, độ dốc, khoảng cách tới sông hoặc đường, lượng mưa.
- **Vector nhúng có sẵn:** 64 chiều AlphaEarth hoặc 128 chiều OlmoEarth thay cho toàn bộ các đặc trưng trên khi cần triển khai nhanh.

Ví dụ quy trình RF trên Google Earth Engine: tổng hợp median Sentinel-2 theo vụ + median Sentinel-1 + DEM → lấy mẫu tại điểm nhãn → `ee.Classifier.smileRandomForest(200)` → đánh giá bằng ma trận nhầm lẫn trên tập kiểm tra tách theo không gian → xuất COG.

## 7. Học sâu theo từng bài toán

Với đa số bài toán năm 2026, cách làm hiệu quả nhất là chọn một kiến trúc đã được kiểm chứng (U-Net, UPerNet, YOLO, Siamese) và gắn nó vào một backbone đã tiền huấn luyện trên ảnh vệ tinh, thay vì tự thiết kế mạng mới. Bảng dưới đây liệt kê kiến trúc theo bài toán, kèm lựa chọn khởi đầu được khuyến nghị.

| Bài toán | Kiến trúc tiêu biểu | Khởi đầu khuyến nghị | Ưu điểm / hạn chế |
| --- | --- | --- | --- |
| Backbone trích xuất đặc trưng | ResNet, EfficientNet, ConvNeXt, ViT, Swin Transformer | ResNet-50 hoặc ViT tiền huấn luyện trên SSL4EO-S12 / mô hình nền tảng | CNN nhẹ, dễ triển khai; ViT mạnh khi có tiền huấn luyện tốt |
| Phân loại cảnh | ResNet, EfficientNet, ViT | Fine-tune backbone + lớp phân loại tuyến tính | Đơn giản nhất; ít khi là sản phẩm cuối |
| Phân đoạn ngữ nghĩa | U-Net (và biến thể U-Net++, Attention U-Net), DeepLabv3+, HRNet, UPerNet, SegFormer, Mask2Former | U-Net + ResNet-50 (baseline), UPerNet + backbone mô hình nền tảng | U-Net giữ biên tốt, học nhanh với ít dữ liệu; SegFormer nhẹ và chính xác |
| Phân đoạn theo lời nhắc | SAM, SAM 2, SAM 3; SegEarth-OV3 | samgeo + SAM 3 cho gán nhãn bán tự động và trích xuất theo cụm từ | Zero-shot tốt trên ảnh RGB độ phân giải cao; kém trên ảnh đa phổ 10 m |
| Phát hiện đối tượng | Faster R-CNN, RetinaNet, YOLO (YOLO11, YOLO26), RT-DETR, RF-DETR | YOLO26 (nhanh, xuất ONNX/TensorRT dễ) hoặc RF-DETR | One-stage nhanh; DETR mạnh với cảnh dày đặc |
| Phát hiện đối tượng xoay (OBB) | Oriented R-CNN, RoI Transformer, S2A-Net, ReDet, YOLO-OBB | YOLO26-OBB; MMRotate cho nghiên cứu | Bắt buộc với tàu, máy bay, xe nhìn từ trên xuống |
| Phân đoạn thực thể | Mask R-CNN, Cascade Mask R-CNN, YOLO-seg, Mask2Former | Mask R-CNN hoặc YOLO26-seg; hậu xử lý chính quy hóa đa giác nhà | Đầu ra vector trực tiếp cho GIS |
| Trích xuất đường | D-LinkNet, RoadTracer, Sat2Graph, RNGDet++ | D-LinkNet → skeleton hóa → đồ thị | Phân đoạn dễ nhưng đứt đoạn; mô hình đồ thị giữ liên thông |
| Phát hiện biến động | Siamese FC-EF/FC-Siam-diff, STANet, SNUNet, BIT, ChangeFormer, ChangeMamba | BIT hoặc ChangeFormer; hoặc encoder mô hình nền tảng dùng chung trọng số | Cần đồng đăng ký chính xác; dễ báo động giả do mùa, bóng |
| Chuỗi thời gian | LSTM, ConvLSTM, TempCNN, Transformer (PSE-TAE, U-TAE, TSViT) | U-TAE cho phân đoạn thửa theo chuỗi; TempCNN cho pixel | Khả năng xử lý chuỗi bị mây che, độ dài không đều |
| Hồi quy dày đặc | U-Net/UPerNet với đầu ra liên tục | U-Net + loss Huber, nhãn thưa GEDI | Cần xử lý nhãn thưa (chỉ tính loss tại điểm có nhãn) |
| Siêu phân giải | SRCNN, EDSR, ESRGAN, SwinIR, mô hình khuếch tán; đa ảnh (HighRes-net) | SwinIR hoặc mô hình đa ảnh huấn luyện trên WorldStrat | GAN/diffusion có thể “bịa” chi tiết; không dùng cho đo đạc |
| Loại mây, SAR → quang học | pix2pix, CycleGAN, DSen2-CR, mô hình khuếch tán, TerraMind (any-to-any) | DSen2-CR trên SEN12MS-CR; thử TerraMind | Kết quả sinh ra là ước lượng, cần gắn nhãn rõ cho người dùng |
| Siêu phổ | 3D-CNN, HybridSN, SpectralFormer | HybridSN (2D+3D) | Dataset nhỏ, dễ overfit |
| Đám mây điểm LiDAR | PointNet++, KPConv, RandLA-Net, Point Transformer v3 | RandLA-Net cho vùng lớn; PTv3 cho độ chính xác | Tốn bộ nhớ; cần chia khối |
| Dữ liệu dạng mạng lưới | GNN (GCN, GAT, GraphSAGE) | GraphSAGE trên đồ thị thửa ruộng hoặc đường | Khai thác quan hệ lân cận ngoài lưới pixel |
| Thị giác-ngôn ngữ | RemoteCLIP, GeoRSCLIP, GeoChat, EarthDial, SkySenseGPT | RemoteCLIP cho tìm kiếm ảnh bằng văn bản; VLM đa năng cho hỏi đáp | Đếm và định vị chính xác còn yếu; nên kết hợp với mô hình chuyên dụng |

### 7.1. Gợi ý lựa chọn theo tình huống

- **Ít nhãn (dưới \~500 mảnh):** tinh chỉnh mô hình nền tảng với encoder đóng băng hoặc LoRA, hoặc dùng vector nhúng + RF.
- **Ảnh đa phổ 10–30 m:** ưu tiên backbone tiền huấn luyện trên Sentinel/HLS (Prithvi, OlmoEarth, Clay, SSL4EO). Trọng số ImageNet chỉ dùng được cho 3 kênh RGB.
- **Ảnh RGB độ phân giải cao:** backbone ImageNet / DINOv2 / DINOv3 vẫn rất tốt; YOLO26 và SAM 3 phát huy hiệu quả.
- **Cần chạy trên thiết bị biên hoặc CPU:** YOLO26n/s, SegFormer-B0, xuất ONNX + lượng tử hóa INT8.
- **Vùng nhiều mây:** mô hình đa phương thức nhận cả Sentinel-1 và Sentinel-2 (hợp nhất sớm bằng ghép kênh, hoặc hợp nhất muộn bằng hai encoder).

## 8. Mô hình nền tảng (foundation models) cho quan sát Trái Đất

Mô hình nền tảng giúp giảm mạnh lượng nhãn cần thiết, nhưng chưa có mô hình nào thắng trên mọi bài toán, nên hãy thử 2–3 mô hình trên chính dữ liệu của bạn. Một khảo sát 152 bài báo năm 2026 cho thấy [các bài chênh nhau từ 10 điểm trở lên ở 46 trường hợp cho cùng mô hình và benchmark, và 39% bài không công bố trọng số](https://arxiv.org/html/2605.12678), nên bảng xếp hạng trong bài báo chỉ nên dùng để lập danh sách ngắn.

### 8.1. Các mô hình chính

| Mô hình | Đơn vị | Dữ liệu đầu vào | Quy mô | Giấy phép | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [Prithvi-EO-2.0](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL) | NASA, IBM, Jülich | HLS 30 m, 6 kênh, đa thời điểm | 300M và 600M tham số; bản TL có nhúng thời gian và vị trí | Apache-2.0 | Tiền huấn luyện trên 4,2 triệu mẫu HLS; tinh chỉnh qua TerraTorch |
| [TerraMind 1.0](https://huggingface.co/ibm-esa-geospatial/TerraMind-1.0-large) | IBM, ESA | 9 phương thức (S2 L1C/L2A, S1 GRD/RTC, DEM, LULC, NDVI, tọa độ, chú thích…) | tiny, small, base, large | Apache-2.0 | Sinh được phương thức còn thiếu (any-to-any); tiền huấn luyện trên 500 tỷ token từ 9 triệu mẫu TerraMesh |
| [OlmoEarth v1.3](https://allenai.org/earth-system) | Ai2 | Sentinel-1, Sentinel-2, Landsat, chuỗi thời gian | ViT-Base 128M tham số | OlmoEarth Artifact License | Công bố cả vector nhúng toàn cầu 128 và 64 chiều (10/2026); có nền tảng huấn luyện và triển khai |
| [AlphaEarth Foundations](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL) | Google DeepMind | Quang học, radar, LiDAR và nguồn khác | Chỉ công bố vector nhúng, không công bố trọng số | Vector nhúng CC-BY 4.0 | Vector 64 chiều, 10 m, theo năm từ 2017; đã chuẩn hóa độ dài 1; trên GEE và GCS |
| Clay v1.5 | Clay Foundation | Đa cảm biến, số kênh linh hoạt | ViT, MAE | Mã nguồn mở (xem model card) | Mã hóa cả vĩ độ, kinh độ, thời gian; chạy ở độ phân giải gốc của cảm biến |
| Galileo, TESSERA, Copernicus-FM, DOFA, Panopticon, AnySat | Các nhóm nghiên cứu | Đa phương thức, số kênh linh hoạt | Khác nhau | Xem model card | Đáng thử khi cần kênh hoặc cảm biến mà các mô hình trên không hỗ trợ |
| SatMAE, Scale-MAE, CROMA, SSL4EO-S12 | Thế hệ 2022–2023 | Sentinel-2, S1+S2, RGB VHR | ResNet/ViT | Chủ yếu mở | Baseline tốt, nhẹ; có sẵn trong TorchGeo |
| DINOv2 / DINOv3 | Meta | Ảnh RGB (DINOv3 có bản tiền huấn luyện trên ảnh vệ tinh) | ViT nhiều cỡ | Xem giấy phép Meta | Mạnh cho ảnh RGB độ phân giải cao; yếu hơn mô hình EO trên ảnh đa phổ |

### 8.2. Bốn cách dùng mô hình nền tảng (từ rẻ đến đắt)

1. **Dùng vector nhúng tính sẵn + học máy cổ điển.** Lấy vector AlphaEarth hoặc OlmoEarth tại điểm nhãn, huấn luyện RF/k-NN/MLP. Không cần GPU, làm được trong vài giờ. Hạn chế: một vector mỗi năm, không tinh chỉnh được, không phù hợp bài toán theo tuần hoặc đối tượng nhỏ hơn 10 m.
2. **Đóng băng encoder, huấn luyện decoder.** Encoder mô hình nền tảng + decoder UPerNet hoặc UNet nhẹ. Cần một GPU 16–24 GB, ít nhãn.
3. **Tinh chỉnh hiệu quả tham số (LoRA, adapter).** Cập nhật 1–5% tham số, thường gần bằng tinh chỉnh toàn phần.
4. **Tinh chỉnh toàn phần.** Chính xác nhất khi có hàng nghìn mảnh nhãn; tốn tài nguyên, dễ overfit nếu nhãn ít.

### 8.3. Tiêu chí chọn mô hình

- **Khớp cảm biến và kênh:** Prithvi cần đúng 6 kênh HLS; TerraMind, OlmoEarth nhận cả Sentinel-1.
- **Khớp độ phân giải:** mô hình huấn luyện ở 10–30 m thường kém trên ảnh 0,5 m và ngược lại.
- **Chiều thời gian:** bài toán cây trồng và biến động cần mô hình nhận chuỗi ảnh.
- **Giấy phép:** kiểm tra có cho phép dùng thương mại không trước khi xây sản phẩm.
- **Chi phí suy luận:** mô hình 600M tham số chạy toàn quốc theo tuần có thể tốn kém; cân nhắc chưng cất (distill) sang mô hình nhỏ.
- **Đánh giá trên dữ liệu của bạn:** benchmark công khai gồm GEO-Bench / GEO-Bench-2, PANGAEA và EarthShift (đo độ bền khi dữ liệu lệch phân phối), nhưng kết quả trên tập kiểm tra địa phương mới là quyết định.

## 9. Dataset huấn luyện cho từng loại mô hình học sâu

Dataset công khai dùng cho ba việc: tiền huấn luyện hoặc khởi động mô hình, kiểm tra pipeline chạy đúng, và so sánh với kết quả đã công bố. Chúng hiếm khi đủ để triển khai trực tiếp ở Việt Nam vì phần lớn được thu thập ở châu Âu, Mỹ và Trung Quốc. Nhiều bộ chỉ cho phép dùng phi thương mại (đánh dấu NC bên dưới): hãy kiểm tra giấy phép trước khi dùng cho sản phẩm.

| Bài toán / loại mô hình | Dataset | Cảm biến, độ phân giải | Quy mô và nội dung | Giấy phép |
| --- | --- | --- | --- | --- |
| Phân loại cảnh (CNN, ViT) | EuroSAT | Sentinel-2, 13 kênh | 27.000 mảnh, 10 lớp | MIT |
|  | BigEarthNet v2 (reBEN) | Sentinel-1 + Sentinel-2 | \~550.000 cặp mảnh, đa nhãn 19 lớp | CDLA-Permissive |
|  | NWPU-RESISC45, AID, UC Merced | RGB 0,2–30 m | 31.500 / 10.000 / 2.100 ảnh | Kiểm tra |
|  | fMoW, So2Sat LCZ42 | RGB VHR; S1+S2 | 1 triệu+ ảnh, 62 lớp chức năng; 17 lớp vùng khí hậu đô thị | Kiểm tra |
| Phân đoạn lớp phủ (U-Net, SegFormer, UPerNet) | LoveDA | RGB 0,3 m | 5.987 ảnh, 7 lớp, cả đô thị và nông thôn | NC |
|  | OpenEarthMap | RGB 0,25–0,5 m | 5.000 ảnh, 8 lớp, 97 vùng thuộc 44 nước | NC |
|  | ISPRS Vaihingen / Potsdam | IRRG/RGB + DSM, 5–9 cm | Benchmark kinh điển 6 lớp | Kiểm tra |
|  | DeepGlobe Land Cover, GID / Five-Billion-Pixels | RGB 0,5 m; Gaofen-2 4 m | 7 lớp; 15–24 lớp | Kiểm tra |
|  | SEN12MS, Dynamic World (điểm huấn luyện) | Sentinel-1/2 10 m | 180.000 bộ ba S1/S2/MODIS; 9 lớp toàn cầu | Kiểm tra |
| Footprint nhà (Mask R-CNN, U-Net) | SpaceNet 1–8 | WorldView 0,3–0,5 m, SAR | Hàng trăm nghìn footprint nhiều thành phố | CC BY-SA 4.0 |
|  | Inria Aerial, WHU Building | RGB 0,3 m | 810 km²; 220.000 nhà | Kiểm tra |
| Trích xuất đường | DeepGlobe Road, Massachusetts Roads, CityScale | RGB 0,5–1 m | Mặt nạ đường; đồ thị đường (CityScale) | Kiểm tra |
| Phát hiện đối tượng (YOLO, DETR, Oriented R-CNN) | DOTA v1.0 / 1.5 / 2.0 | RGB 0,1–4,5 m | 11.268 ảnh, 18 lớp, 1,8 triệu hộp xoay (v2.0) | Chỉ học thuật |
|  | DIOR / DIOR-R | RGB 0,5–30 m | 23.463 ảnh, 20 lớp, hộp thẳng và xoay | Kiểm tra |
|  | xView | WorldView-3 0,3 m | 1 triệu đối tượng, 60 lớp | NC |
|  | FAIR1M | Gaofen 0,3–0,8 m | 1 triệu+ đối tượng, 37 lớp chi tiết, hộp xoay | Kiểm tra |
|  | HRSC2016, ShipRSImageNet | RGB VHR | Tàu, hộp xoay, phân cấp loại tàu | Kiểm tra |
| Phát hiện tàu trên SAR | xView3-SAR | Sentinel-1 | 1.000 cảnh, tàu không phát AIS, phân biệt tàu cá | Kiểm tra |
|  | SSDD, HRSID, OpenSARShip | Sentinel-1, TerraSAR-X | Chip tàu, hộp bao và mặt nạ | Kiểm tra |
| Phát hiện biến động (Siamese, BIT, ChangeFormer) | LEVIR-CD / LEVIR-CD+ | Google Earth 0,5 m | 637 / 985 cặp ảnh, biến động nhà | Chỉ học thuật |
|  | WHU-CD, SYSU-CD, CDD, DSIFN | RGB 0,075–1 m | Biến động nhà, đường, thực vật | Kiểm tra |
|  | S2Looking | VHR chụp xiên | 5.000 cặp, nông thôn, góc nhìn khác nhau | Kiểm tra |
|  | OSCD | Sentinel-2 | 24 cặp, biến động đô thị | Kiểm tra |
|  | SECOND | RGB 0,5–3 m | 4.662 cặp, biến động có ngữ nghĩa (từ lớp nào sang lớp nào) | Kiểm tra |
| Đánh giá thiệt hại, thiên tai | xBD (xView2) | Maxar 0,3–0,8 m | 850.000 nhà, 4 mức thiệt hại, 19 sự kiện | NC |
|  | Sen1Floods11 | Sentinel-1 + Sentinel-2 | 4.831 mảnh, 11 sự kiện lũ trên 6 châu lục | CC BY 4.0 |
|  | MMFlood, Landslide4Sense, CaBuAr | S1, S2, DEM | Ngập lụt; sạt lở; vùng cháy | Kiểm tra |
| Chuỗi thời gian cây trồng (U-TAE, TSViT, LSTM) | PASTIS / PASTIS-R | Chuỗi Sentinel-2 (+ S1) | 2.433 mảnh, 18 lớp, nhãn panoptic từng thửa | CC BY 4.0 |
|  | BreizhCrops, EuroCrops, Sen4AgriNet, TimeSen2Crop | Chuỗi Sentinel-2 | Hàng triệu thửa ruộng châu Âu | Kiểm tra |
|  | CropHarvest, AgriFieldNet | S1, S2, khí tượng | \~90.000 điểm toàn cầu; thửa nhỏ Ấn Độ | Kiểm tra |
|  | PLANTEUR | Sentinel / Landsat | Loại cây trồng nhiệt đới (các vùng hải ngoại của Pháp), công bố cùng OlmoEarth v1.3 | Kiểm tra |
| Che mây, loại mây (U-Net, GAN, diffusion) | CloudSEN12 / CloudSEN12+ | Sentinel-2 | 49.400 mảnh, mặt nạ mây dày, mỏng, bóng | Kiểm tra |
|  | 38-Cloud / 95-Cloud, L8 Biome | Landsat 8 | Mặt nạ mây | Kiểm tra |
|  | SEN12MS-CR, SEN12MS-CR-TS | S1 + S2 có mây và không mây | Cặp huấn luyện loại mây; bản chuỗi thời gian | Kiểm tra |
| Hợp nhất SAR–quang học | SEN1-2, SpaceNet 6 | S1 + S2; SAR độ phân giải cao + quang học | 282.000 cặp; footprint nhà trên SAR | Kiểm tra |
| Siêu phân giải (SwinIR, đa ảnh) | WorldStrat | Sentinel-2 + SPOT 1,5 m | \~10.000 km², nhiều thời điểm cho mỗi vị trí | Kiểm tra (ảnh SPOT hạn chế) |
|  | SEN2VENµS, PROBA-V, OLI2MSI | S2 + VENµS; Landsat + S2 | Cặp thấp–cao cùng thời điểm | Kiểm tra |
| Siêu phổ (3D-CNN, SpectralFormer) | Indian Pines, Pavia University, Salinas, Houston 2013/2018, WHU-Hi | AVIRIS, ROSIS, CASI, UAV | 100–270 kênh, vài chục nghìn pixel nhãn | Kiểm tra |
| Đám mây điểm (PointNet++, KPConv, RandLA-Net) | DALES, SensatUrban, Toronto-3D, ISPRS Vaihingen 3D, H3D | LiDAR hàng không / UAV | Hàng trăm triệu điểm, 8–13 lớp | Kiểm tra |
| Hồi quy sinh khối, chiều cao tán | BioMassters | Chuỗi S1 + S2 | 13.000 mảnh rừng Phần Lan, nhãn từ LiDAR | Kiểm tra |
|  | GEDI L2A / L4A | LiDAR không gian | Hàng tỷ điểm đo chiều cao và sinh khối, dùng làm nhãn thưa | Mở (NASA) |
| Tiền huấn luyện tự giám sát | SSL4EO-S12, Major TOM, SatlasPretrain, TerraMesh, MillionAID | S1, S2, Landsat, NAIP, VHR | 250.000 đến hàng chục triệu mảnh, ít hoặc không nhãn | Phần lớn mở |
| Thị giác-ngôn ngữ | RSICD, UCM-Captions, RSVQA, RS5M, SkyScript, GeoChat-Instruct | RGB nhiều độ phân giải | Cặp ảnh–văn bản, hỏi–đáp, chỉ dẫn | Kiểm tra |

Phần lớn các bộ trên đã có trình nạp dữ liệu sẵn trong TorchGeo (hơn 50 benchmark, tự tải về) và TerraTorch, giúp tiết kiệm nhiều ngày viết mã đọc dữ liệu. Số liệu quy mô lấy theo bài báo gốc và có thể thay đổi giữa các phiên bản.

## 10. Xây dựng dataset riêng

Tập nhãn địa phương là tài sản quan trọng nhất của một ứng dụng GeoAI, và phần quan trọng nhất trong đó là tập kiểm tra độc lập, được lấy mẫu khách quan. Nên dành 25–40% công sức của dự án cho dữ liệu và nhãn.

### 10.1. Nguồn nhãn

| Nguồn | Ví dụ | Độ tin cậy | Cách dùng |
| --- | --- | --- | --- |
| Khảo sát thực địa | Điểm GPS + ảnh chụp qua KoboToolbox, ODK, QField | Cao nhất | Tập kiểm tra, kiểm định lớp khó phân biệt bằng mắt |
| Giải đoán ảnh bởi chuyên gia | Vẽ đa giác trên ảnh VHR, Google Earth lịch sử | Cao nếu có hướng dẫn rõ | Tập huấn luyện chính |
| Bản đồ chuyên đề có sẵn | Bản đồ hiện trạng sử dụng đất, kiểm kê rừng, thống kê nông nghiệp | Trung bình (có thể cũ hoặc sai vị trí) | Nhãn yếu, lọc lại trước khi dùng |
| Sản phẩm toàn cầu | ESA WorldCover, Dynamic World, Google Open Buildings, Microsoft Building Footprints, OpenStreetMap, Overture Maps | Trung bình, khác nhau theo vùng | Tiền huấn luyện, nhãn yếu, đối chứng |
| Nhãn từ cảm biến khác | GEDI cho chiều cao tán, LiDAR UAV, dữ liệu AIS cho tàu | Cao nhưng thưa | Nhãn thưa cho hồi quy, tự động gán nhãn tàu |
| Gán nhãn bán tự động | SAM 3 / samgeo tạo mặt nạ, người sửa | Phụ thuộc người kiểm tra | Tăng tốc vẽ footprint, ao hồ, thửa ruộng |

### 10.2. Công cụ gán nhãn

- **QGIS:** vẽ đa giác trực tiếp trên raster có tọa độ, xuất GeoPackage. Miễn phí, phù hợp nhóm GIS. Các plugin hỗ trợ SAM giúp vẽ nhanh hơn.
- **Google Earth Engine:** đặt điểm nhãn trên ảnh tổng hợp nhiều thời điểm, rất tiện cho bài toán phân loại theo pixel.
- **CVAT, Label Studio:** gán nhãn theo nhóm, có quy trình duyệt, hỗ trợ hộp xoay và đa giác; cần cắt ảnh thành mảnh và giữ file ánh xạ tọa độ.
- **GroundWork, Roboflow:** nền tảng thương mại/miễn phí một phần, có hỗ trợ ảnh vệ tinh.

### 10.3. Chiến lược lấy mẫu

1. **Lấy mẫu ngẫu nhiên phân tầng** theo lớp, vùng sinh thái hoặc đơn vị hành chính cho tập kiểm tra. Đây là điều kiện để ước tính diện tích không chệch theo phương pháp của Olofsson và cộng sự (2014).
2. **Tập huấn luyện có thể lệch có chủ đích:** bổ sung mẫu cho lớp hiếm và vùng dễ nhầm (ruộng bỏ hoang vs đất trống, ao nuôi vs ruộng ngập).
3. **Học chủ động (active learning):** huấn luyện mô hình đầu tiên, chạy trên vùng lớn, gán nhãn thêm chỗ mô hình không chắc chắn nhất, lặp lại.
4. **Chống rò rỉ dữ liệu:** chia tập train/val/test theo khối không gian (ví dụ ô lưới 10×10 km hoặc theo huyện) trước khi cắt mảnh, không chia ngẫu nhiên từng mảnh.

### 10.4. Quy mô tham khảo

| Cách tiếp cận | Lượng nhãn khởi điểm hợp lý |
| --- | --- |
| Vector nhúng + Random Forest | Vài trăm đến vài nghìn điểm |
| Mô hình nền tảng + decoder | 100–500 mảnh 256×256 có nhãn đầy đủ |
| U-Net huấn luyện từ backbone ImageNet | 1.000–5.000 mảnh |
| Phát hiện đối tượng (YOLO) | 1.500+ đối tượng mỗi lớp |

Các con số trên chỉ là điểm bắt đầu; quyết định dừng hay gán thêm dựa vào đường cong học (độ chính xác theo số lượng nhãn).

### 10.5. Kiểm soát chất lượng nhãn

- Viết hướng dẫn gán nhãn có ảnh mẫu cho từng lớp và các trường hợp biên.
- Cho 2 người gán độc lập 5–10% mẫu và đo độ đồng thuận (Cohen’s kappa, IoU giữa hai người).
- Ghi ngày ảnh dùng để gán nhãn; nhãn phải khớp thời điểm với ảnh đầu vào.
- Lưu kèm “thẻ dữ liệu” (datasheet): phạm vi, thời gian, nguồn ảnh, định nghĩa lớp, người gán, giấy phép, phiên bản.

## 11. Huấn luyện và đánh giá

Sai lầm phổ biến nhất trong GeoAI là đánh giá trên tập kiểm tra nằm sát cạnh tập huấn luyện, làm độ chính xác bị thổi phồng do tự tương quan không gian. Kiểm định không gian và đánh giá trên vùng hoặc năm chưa thấy là bắt buộc trước khi triển khai.

### 11.1. Hàm mất mát theo bài toán

| Bài toán | Hàm mất mát | Khi nào dùng |
| --- | --- | --- |
| Phân đoạn cân bằng lớp | Cross-entropy | Mặc định |
| Phân đoạn mất cân bằng (nhà, đường, biến động) | Dice, Focal, Lovász, hoặc CE có trọng số + Dice | Lớp quan tâm chiếm < 10% pixel |
| Biên đối tượng cần sắc nét | Thêm boundary loss | Footprint nhà, thửa ruộng |
| Hồi quy | MSE, Huber, hoặc Gaussian NLL (dự đoán cả độ bất định) | Sinh khối, chiều cao tán |
| Nhãn thưa | Bất kỳ loss nào, chỉ tính tại pixel có nhãn (masked loss) | Nhãn GEDI, điểm khảo sát |
| Phát hiện đối tượng | Classification + box (GIoU, CIoU); KLD/GWD cho hộp xoay | Theo thư viện sử dụng |

### 11.2. Tăng cường dữ liệu (augmentation)

- **Hình học:** xoay 90°, lật ngang/dọc (ảnh nhìn từ trên không có “chiều lên”), cắt ngẫu nhiên, co giãn tỷ lệ nhỏ.
- **Phổ và bức xạ:** nhiễu Gauss, thay đổi độ sáng nhẹ theo từng kênh. Tránh biến đổi màu kiểu ảnh thường vì có thể phá ý nghĩa vật lý của phổ.
- **Thời gian:** bỏ ngẫu nhiên một số thời điểm, dịch ngày, mô phỏng mây che để mô hình bền với dữ liệu thiếu.
- **SAR:** nhiễu speckle nhân tính, thay đổi góc tới.
- Thư viện: Kornia (GPU, có trong TorchGeo), Albumentations.

### 11.3. Chỉ số đánh giá

| Bài toán | Chỉ số chính | Bổ sung |
| --- | --- | --- |
| Phân loại, phân đoạn | F1 từng lớp, IoU / mIoU | Ma trận nhầm lẫn, độ chính xác của người sản xuất và người dùng (producer’s / user’s accuracy) |
| Ước tính diện tích | Diện tích điều chỉnh theo ma trận nhầm lẫn kèm khoảng tin cậy 95% (Olofsson 2014) | So với số liệu thống kê |
| Phát hiện đối tượng | mAP@0,5 và mAP@0,5:0,95 | Recall theo kích thước đối tượng |
| Phân đoạn thực thể | Mask AP, Polygon IoU | Chất lượng hình học (số đỉnh, góc vuông) |
| Biến động | F1 và IoU của lớp biến động | Tỷ lệ báo động giả trên mỗi km² |
| Hồi quy | RMSE, MAE, R², bias | Biểu đồ phân tán dự đoán–thực tế, sai số theo khoảng giá trị |
| Siêu phân giải | PSNR, SSIM, LPIPS | Hiệu quả trên bài toán hạ nguồn |

Không dùng “overall accuracy” làm chỉ số chính khi lớp mất cân bằng: mô hình đoán toàn bộ là “không phải nhà” vẫn có thể đạt 95%.

### 11.4. Quy trình kiểm định

1. **Kiểm định chéo theo khối không gian** (spatial k-fold) để chọn mô hình và siêu tham số.
2. **Tập kiểm tra giữ kín** ở vùng địa lý riêng, chỉ dùng một lần cuối.
3. **Kiểm tra chuyển giao thời gian:** huấn luyện năm N, đánh giá năm N+1.
4. **Kiểm tra theo điều kiện:** mùa mưa vs mùa khô, đồng bằng vs miền núi, tỷ lệ mây cao.
5. **So với baseline:** Random Forest, ngưỡng chỉ số đơn giản, và sản phẩm toàn cầu có sẵn (WorldCover, Dynamic World).
6. **Đánh giá trực quan:** chuyên gia xem bản đồ trên toàn vùng, không chỉ xem số liệu.

### 11.5. Cấu hình huấn luyện khởi điểm

- Bộ tối ưu AdamW, learning rate 1e-4 cho decoder và 1e-5 cho encoder đã tiền huấn luyện, lịch cosine có warm-up.
- Mixed precision (bf16/fp16), batch 8–32 mảnh 256×256 trên GPU 24 GB.
- Dừng sớm theo mIoU/F1 của tập kiểm định không gian.
- Theo dõi thí nghiệm bằng MLflow hoặc Weights & Biases; ghi lại phiên bản dữ liệu, cấu hình và seed.
- Báo cáo trung bình và độ lệch chuẩn qua ít nhất 3 lần chạy với seed khác nhau.

**Suy luận trên vùng lớn:** cắt ảnh thành mảnh chồng lấn, dự đoán, ghép lại bằng trung bình có trọng số (cửa sổ Hann hoặc cắt bỏ viền). Có thể dùng test-time augmentation (lật/xoay rồi lấy trung bình) để tăng độ ổn định.

## 12. Kiến trúc ứng dụng GeoAI end-to-end

Một ứng dụng GeoAI hoàn chỉnh gồm năm tầng, trong đó mô hình chỉ là một tầng; phần lớn công sức kỹ thuật nằm ở thu nhận dữ liệu, lưu trữ và phục vụ. Thiết kế theo chuẩn mở (STAC, COG, OGC) giúp thay từng thành phần mà không phải xây lại toàn bộ.

&#91;embedded content: kiến trúc ứng dụng GeoAI · 5 tầng và vòng phản hồi\]

Dữ liệu chảy từ trên xuống: ảnh mới được tìm qua STAC, tiền xử lý, đưa qua mô hình, lưu thành COG và vector, rồi hiển thị cho người dùng. Chỗ sai người dùng đánh dấu quay lại tầng mô hình làm nhãn mới.

### 12.1. Hai chế độ xử lý

- **Xử lý theo lô (batch):** chạy theo lịch (hàng tuần, theo vụ) trên toàn vùng. Phù hợp bản đồ lớp phủ, thống kê nông nghiệp, giám sát rừng. Đơn giản và rẻ nhất.
- **Xử lý theo sự kiện (event-driven):** khi có ảnh mới xuất hiện trong danh mục STAC, một tác vụ được kích hoạt ngay. Phù hợp cảnh báo ngập lụt, tàu không phát AIS, cháy rừng. Cần hàng đợi (Redis, RabbitMQ) và GPU sẵn sàng.

### 12.2. Mô hình dữ liệu cho kết quả

Mỗi lần chạy mô hình nên sinh ra một STAC Item riêng, ghi đủ nguồn gốc để có thể kiểm tra lại và so sánh giữa các phiên bản.

| Trường | Ví dụ | Mục đích |
| --- | --- | --- |
| `datetime`, `geometry` | 2026-10-15, ranh giới tỉnh | Tìm kiếm theo thời gian và vùng |
| `assets` | COG phân loại, COG xác suất, GeoParquet đa giác | Dữ liệu kết quả |
| `derived_from` | ID các cảnh Sentinel-1/2 đầu vào | Truy ngược nguồn |
| `mlm:name`, phiên bản mô hình | rice-mapper v1.3 | Biết kết quả đến từ mô hình nào |
| Chỉ số đánh giá | F1 = 0,87 trên tập kiểm tra 2025 | Hiển thị độ tin cậy cho người dùng |

Lưu luôn lớp xác suất (hoặc độ tin cậy) bên cạnh lớp nhãn cuối cùng: nó cho phép đổi ngưỡng sau này và hiển thị vùng mô hình không chắc chắn.

### 12.3. API mẫu

| Endpoint | Chức năng |
| --- | --- |
| `GET /stac/search` | Tìm kết quả theo vùng, thời gian, loại sản phẩm (pgSTAC) |
| `GET /tiles/{item}/{z}/{x}/{y}.png` | Tile bản đồ động từ COG kết quả (TiTiler) |
| `GET /stats?admin=xa_123&product=rice&season=2026-HT` | Thống kê diện tích theo đơn vị hành chính (PostGIS) |
| `POST /jobs` | Yêu cầu xử lý một vùng hoặc khoảng thời gian mới |
| `POST /feedback` | Người dùng gửi điểm hoặc đa giác báo kết quả sai |

### 12.4. Triển khai và hạ tầng

- **Container hóa:** mỗi thành phần là một image Docker; triển khai bằng Docker Compose cho giai đoạn thử nghiệm, Kubernetes khi cần mở rộng.
- **Tại chỗ hay đám mây:** dữ liệu cơ quan nhà nước thường phải lưu trong nước, nên thiết kế để chạy được trên MinIO + PostGIS tự quản lý; phần huấn luyện có thể thuê GPU đám mây theo giờ.
- **Phần cứng tham khảo cho giai đoạn đầu:** một máy chủ 1–2 GPU 24–48 GB cho huấn luyện và suy luận cấp tỉnh; ổ lưu trữ vài chục TB cho chuỗi Sentinel nhiều năm của một tỉnh.
- **Bảo mật:** xác thực OAuth2/OIDC (Keycloak), phân quyền theo vùng địa lý, ghi nhật ký truy cập, mã hóa dữ liệu ảnh thương mại theo hợp đồng.

## 13. Công cụ, thư viện và nền tảng

Một ngăn xếp toàn mã nguồn mở là đủ để xây một ứng dụng GeoAI hoàn chỉnh. Bảng dưới đây nhóm công cụ theo tầng của kiến trúc ở mục 12; cột “Gợi ý mặc định” là lựa chọn an toàn để bắt đầu.

| Tầng | Công cụ | Gợi ý mặc định | Ghi chú |
| --- | --- | --- | --- |
| Tìm và tải ảnh | pystac-client, odc-stac, stackstac, asf\_search, earthaccess, openEO, Earth Engine API | pystac-client + odc-stac | Đọc trực tiếp COG từ STAC thành xarray, không cần tải cả cảnh |
| Đọc ghi raster/vector | GDAL, rasterio, rioxarray, xarray, GeoPandas, Shapely, pyogrio | rasterio + rioxarray + GeoPandas | Nền tảng của mọi thứ khác |
| Xử lý SAR | ESA SNAP (esa\_snappy), pyroSAR, ISCE3, MintPy, HyP3 | Sản phẩm RTC có sẵn; SNAP khi cần tự xử lý | HyP3 của ASF xử lý RTC/InSAR theo yêu cầu |
| Tính toán phân tán | Dask, Ray, Apache Sedona | Dask cho xarray; Ray cho suy luận GPU song song |  |
| Thư viện GeoAI | TorchGeo, TerraTorch, segment-geospatial (samgeo), geoai-py, Raster Vision, OlmoEarth Projects | TorchGeo (đang ở dòng 0.9) hoặc TerraTorch | TorchGeo có hơn 50 benchmark và hơn 40 bộ trọng số tiền huấn luyện; TerraTorch tối ưu cho Prithvi, TerraMind |
| Thư viện thị giác chung | PyTorch, timm, segmentation\_models\_pytorch, Ultralytics, RF-DETR, MMSegmentation, MMRotate, Hugging Face Transformers | segmentation\_models\_pytorch + Ultralytics | Kiểm tra giấy phép (mục 15) |
| Học máy cổ điển | scikit-learn, XGBoost, LightGBM, GEE classifiers | scikit-learn + LightGBM |  |
| Theo dõi thí nghiệm, MLOps | MLflow, Weights & Biases, DVC, Hydra | MLflow + DVC | Phiên bản hóa dữ liệu, mô hình, cấu hình |
| Phục vụ mô hình | ONNX Runtime, TensorRT, NVIDIA Triton, TorchServe, BentoML | ONNX Runtime | Xuất ONNX giúp độc lập với framework huấn luyện |
| Điều phối pipeline | Prefect, Apache Airflow, Dagster, Argo Workflows | Prefect hoặc Dagster | Lập lịch xử lý ảnh mới, chạy lại khi lỗi |
| Danh mục và tile raster | STAC (stac-fastapi, pgSTAC), TiTiler, eoAPI | eoAPI (pgSTAC + TiTiler + TiPg) | Phục vụ tile động trực tiếp từ COG |
| CSDL không gian và tile vector | PostgreSQL + PostGIS, Martin, pg\_tileserv, PMTiles, GeoServer | PostGIS + Martin hoặc PMTiles | GeoServer khi cần chuẩn OGC WMS/WFS cho cơ quan nhà nước |
| Lưu trữ đối tượng | S3, MinIO, Google Cloud Storage | MinIO (tại chỗ) hoặc S3 | Lưu COG, Zarr, GeoParquet |
| Backend API | FastAPI, Django + GeoDjango | FastAPI | API bất đồng bộ, tài liệu OpenAPI tự sinh |
| Frontend bản đồ | MapLibre GL JS, deck.gl, OpenLayers, Leaflet, CesiumJS (3D) | MapLibre GL JS + deck.gl | MapLibre mã nguồn mở, hiệu năng cao |
| Khám phá, demo nhanh | leafmap, geemap, Jupyter, Streamlit, Solara | leafmap + Jupyter | Dựng bản demo cho khách hàng trong vài ngày |
| Desktop GIS | QGIS | QGIS | Gán nhãn, kiểm tra kết quả, người dùng chuyên môn |

### 13.1. Nền tảng mây và dịch vụ trọn gói

- **Google Earth Engine:** mạnh nhất cho phân tích quy mô lớn và học máy cổ điển; miễn phí cho nghiên cứu, giáo dục và phi lợi nhuận, có phí cho thương mại.
- **Copernicus Data Space Ecosystem:** openEO, Sentinel Hub, JupyterLab miễn phí trong hạn mức.
- **Microsoft Planetary Computer:** STAC API và dữ liệu COG miễn phí.
- **OlmoEarth Platform (Ai2), IBM Geospatial Studio:** nền tảng huấn luyện và triển khai mô hình nền tảng, ưu tiên tổ chức phi lợi nhuận và đối tác.
- **AWS SageMaker, Google Vertex AI, Azure ML:** huấn luyện và phục vụ mô hình tự quản lý khi cần GPU theo giờ.

## 15. Rủi ro, pháp lý, giấy phép và vận hành

Ba rủi ro thường làm hỏng dự án GeoAI nhất không nằm ở mô hình: giấy phép dữ liệu hoặc phần mềm không cho phép dùng thương mại, mô hình xuống cấp âm thầm khi đổi mùa hoặc đổi cảm biến, và người dùng tin kết quả quá mức.

### 15.1. Pháp lý tại Việt Nam

- **Hoạt động viễn thám:** hiện điều chỉnh bởi Nghị định 03/2019/NĐ-CP, sửa đổi bởi Nghị định 22/2023/NĐ-CP; [Bộ Nông nghiệp và Môi trường đã ban hành văn bản hợp nhất số 77/2026/VBHN-NĐ-BNNMT](https://mae.gov.vn/du-lieu-vien-tham-duoc-tang-cuong-khai-thac-phuc-vu-quan-ly-tai-nguyen-moi-truong-22720.htm). Một nghị định thay thế đang được soạn thảo, nên cần theo dõi khi thiết kế sản phẩm cung cấp cho cơ quan nhà nước.
- **Đo đạc và bản đồ:** sản phẩm bản đồ công bố công khai chịu sự điều chỉnh của Luật Đo đạc và bản đồ 2018, bao gồm thể hiện đúng đường biên giới, chủ quyền biển đảo và quy định về khu vực cấm.
- **Dữ liệu cá nhân:** ảnh độ phân giải rất cao, ảnh UAV và dữ liệu gắn với chủ sở hữu thửa đất có thể là dữ liệu cá nhân theo Luật Bảo vệ dữ liệu cá nhân (hiệu lực từ 1/1/2026). Cần đánh giá khi kết hợp bản đồ với thông tin chủ hộ.
- **Khu vực an ninh quốc phòng:** không công bố kết quả phát hiện đối tượng tại khu vực nhạy cảm; hỏi ý kiến pháp chế trước khi phát hành.

Nội dung pháp lý trên chỉ mang tính định hướng, không thay thế tư vấn của luật sư.

### 15.2. Giấy phép dữ liệu và phần mềm

| Thành phần | Giấy phép / điều kiện | Ảnh hưởng đến sản phẩm thương mại |
| --- | --- | --- |
| Sentinel, Landsat, HLS, NISAR | Mở, miễn phí, chỉ cần ghi nguồn | Dùng tự do |
| Vector nhúng AlphaEarth | CC-BY 4.0, bắt buộc ghi nguồn Google và Google DeepMind | Dùng được, nhưng Earth Engine có phí khi dùng thương mại |
| Ảnh thương mại (Maxar, Planet, Airbus) | Theo hợp đồng; thường giới hạn số người dùng và việc phân phối sản phẩm phái sinh | Đàm phán quyền dùng ảnh để huấn luyện mô hình |
| Dataset NC (xView, xBD, LoveDA…) hoặc “chỉ học thuật” (DOTA, LEVIR-CD) | Phi thương mại | Không dùng mô hình huấn luyện trên chúng cho sản phẩm bán ra nếu chưa làm rõ |
| Ultralytics YOLO | AGPL-3.0 hoặc giấy phép doanh nghiệp | Phải mở mã nguồn dịch vụ hoặc mua giấy phép; cân nhắc RF-DETR (Apache-2.0) |
| Prithvi-EO-2.0, TerraMind | Apache-2.0 | Dùng tự do |
| OlmoEarth | OlmoEarth Artifact License | Đọc kỹ điều khoản trước khi thương mại hóa |
| OpenStreetMap | ODbL | Sản phẩm dữ liệu phái sinh phải chia sẻ cùng giấy phép |

### 15.3. Rủi ro kỹ thuật và biện pháp

| Rủi ro | Biểu hiện | Biện pháp |
| --- | --- | --- |
| Lệch miền dữ liệu (domain shift) | Độ chính xác giảm khi sang vùng, mùa, năm mới | Nhãn địa phương, kiểm định không gian–thời gian, tinh chỉnh định kỳ |
| Thay đổi cảm biến hoặc xử lý | Vệ tinh mới thay thế (S1A → S1C/D), đổi baseline xử lý (offset Sentinel-2) | Theo dõi thông báo vận hành, kiểm tra phân phối đầu vào tự động |
| Mây và dữ liệu thiếu | Không có ảnh quang học nhiều tuần trong mùa mưa | Kết hợp SAR, mô hình xử lý chuỗi thiếu, báo rõ ngày dữ liệu cho người dùng |
| Ảnh sinh ra bị hiểu nhầm là ảnh thật | Ảnh loại mây, siêu phân giải chứa chi tiết “bịa” | Gắn nhãn “ảnh mô phỏng”, không dùng cho đo đạc hay chứng cứ |
| Tin tưởng quá mức | Dùng kết quả mô hình làm căn cứ xử phạt | Hiển thị độ tin cậy, quy trình con người xác minh trước khi ra quyết định |
| Chi phí tăng nhanh | Suy luận mô hình lớn trên toàn quốc mỗi tuần | Chỉ xử lý vùng thay đổi, chưng cất mô hình, lượng tử hóa |

### 15.4. Vận hành mô hình (MLOps)

- **Phiên bản hóa mọi thứ:** dữ liệu (DVC), mã, cấu hình, trọng số mô hình (MLflow Model Registry). Mỗi sản phẩm bản đồ phải truy ngược được mô hình và ảnh đầu vào đã dùng (ghi vào metadata STAC).
- **Giám sát trôi dữ liệu:** theo dõi phân phối phản xạ và tán xạ đầu vào, tỷ lệ các lớp dự đoán theo tháng; cảnh báo khi lệch bất thường.
- **Kiểm tra định kỳ:** mỗi mùa lấy một tập mẫu mới để đánh giá lại, kế hoạch huấn luyện lại 6–12 tháng một lần.
- **Vòng phản hồi:** cho người dùng đánh dấu kết quả sai trên bản đồ; các điểm này trở thành nhãn mới cho lần huấn luyện sau.
- **Kiểm thử pipeline:** kiểm tra hệ tọa độ, NoData, số kênh, dải giá trị trước khi đưa vào mô hình; nhiều lỗi im lặng bắt nguồn từ sai hệ tọa độ hoặc sai thứ tự kênh.

## 16. Tài liệu tham khảo

**Dữ liệu và cảm biến**

- [Copernicus Sentinel-1A kết thúc hoạt động, 30/6/2026 — Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/news/2026-6-30-copernicus-sentinel-1a-satellite-end-operations-after-12-years-service)
- [NISAR L-Band Data Now Publicly Available — NASA Earthdata](https://www.earthdata.nasa.gov/data/alerts-outages/nisar-l-band-data-now-publicly-available)
- [NISAR data availability overview — ASF](https://hyp3-docs.asf.alaska.edu/nisar-docs/availability-overview/)
- [Japan aims for 2027 launch of Vietnam’s LOTUSat-1 — Tuổi Trẻ News](https://news.tuoitre.vn/japan-aims-for-2027-launch-of-vietnams-lotusat-1-earth-observation-satellite-103260504134743019.htm)

**Mô hình nền tảng**

- [Satellite Embedding V1 (AlphaEarth Foundations) — Earth Engine Data Catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL)
- [Prithvi-EO-2.0 model card — Hugging Face](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL)
- [Prithvi-EO-2.0 technical report — arXiv 2412.02732](https://arxiv.org/html/2412.02732v1)
- [TerraMind 1.0 large model card — Hugging Face](https://huggingface.co/ibm-esa-geospatial/TerraMind-1.0-large)
- [OlmoEarth Platform — Ai2](https://allenai.org/earth-system)
- [Ai2 OlmoEarth v1.3 embeddings — The Letter Two](https://thelettertwo.com/2026/10/22/ai2-olmoearth-v1-3-satellite-embeddings/)
- [No One Knows the State of the Art in Geospatial Foundation Models — arXiv 2605.12678](https://arxiv.org/html/2605.12678)

**Mô hình thị giác**

- [SAM 3 với dữ liệu không gian (samgeo) — GIS Hub AI book](https://aibook.gishub.org/book/advanced/sam-geospatial)
- [SegEarth-OV3: SAM 3 cho phân đoạn từ vựng mở trong viễn thám — arXiv 2512.08730](https://arxiv.org/abs/2512.08730v1)
- [Ultralytics YOLO26: Unified Real-Time End-to-End Vision Models — arXiv 2606.03748](https://arxiv.org/pdf/2606.03748)

**Pháp lý Việt Nam**

- [Văn bản hợp nhất 77/2026/VBHN-NĐ-BNNMT về hoạt động viễn thám — Bộ Nông nghiệp và Môi trường](https://mae.gov.vn/du-lieu-vien-tham-duoc-tang-cuong-khai-thac-phuc-vu-quan-ly-tai-nguyen-moi-truong-22720.htm)

**Phương pháp kinh điển nên đọc**

- Olofsson, P. và cộng sự (2014). *Good practices for estimating area and assessing accuracy of land change.* Remote Sensing of Environment, 148, 42–57.
- Ronneberger, O. và cộng sự (2015). *U-Net: Convolutional Networks for Biomedical Image Segmentation.* MICCAI.
- Stewart, A. J. và cộng sự (2022). *TorchGeo: Deep Learning with Geospatial Data.* ACM SIGSPATIAL.
- Garnot, V. S. F. và Landrieu, L. (2021). *Panoptic Segmentation of Satellite Image Time Series with Convolutional Temporal Attention Networks* (U-TAE, PASTIS). ICCV.

Các số liệu về quy mô dataset và kiến trúc mô hình không có liên kết riêng được lấy theo bài báo gốc của từng dataset hoặc mô hình; hãy đối chiếu với trang chính thức trước khi trích dẫn trong tài liệu chính thức.
