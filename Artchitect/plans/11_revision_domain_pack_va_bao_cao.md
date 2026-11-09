# Revision, Domain Pack và báo cáo

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Duyệt kết quả, phiên bản chỉnh sửa, gói nghiệp vụ và xuất PDF.

<a id="muc-12"></a>

## 12. Revision, gói nghiệp vụ và báo cáo

<a id="muc-12-1"></a>

### 12.1. Phân biệt hoàn tất kỹ thuật và duyệt nghiệp vụ

Job `succeeded` có nghĩa quá trình tính toán và công bố artifact thành công. Nó không tự có nghĩa kết quả đủ chất lượng hoặc đã được chuyên gia duyệt. **Bản đầu chỉ có hai review state: `unreviewed` (chưa duyệt), `reviewed` (đã duyệt)**, kèm người/thời điểm, phạm vi kiểm tra và nhận xét. Người dùng có thể đưa về chưa duyệt kèm lý do; chưa xây quy trình nhiều cấp phê duyệt hoặc trạng thái approved/rejected riêng.

Chỉnh sửa tạo revision có `parent_revision_id`, giữ lớp dự đoán gốc và edit artifact. Sửa sau duyệt tạo revision chưa duyệt; metrics được tính lại từ revision mới. Thay model, nguồn, lưới hoặc tiền xử lý tạo run mới. Thay threshold từ probability artifact có thể chỉ chạy hậu xử lý nhưng vẫn tạo revision và ghi recipe.

Đầu ra được phân loại rõ: raster dự đoán và vector dẫn xuất; chỉnh sửa vector trong QGIS không tự làm đổi raster gốc. Metrics/report phải chỉ định representation và revision có thẩm quyền; nếu muốn raster sửa theo vector thì tạo artifact dẫn xuất mới có recipe và kiểm tra NoData/grid. Nhập lại GeoPackage giữ liên kết với run/revision gốc, không coi file ngoài là ground truth tự động.

<a id="muc-12-2"></a>

### 12.2. Domain Pack

Mỗi `domain_id + feature_id + feature_version` xác định: bài toán, schema tham số, product/model requirements, workflow, quy tắc hậu xử lý, công thức chỉ tiêu, đơn vị, tiêu chí chất lượng, style và template. Dùng lại engine xử lý và thống kê.

Ví dụ: gói lớp phủ tính diện tích theo vùng; gói rừng thêm định nghĩa biến động và phương pháp kiểm chứng; gói ngập thêm thời điểm trước/sau và coverage. Ước tính carbon cần phương pháp và dữ liệu kiểm định phù hợp; lớp hiển thị ngập 3D không thay engine mô phỏng thủy động lực.

Domain Pack vật lý tham chiếu danh mục [mục 8.6](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-6) và `PhysicalModelSpec`: gói thực vật chọn PROSAIL; gói nước cây trồng chọn FAO-56 hoặc SEBAL theo dữ liệu; gói lưu vực chọn SCS-CN, HAND hay solver 2D theo đại lượng cần dự báo; gói đất dùng RUSLE; gói rừng dùng allometry và hồi quy diện rộng đã kiểm định. Chỉ kích hoạt feature khi có input profile, nguồn hệ số, calibration/evaluation và runtime/solver đã duyệt. Một lớp phủ AI có thể là đầu vào của nhiều gói, nhưng bảng ánh xạ lớp sang CN/C/P và sai số của nó phải được version hóa riêng.

<a id="muc-12-3"></a>

### 12.3. Báo cáo

**ResultRevision được chọn → MetricsSnapshot → ReportContext → bản đồ/biểu đồ → Typst PDF và bảng phụ lục khi cần.**

PDF bản đầu dùng Typst CLI, font tiếng Việt và template local. Matplotlib/renderer 2D trong worker dựng bản đồ báo cáo; không phụ thuộc cửa sổ viewer đang mở. XLSX khi cần bảng; DOCX khi có yêu cầu mẫu có thể chỉnh sửa. HTML report tương tác là mở rộng, không triển khai song song hai renderer PDF ngay từ đầu.

Báo cáo bắt buộc ghi AOI, acquisition range, ngày phân tích/lập báo cáo, coverage và diện tích chưa quan sát, class/threshold, đơn vị/phương pháp, backbone/decoder/feature/template version, result revision và representation, trạng thái duyệt, evaluation reference và giới hạn. Kết quả chưa duyệt có thể xuất bản nháp với nhãn rõ; bản báo cáo chính thức của feature đầu yêu cầu revision `reviewed`. Trạng thái này ghi nhận việc kiểm tra của người dùng, không tự chứng nhận chất lượng pháp lý hoặc đo đạc.

Với kết quả vật lý, báo cáo ghi đại lượng/phương trình và PhysicalModelSpec, bộ tham số/nguồn hệ số, kỳ tính, forcing/điều kiện biên, solver và kết quả kiểm định/bất định thay cho các trường backbone/decoder không áp dụng. Phân biệt ET0/ETc/ET thực, Q theo mm/thể tích/lưu lượng, HAND/độ sâu mô phỏng, mất đất sườn dốc/bùn cát cửa ra và AGB/carbon tồn trữ/biến động carbon. Kịch bản giả định phải được gắn nhãn và nêu giả định; vùng không có dữ liệu hoặc ngoài miền hiệu lực không ghi thành giá trị 0.

Một report record lưu file/hash và tất cả snapshot liên quan. Xuất lại nội dung dùng snapshot cũ; không yêu cầu PDF tái render phải có hash giống hệt nếu metadata render thay đổi, nhưng số liệu/nội dung phải tương đương. Bản PDF gốc được lưu để truy nguyên chính xác. Nếu sau này dùng LLM, LLM chỉ viết diễn giải dựa trên số liệu đã chốt, không tự tính số liệu hay thay artifact.

---

**Tài liệu liên quan:**

- [Hợp đồng dữ liệu và versioning](05_hop_dong_du_lieu_va_versioning.md)
- [Lưu trữ, artifact và project di động](09_luu_tru_artifact_va_project.md)
- [Viewer GIS/3D và kiểm tra kết quả](10_viewer_gis_3d_va_kiem_tra_ket_qua.md)
- [Lộ trình và cổng nghiệm thu](15_lo_trinh_va_cong_nghiem_thu.md)
