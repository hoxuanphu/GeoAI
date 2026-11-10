# Quy tắc tính đúng địa lý

Đọc trước mọi thay đổi raster/vector/CRS. Chi tiết nguồn: [chuẩn hóa địa lý](../plans/06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md), [phương trình và đơn vị](../plans/07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-7), ADR-005 và ADR-010.

Cách tạo AOI vẽ/footprint ảnh import/Shapefile và quy tắc cố định phạm vi ở [AOI policy](domain/aoi-policy.md). Bộ bảy lớp, crosswalk và `ignore_index = -1` ở [landcover taxonomy](domain/landcover-taxonomy.md); lớp 0 là nước hợp lệ, không dùng làm NoData. Quyền đọc file/nguồn theo importer/resolver, không suy từ việc dữ liệu có CRS hợp lệ.

## CRS, trục và grid

1. Giữ AOI gốc và CRS; tạo footprint WGS84 longitude/latitude cho tìm kiếm. Không chỉ đổi hai góc bbox khi cạnh cần densify hoặc gặp antimeridian.
2. GridSpec xác định CRS + affine + width/height. Cùng pixel size không đồng nghĩa cùng grid. Nếu bám raster tham chiếu thì giữ đúng cả bốn thành phần.
3. Backend là nguồn CRS/TransformSpec: WKT2/PROJJSON hoặc authority đã kiểm, trục/đơn vị, operation, datum grid/hash, area of use, PROJ database/version và tolerance.
4. VN-2000 phải xác định datum, múi/kinh tuyến trục, scale, false easting/northing và nguồn tham số phù hợp; không tự gán “VN-2000 chung” hoặc suy CRS từ tên file. Thiếu grid/phép chuyển đạt chuẩn thì báo lỗi, không fallback ballpark âm thầm.
5. Frontend dùng phép đã kiểm tương đương. Nếu proj4/loader thiếu operation/grid, backend tạo asset/tile reprojection. Rendering không ghi đè grid phân tích.
6. HLS MGRS/UTM qua 108°E phải warp từng tile về grid đích trước ghép; kiểm đường nối, mask và không đếm trùng vùng chồng 48N/49N.
7. Chiều cao có datum đứng/đơn vị riêng. DEM, DSM, DTM và chiều cao cây không hoán đổi.

### Thứ tự affine và vị trí pixel

`GridSpec.affine = [a,b,c,d,e,f]` có nghĩa `x = a×col + b×row + c`, `y = d×col + e×row + f`; điều kiện khả nghịch `a×e − b×d ≠ 0`. Đây là thứ tự sáu hệ số của Affine, **khác GDAL GeoTransform** `[c,a,b,f,d,e]`. Adapter phải chuyển thứ tự rõ ràng; comment trong mã đã được sửa cùng SPEC-001.

Với `pixel_interpretation=area`, `(0,0)` là góc ô trên trái, tâm pixel `(col,row)` ở `(col+0.5,row+0.5)`. Ví dụ `[30,0,500000,0,-30,1200000]` có tâm ô đầu `(500015,1199985)`, mỗi ô phẳng 900 m² trước cắt AOI; fixture không chứng minh CRS/tolerance đã được duyệt. PixelIsPoint phải có quy ước chuyển đổi/fixture riêng trước hỗ trợ, tránh nửa pixel dịch hai lần. Bản đồ xoay cần giữ cả `b`/`d`, không suy bbox chỉ từ pixel size.

## Band, mask và nội suy

- Product profile khóa sensor/product/baseline, band mapping, scale/offset, QA và đơn vị. Không áp scale/offset hai lần; display stretch không tham gia phân tích.
- Phân biệt footprint, vùng có quan sát và valid mask sau QA. Pixel hợp lệ cho model phải đủ band. Cloud/shadow/NoData/ngoài AOI/không phát hiện là các trạng thái khác nhau.
- Giải mã Fmask đúng bit/version. Phần trăm mây toàn scene không thay coverage AOI.
- Nhãn/QA dùng nearest hoặc mode theo tác vụ; không bilinear/cubic/average làm sinh mã lớp mới. Reflectance dùng phương pháp được profile chốt và kiểm chứng.
- Mosaic/composite lưu mọi source scene/ngày, recipe và mask; có thể cần source/date raster. Không gán một acquisition date giả cho composite TL.
- Coverage ngày tốt nhất và coverage hợp tháng là hai phép đo riêng; resample không tạo chi tiết quan trắc mới.
- COG dùng chung cho phân tích/hiển thị khi codec/overviews đáp ứng; bản hiển thị dẫn xuất có source/recipe, chịu cache policy khi tái tạo được.

## Diện tích và thống kê

`A_k = sum(a_i × valid_i × I(label_i = k))`, a_i là diện tích ô giao AOI bằng m² theo ellipsoid hoặc CRS phù hợp; ha = m²/10.000. Không lấy pixel Web Mercator để tính diện tích mà bỏ biến dạng. Ghi cách xử lý biên pixel và phần AOI không quan sát; coverage theo diện tích, không theo giao bbox.

Diện tích bản đồ chưa là ước lượng điều chỉnh sai số. Khoảng tin cậy cần thiết kế lấy mẫu kiểm định; confidence model chưa là xác suất hiệu chuẩn hoặc khoảng tin cậy.

[Tiêu chí nghiệm thu](domain/acceptance-criteria.md) ghi yêu cầu diện tích/CI, RMSE VN-2000 ≤15 m và chênh lệch diện tích AOI ≤0,1%, cùng protocol còn cần khóa. CI diện tích cần probability sampling/trọng số đúng thiết kế; không dùng sample counts của chip thuận tiện làm diện tích toàn AOI. So diện tích reprojection phải cùng ranh/phương pháp vật lý, không nhầm biến dạng phép chiếu với lỗi datum. Không lấy tolerance 15 m hoặc bộ 7 tham số làm chứng nhận pháp lý/độ chính xác chưa kiểm.

Coverage là `A_valid / A_AOI`, cùng phương pháp diện tích và policy cắt biên; không dùng bbox chung làm mẫu số. Với AOI diện tích dương, tổng diện tích lớp quan sát và diện tích chưa quan sát phải khớp diện tích AOI trong tolerance của phương pháp đã chốt. Không có pixel hợp lệ phải báo coverage 0 và không có kết quả phân loại hợp lệ; không biến toàn AOI thành lớp 0. AOI rỗng/diện tích bằng 0 bị từ chối, không chia cho 0.

## Bất biến kiểm chứng

- Điểm khống chế độc lập và raster overlay ở nhiều vị trí; round-trip chỉ bổ sung, không phát hiện hai bên cùng sai.
- Constant-field reprojection giữ giá trị ngoài mask; nhãn không sinh class ID mới; mosaic không trùng diện tích; vùng invalid không biến thành lớp nền/0.
- Forcing vật lý có kỳ tích lũy/múi giờ/datum khớp; mm không phải m, kg không phải Mg, °C không phải K. Missing input không tự điền 0.
- Vector sửa qua QGIS không tự sửa raster dự đoán. Metrics/report chọn representation/revision rõ; sửa nhãn/hình học phải có revision và review lại.

Fixture địa lý thật và tolerance nghiệp vụ chưa được cung cấp; contract geometry validator chỉ kiểm cấu trúc/range/ring closure, chưa chứng minh topology hoặc độ chính xác PROJ/GDAL.
