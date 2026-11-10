# Dữ liệu đa nguồn và chuẩn hóa địa lý

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Provider/product profile, định dạng, QA, grid, CRS và VN-2000.

AOI có thể do người dùng vẽ, lấy theo footprint ảnh import hoặc import Shapefile; chi tiết identity/CRS/topology/snapshot ở [AOI policy](../docs/domain/aoi-policy.md). Không tự thu AOI theo valid mask. Bộ 7 lớp/crosswalk WorldCover-JAXA ở [landcover taxonomy](../docs/domain/landcover-taxonomy.md); nhãn mở phải được version hóa và QC trước dùng train.

<a id="muc-7"></a>

## 7. Dữ liệu đa nguồn và chuẩn hóa địa lý

<a id="muc-7-1"></a>

### 7.1. Ba lớp thu nhận

Chính sách nguồn ảnh đã xác nhận tại G0: nguồn mở/miễn phí trước; ảnh thương mại chỉ tích hợp khi có quyền và ngân sách. Mục tiêu đa nguồn toàn cầu không thay kiểm license/quota/quyền đọc từng asset và gate từng product profile; danh sách provider thực tế vẫn chờ chọn và thử truy cập. Ảnh 10/5/1 m là các profile mở rộng sau nhánh HLS 30 m, không đổi pixel size HLS để tuyên bố nguồn quan trắc mới.

**Provider Adapter → Product Profile → biểu diễn phân tích.**

- Provider adapter phụ trách search, phân trang, rate limit, xác thực, resolve URL, preview và download/remote compute theo capability.
- Product profile mô tả cảm biến, processing baseline, band mapping, scale/offset, đơn vị, QA, grid và yêu cầu tiền xử lý.
- Pipeline nhận AssetRef/GridSpec đã chuẩn hóa và kiểm tra; không rải điều kiện theo tên provider trong thuật toán ngành.

Ví dụ cùng Sentinel-2 L2A từ hai provider phải kiểm tra metadata để biết dữ liệu đã áp offset hay chưa; không trừ offset lần nữa chỉ dựa vào tên cảm biến. SAR RTC cần phân biệt gamma0/sigma0, linear/dB và phân cực. Không trộn giá trị dB và tỷ số tuyến tính theo một công thức không được định nghĩa.

Search, order, download và analysis là các thao tác khác nhau. Bản đầu ưu tiên nguồn mở/import local. Khi thêm ảnh thương mại, xác nhận đúng sản phẩm, quyền sử dụng, điều kiện cung cấp và chi phí trước order; retry của download không tự tạo đơn mua mới. Tham chiếu quy trình UP42 [M13].

