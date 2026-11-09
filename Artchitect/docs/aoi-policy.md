# AOI — chọn vùng phân tích và cố định phạm vi kiểm định

**Ngày:** 08/11/2026. **Trạng thái:** yêu cầu tương tác đã được người dùng xác nhận; chưa có UI/importer/GIS runtime. Liên quan [SPEC-002](specs/002-g0-evidence.md), [SPEC-006](specs/006-landcover-workflow.md), [SPEC-007](specs/007-g1-platform-validation.md), [domain rules](domain-rules.md).

## Ba cách tạo AOI

| Cách chọn đã xác nhận | Hành vi cần triển khai | Thông tin phải hiển thị/giữ |
| --- | --- | --- |
| Người dùng vẽ trên bản đồ | Nhận polygon, cho sửa và xác nhận trước chạy; hỗ trợ phạm vi có nhiều phần khi hợp lệ | Geometry, nguồn vẽ, diện tích, CRS và version/hash khi đưa vào snapshot |
| Dựa vào ảnh vệ tinh import | Lấy footprint địa lý của ảnh hoặc tập ảnh do người dùng chọn làm ranh giới; có preview/xác nhận | Asset ID/hash, CRS/transform nguồn, lựa chọn ảnh, quy tắc hợp/giao nếu nhiều ảnh; không suy AOI từ kích thước màn hình |
| Import Shapefile | Đọc polygon/multipolygon, cho chọn feature hoặc hợp các feature đã chọn; giữ lỗ và các phần rời | Bộ file .shp/.shx/.dbf/.prj và .cpg khi có, layer/feature IDs, CRS nguồn và geometry/hash kết quả |

Shapefile là yêu cầu bổ sung rõ của người dùng; các đường GeoPackage/GeoJSON đã có trong thiết kế vẫn áp dụng khi được hỗ trợ. Thiếu .prj/CRS phải yêu cầu khai báo rõ hoặc từ chối thao tác chưa đủ thông tin; không tự mặc định VN-2000 hay WGS84. Không âm thầm dissolve mọi layer/feature. Import tuân [policy importer/resolver](importer-resolver-security.md); không cho đường dẫn từ dữ liệu quyết định vị trí đọc/ghi ngoài quyền đã cấp.

## Geometry và mask có vai trò khác nhau

Footprint raster lấy từ geotransform và toàn bộ ranh ảnh; raster xoay không được thay bằng bbox trục thẳng. Chuyển ranh sang WGS84 longitude/latitude có densify phù hợp, xử lý ranh múi/antimeridian theo domain rules; không chỉ đổi hai góc bbox. Không tự biến preview, overview hoặc ảnh RGB không georeference thành AOI phân tích.

AOI biểu diễn vùng người dùng muốn phân tích. Valid-data mask biểu diễn nơi có quan sát hợp lệ sau footprint/band validity/QA; không tự thu nhỏ AOI để bỏ vùng mây/NoData nhằm làm coverage tốt hơn. Nếu cho chọn “chỉ vùng có dữ liệu” thì phải là thao tác minh bạch, tạo AOI/snapshot mới và giữ nguồn mask; đây chưa là thao tác mặc định đã được duyệt.

Kiểm polygon có diện tích dương, topology, holes, trục/đơn vị, diện tích và giới hạn workload trước enqueue; lỗi hoặc repair phải được thông báo, không sửa ranh ngầm. Geometry nguồn được giữ; snapshot cố định geometry WGS84, identity/hash nguồn, GridSpec và TransformSpec. Sửa AOI tạo snapshot/job mới, không đổi ngược run/report đã công bố.

## AOI linh hoạt trong sản phẩm và AOI nghiệm thu

Ứng dụng cho chọn AOI mỗi lần chạy. Điều đó không thay nhu cầu khóa một tập AOI/vùng/mùa cụ thể để lấy nhãn, chia train/validation/test, khảo sát coverage và benchmark G0–G2. Người dùng đã chốt cách chọn vùng, **chưa chọn các AOI kiểm định cụ thể** hoặc thời kỳ phân tích. Không tuyên bố model đạt toàn thế giới chỉ vì UI vẽ được ở mọi vị trí.

AOI lớn vẫn chịu kiểm ngân sách RAM/VRAM/đĩa/thời gian và nguồn ảnh; đọc theo cửa sổ không đồng nghĩa hỗ trợ vô hạn. Với raster import làm AOI, chỉ các ảnh tương thích product/model profile mới được dùng làm input HLS; ảnh không tương thích có thể làm ranh tham chiếu nếu georeference đã kiểm.

## Ca kiểm cần có khi triển khai

- Cùng một polygon từ vẽ/import cho cùng footprint/diện tích trong tolerance đã chốt; holes/multipolygon và chọn feature không bị mất.
- Raster xoay, khác CRS, qua 108°E hoặc antimeridian giữ ranh đúng; thiếu CRS/georeference, hình tự cắt hoặc AOI rỗng bị xử lý rõ.
- Footprint đầy đủ và vùng valid khác nhau được thể hiện; coverage dùng AOI đã xác nhận làm mẫu số.
- Đổi AOI sau chạy không sửa snapshot/revision/PDF cũ; vượt workload báo lỗi hoặc đề nghị thu hẹp rõ ràng.

Đây là acceptance dự kiến cho SPEC-006/007/009; chưa có test hoặc dữ liệu kiểm thực.
