# Viewer GIS/3D và kiểm tra kết quả

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Giro3D, asset streaming, state, review và fixture hiển thị.

<a id="muc-11"></a>

## 11. Viewer GIS/3D và kiểm tra kết quả

**Giro3D là lựa chọn ban đầu**, vì phù hợp hướng GIS 2D/2.5D/3D và nguồn dữ liệu địa lý. Tài liệu và ví dụ chính thức có COG/GeoTIFF elevation và COPC [T3], [T6]. Điều này xác nhận hướng tích hợp; chưa chứng minh tốc độ, độ chính xác đo đạc hay kích thước bộ cài của GeoAI.

- DEM dùng COG độ cao nếu reader đáp ứng; point cloud ưu tiên COPC. 3D Tiles dùng khi loại sản phẩm và quy mô cần; không bắt buộc chuyển mọi point cloud thành 3D Tiles.
- Local asset API dùng `asset_id`, HTTP Range/206, ETag và chính sách cache. Xác thực cả request từ loader, worker và decoder; không đưa nguyên file lớn qua Tauri IPC.
- Với phiên bản Giro3D đã khóa, kiểm chứng fetch hook/adapter gắn token phiên trong header cho request asset/tile và Range, kể cả request phát từ web worker. Không đưa token vào URL, log hoặc cache key công khai; nếu loader không hỗ trợ đường xác thực đã chọn thì dùng adapter/proxy local được kiểm chứng, không bỏ xác thực.
- Đóng gói decoder/WASM, font, shader/tài nguyên và bản đồ nền offline cần thiết. Với phiên bản Giro3D được khóa, kiểm tra đường tải laz-perf và cấu hình local trước khi khởi tạo nguồn COPC/LAS/LAZ.
- Backend xử lý khi JavaScript không đọc được codec/CRS hoặc khi style cần biểu thức phức tạp. GDAL hỗ trợ một định dạng không tự bảo đảm frontend đọc trực tiếp được.
- State layer, camera, selection, AOI, style và timeline nằm ở ứng dụng. Mỗi result/revision được định danh riêng; đổi threshold không chỉ thay màu rồi ghi đè kết quả cũ.
- Review bản đầu gồm xem nguồn/kết quả, lọc theo lớp/confidence, định vị vùng lỗi, nhận xét và sửa thuộc tính. Sửa hình học qua QGIS rồi nhập GeoPackage thành revision mới, kiểm tra CRS/feature ID/class schema/geometry; chưa xây editor hình học tổng quát trong Giro3D.

Fixture viewer phải có raster lớn, DEM có NoData/datum rõ, COPC, vector nhiều đỉnh, nhãn và picking. Đo byte tải, cold/warm load, RAM/VRAM, phân vị frame time, giải phóng bộ nhớ khi đóng lớp và cạnh tranh với AI. **p95 frame time ≤ 33 ms** trên scene và chuỗi thao tác cố định là mục tiêu thử nghiệm đề xuất ban đầu; chưa là cam kết cho mọi dữ liệu. G0/G1 phải ghi viewport, độ phân giải màn hình, layer/style, số đối tượng/đỉnh hiển thị, cấu hình máy và trạng thái AI; số lượng polygon tổng trong dataset không tự xác định tải render.

Adapter viewer chỉ bao phủ thao tác ứng dụng đang dùng: thêm/xóa lớp, camera, chọn đối tượng, cập nhật style/time và lấy ảnh xem trước khi cần. Báo cáo chính thức vẫn dùng renderer backend theo [mục 12.3](11_revision_domain_pack_va_bao_cao.md#muc-12-3). Giữ state ngoài engine và giới hạn nơi gọi API Giro3D để giảm chi phí đổi phiên bản; không coi interface là bảo đảm thay engine không tốn công về CRS, picking, style hoặc hiệu năng. Mỗi lần nâng phiên bản chạy lại fixture codec/COG, COPC/WASM, xác thực và offline; kiểm tra không phát request CDN khi ngắt mạng.

Chỉ thêm OpenLayers/MapLibre hoặc đổi engine khi fixture nghiệp vụ chứng minh Giro3D không đáp ứng. Không đóng gói nhiều engine để dự phòng ngay từ đầu.

---

**Tài liệu liên quan:**

- [Phạm vi bản đầu và luồng sử dụng](03_pham_vi_ban_dau_va_luong_su_dung.md)
- [Dữ liệu đa nguồn và chuẩn hóa địa lý](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md)
- [Revision, Domain Pack và báo cáo](11_revision_domain_pack_va_bao_cao.md)
- [Runtime CPU/NVIDIA và hiệu năng](12_runtime_cpu_nvidia_va_hieu_nang.md)

[T3]: https://giro3d.org/latest/apidoc/index.html
[T6]: https://giro3d.org/latest/examples/index.html