**Đường truy cập HLS:** G0 chốt một provider/collection cụ thể và thử từ tìm kiếm đến đọc band/QA trên AOI thật. Đường NASA Earthdata yêu cầu tài khoản/xác thực theo dịch vụ; provider thay thế có cơ chế truy cập và điều kiện riêng. Không suy quyền tải asset từ việc tìm được metadata công khai. Credential/token lưu trong kho hệ điều hành theo [mục 15.1](14_bao_mat_server_va_van_hanh.md#muc-15-1), không trong snapshot, project export hoặc log; kiểm tra hết hạn/làm mới và lỗi thiếu quyền. Offline dùng các asset đã được giữ local hợp lệ.

<a id="muc-7-2"></a>

### 7.2. Biểu diễn và lưu trữ

| Loại dữ liệu | Dạng ưu tiên | Điều kiện |
| --- | --- | --- |
| Ảnh quang học, DEM và kết quả raster | COG có overviews khi cần đọc theo vùng | Giữ dữ liệu gốc; không convert lại COG đã phù hợp |
| Cube nhiều thời điểm/siêu phổ | Xarray; Zarr khi có lợi | Chọn chunk theo kiểu truy vấn và ngân sách RAM/I/O |
| Vector | GeoPackage để trao đổi/chỉnh sửa; GeoParquet cho bảng lớn | GeoJSON chỉ cho tập nhỏ/giao tiếp; kiểm tra geometry/CRS/schema |
| LiDAR | COPC khi cần streaming; LAS/LAZ gốc được giữ hoặc tham chiếu | GDAL không thay thế PDAL; công bố driver thực được đóng gói |
| Mesh/photogrammetry | GLB nhỏ; 3D Tiles khi cần phân cấp | Kiểm tra georeference, LOD và extension renderer hỗ trợ |
| SAR SLC/InSAR | Định dạng chuyên biệt giữ pha và metadata | Ngoài phạm vi đầu; không ép thành amplitude COG cho mọi tác vụ |

STAC mô tả nguồn và artifact ở ranh giới trao đổi [T1]. Không mặc định mọi job phải là một STAC Item: job quản lý thực thi, còn sản phẩm địa lý được công bố theo độ hạt phù hợp. Một job có thể sinh nhiều item/asset.

Phân biệt hai **profile sử dụng COG**, không bắt buộc tạo hai file cho mỗi raster:

| Profile | Yêu cầu |
| --- | --- |
| Phân tích | Giữ dtype, giá trị, band/scale, CRS/grid và NoData theo contract; chọn nén lossless và block size theo workload đọc cửa sổ. Block 512 là ứng viên thử nghiệm, chưa là mặc định bắt buộc cho mọi nguồn |
| Hiển thị trực tiếp | Codec/predictor, overviews, mask/NoData và số band phải đọc được bằng decoder JavaScript của phiên bản viewer đã khóa; DEFLATE là ứng viên cần thử. Overview của nhãn phải giữ ý nghĩa lớp, không dùng quy tắc của reflectance tùy tiện |

Nếu COG phân tích đáp ứng viewer thì dùng chung asset. Nếu không, tạo biểu diễn hiển thị dẫn xuất hoặc render tile phía backend (có thể dùng rio-tiler sau kiểm chứng); ghi source asset/version và recipe/style. Tile/display stretch không thay dữ liệu dùng cho suy luận hoặc đo đạc. Bản hiển thị tái tạo được chịu quota/cache theo [mục 10.4](09_luu_tru_artifact_va_project.md#muc-10-4); chỉ giữ lâu dài nếu được package/report/run yêu cầu.

<a id="muc-7-3"></a>

### 7.3. Quy tắc địa lý bắt buộc

- Giữ AOI gốc kèm CRS; tạo hình học WGS84 chuẩn cho tìm kiếm. Khi chuyển footprint cần xử lý độ cong cạnh, trục tọa độ và antimeridian theo phạm vi hỗ trợ; không chỉ biến đổi hai góc bbox.
- Lưới xử lý được chọn theo AOI/model. Nếu người dùng yêu cầu bám raster tham chiếu thì giữ chính xác CRS, transform, width/height của reference grid; pixel size giống nhau chưa đủ để gọi là cùng lưới.
- Phân biệt footprint giao AOI, vùng có dữ liệu và vùng hợp lệ sau QA. Coverage sau mosaic/suy luận phải tính từ mask thực, không chỉ từ giao bbox.
- Mọi tính toán diện tích công bố phương pháp: ellipsoid hoặc CRS phù hợp. Không tính diện tích bằng số pixel Web Mercator mà bỏ qua biến dạng.
- Đồng đăng ký trước biến động; resample nhãn bằng phương pháp giữ lớp. Scale/offset và normalization theo product/model contract; display stretch không làm đổi raster phân tích.
- Mosaic ghi mọi scene/ngày, phương pháp và mask; xuất thêm source/date raster nếu cần truy nguồn theo pixel. Không gán một ngày chụp duy nhất gây hiểu nhầm cho composite nhiều ngày.
- NoData, mây, ngoài AOI và “không phát hiện” là các trạng thái khác nhau. QA raster dùng schema/version rõ ràng.
- Height có đơn vị và datum đứng; DEM/DSM/DTM không hoán đổi ngầm. Đo từ dữ liệu nguồn, không lấy bề mặt LOD làm số liệu chính thức.

HLS S30/L30 dùng lưới tile MGRS trên UTM ở 30 m [P9]. AOI trên phần đất liền Việt Nam có thể cắt ranh UTM 48N/49N tại 108°E. Mỗi tile giữ CRS nguồn; chọn một `GridSpec` đích phù hợp AOI/model, warp từng nguồn về grid đó trước khi ghép. Không nối trực tiếp chỉ số pixel giữa hai múi. G1 có fixture cắt ranh 108°E để kiểm tra đồng đăng ký, đường nối, vùng chồng lấn, NoData/QA và diện tích không đếm trùng; QA/nhãn dùng resampling giữ lớp, reflectance theo product profile.

<a id="muc-7-4"></a>

### 7.4. CRS frontend–backend và VN-2000

Backend là nguồn quản lý **CRS và phép chuyển đổi có phiên bản**. Hệ thống không duy trì hai bộ tham số do frontend/backend nhập tay độc lập. `TransformSpec` ghi định nghĩa WKT2/PROJJSON hoặc mã authority đã kiểm tra, trục/đơn vị, phép chuyển datum, grid cần thiết và checksum, phạm vi sử dụng, phiên bản PROJ/database và sai số chấp nhận được. Chỉ thống nhất mã CRS chưa đủ: PROJ có thể chọn phép chuyển khác nhau tùy vùng, độ chính xác và grid hiện có [T7].

VN-2000 phải được mô tả theo cấu hình thực của dữ liệu: datum, phép chiếu, múi/kinh tuyến trục, hệ số tỷ lệ, false easting/northing, đơn vị và thứ tự trục. Không có một chuỗi “VN-2000 chung” dùng đúng cho mọi bản đồ cấp tỉnh hoặc mọi nguồn. Thiếu thông tin thì yêu cầu xác định CRS khi import, không tự gán WGS84 hoặc một múi UTM. Các tham số chuyển đổi phải có nguồn và phạm vi sử dụng được đơn vị dữ liệu xác nhận; không sao chép một bộ tham số trên Internet cho mọi dự án.

Quy tắc tại ranh giới ứng dụng:

1. Backend tính AOI tìm kiếm, phép đo, raster phân tích và geometry kết quả. GeoJSON trao đổi theo quy ước longitude/latitude WGS84; tọa độ ở CRS khác dùng DTO có CRS và trục rõ ràng, không gắn nhãn GeoJSON WGS84 sai.
2. Frontend đăng ký cấu hình proj4 từ registry do backend cung cấp, chỉ với phép chuyển đã qua fixture tương đương. Nếu loader không áp dụng được cùng operation/grid/datum thì backend tạo asset/tile đã chuyển sang CRS hiển thị được hỗ trợ; không fallback datum âm thầm.
3. Geometry người dùng vẽ/sửa gửi kèm CRS và phiên bản cấu hình view. Backend xác thực/chuyển đổi và trả geometry chuẩn; tọa độ dùng để hiển thị không tự trở thành tọa độ đo đạc chính thức.
4. Giữ riêng dữ liệu phân tích và dữ liệu hiển thị. Reprojection để render không được ghi đè grid phân tích hoặc nâng giả độ chính xác. Datum đứng có hợp đồng riêng, không mặc định proj4 đã giải quyết chuyển cao độ.
5. Khi thiếu grid hoặc chỉ còn phép chuyển gần đúng không đạt yêu cầu, báo lỗi có cấu trúc; không âm thầm chấp nhận ballpark transformation cho phân tích/đo đạc.

G0 chốt danh sách CRS/VN-2000 mục tiêu và tolerance theo nghiệp vụ. G1 kiểm tra điểm khống chế độc lập trên nhiều vị trí, trục và đơn vị; so backend với frontend và giá trị chuẩn, kiểm tra cả raster overlay. Kiểm tra round-trip là bổ sung, không đủ để phát hiện hai phía cùng dùng một phép chuyển sai. Bộ fixture và tài nguyên grid phải chạy được offline; không tự tuyên bố độ chính xác địa chính từ một phép đổi tọa độ chưa kiểm chứng.

<a id="muc-7-5"></a>

### 7.5. Khảo sát khả năng quan sát HLS tại G0

Trên AOI đại diện, thống kê 2–3 năm dữ liệu theo tháng và mùa, bắt đầu bằng HLS S30 v2 đúng provider/profile dự kiến phát hành. Nếu thử thêm L30, công bố riêng S30, L30 và tổ hợp; không dùng độ phủ tổ hợp để hứa khả năng của S30 đơn lẻ. Nếu lịch sử không đủ thì ghi khoảng thiếu và giới hạn kết luận.

- Khóa AOI, grid đo, khoảng thời gian, asset/version và chính sách Fmask/NoData; giải mã đúng bit QA, không dùng phần trăm mây toàn scene thay coverage AOI. Pixel hợp lệ phải có đủ sáu band và đạt QA đã chọn; phân biệt không có quan sát với có quan sát nhưng bị loại.
- Đo coverage từng ngày, ngày tốt nhất trong tháng, số ngày đạt coverage nghiệp vụ, số quan sát hợp lệ theo pixel và khoảng trống quan sát. Các tile cùng ngày có thể mosaic theo grid chuẩn, nhưng không gộp nhiều ngày rồi gọi là một lần chụp.
- Đo riêng coverage hợp của các quan sát hợp lệ trong tháng hoặc cửa sổ composite; ghi độ trải ngày, scene nguồn và quy tắc chọn pixel. Coverage hợp chỉ là khả năng phủ tiềm năng; recipe composite thực tế còn phải kiểm tra mask đầu ra và profile model.
- Lưu bảng theo tháng và bản đồ coverage/thiếu dữ liệu với provenance; G0 dùng kết quả để chốt feature, mùa, AOI, coverage tối thiểu và chiến lược ảnh một ngày/composite. Bắt đầu bằng đọc QA và kiểm tra validity các band theo cửa sổ, chưa cần suy luận; chi phí vẫn phụ thuộc provider, số scene và diện tích.

Tỷ lệ trung bình tháng không chứng minh tồn tại ảnh một ngày đủ phủ AOI. Composite và metadata TL tuân theo [mục 8.2](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-2); đổi chiến lược ảnh phải cập nhật profile huấn luyện/kiểm định.

---

**Tài liệu liên quan:**

- [Hợp đồng dữ liệu và versioning](05_hop_dong_du_lieu_va_versioning.md)
- [Model Prithvi, dữ liệu nhãn và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md)
- [Viewer GIS/3D và kiểm tra kết quả](10_viewer_gis_3d_va_kiem_tra_ket_qua.md)

[M13]: https://docs.up42.com/data/catalog-process
[T1]: https://stacspec.org/en
[T7]: https://proj.org/en/stable/operations/operations_computation.html
[P9]: https://www.earthdata.nasa.gov/data/projects/hls
