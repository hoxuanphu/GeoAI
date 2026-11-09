# Cơ sở đề xuất và tham chiếu thị trường

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Chắt lọc tài liệu nội bộ, đối chiếu sản phẩm và yêu cầu R01–R09.

<a id="muc-2"></a>

## 2. Chắt lọc từ bốn tài liệu nội bộ

| Nguồn | Nội dung giữ lại | Điều chỉnh trong bản tổng hợp |
| --- | --- | --- |
| Bản chính [A], [mục 1](01_dinh_huong_san_pham.md#muc-1)–4, 6, 9–12 | Desktop trước; module và hợp đồng; SQLite; Giro3D; CPU/NVIDIA; bộ cài và offline | Làm rõ vòng đời job, phiên bản kết quả, quyền ghi project, backup và điều kiện lên server |
| Bản Copilot [B], [mục 2](02_co_so_de_xuat_va_tham_chieu_thi_truong.md#muc-2), 6, 11–12 | Phân biệt Client/Local Workstation; adapter nhà cung cấp → hồ sơ sản phẩm; hàng đợi server; quyền trên API/tile/asset/report | Đưa PostgreSQL/Procrastinate vào cấu hình server; hoãn AMD và hai engine bản đồ song song |
| Cẩm nang [C1], [mục 2](02_co_so_de_xuat_va_tham_chieu_thi_truong.md#muc-2)–7 | Năng lực phân tích; vai trò baseline vật lý/ML; xử lý ảnh lớn; chống rò rỉ không gian; vòng phản hồi | Danh mục thuật toán là hướng mở rộng, không phải danh sách dependency bắt buộc |
| Hướng dẫn [C2], [mục 3](02_co_so_de_xuat_va_tham_chieu_thi_truong.md#muc-3), 10–12, 15 | Đặc tả bài toán; dữ liệu và nhãn địa phương; kiểm định độc lập; model/data version; drift | Chuyển thành hợp đồng dữ liệu, quy trình kiểm duyệt và tiêu chí nghiệm thu có thể kiểm tra |

Không kế thừa các khuyến nghị tuyệt đối hóa: mọi raster đều phải thành COG; mọi bài toán phát hiện đều phải dùng OBB; mọi pipeline đều clipping theo phân vị; một lưới UTM/GSD dùng cho mọi dự án; mọi polygon phải vuông hóa; mọi model nền tảng nhận được mọi cảm biến. Các lựa chọn này phụ thuộc dữ liệu và mục tiêu cụ thể.

Không dùng thông số minh họa trong cẩm nang làm cam kết sản phẩm: độ trễ vài giờ, tốc độ vài mili giây, độ chính xác, tỷ lệ tiết kiệm VRAM, hoặc siêu phân giải 10 m thành quan sát thật 2,5 m. Không sao chép số liệu dataset, lịch vệ tinh hay diễn giải giấy phép chưa được đối chiếu riêng.

<a id="muc-3"></a>

## 3. Tham chiếu sản phẩm thị trường và bài học áp dụng

<a id="muc-3-1"></a>

### 3.1. Cách sử dụng nguồn

Đã đọc trực tiếp tài liệu công khai trên website chính thức của các sản phẩm dưới đây. “Tham chiếu thị trường” có nghĩa là tham khảo quy trình và năng lực được mô tả; **không phải chứng nhận chất lượng, benchmark độc lập hay yêu cầu phải mua sản phẩm đó**. Chuẩn định dạng được đối chiếu riêng với STAC và OGC [T1], [T2].

Phân biệt ba loại nguồn: tài liệu sử dụng/API; trang giới thiệu sản phẩm; đặc tả chuẩn. Chỉ suy ra tính năng mà trang đã đọc thực sự mô tả. Không suy đoán database, framework nội bộ, độ chính xác hoặc kiến trúc triển khai của nhà cung cấp.

<a id="muc-3-2"></a>

### 3.2. Sản phẩm đối chiếu

| Sản phẩm/nền tảng | Điều đã xác nhận từ tài liệu | Điều GeoAI nên học | Giới hạn khi tham khảo |
| --- | --- | --- | --- |
| **Esri ArcGIS Pro / Image Analyst** | Quy trình chuẩn bị nhãn, train, inference, review; package `.dlpk` chứa model và `.emd`; công cụ đo precision/recall/F1/AP và xuất báo cáo độ chính xác [M1], [M2], [M3], [M4] | Model phải có hợp đồng đầu vào; đánh giá là sản phẩm riêng; có bước chuyên gia rà soát | Không mặc định tương thích `.dlpk`, không sao chép runtime/plugin hoặc yêu cầu license Esri |
| **ENVI Deep Learning** | Module cài/license riêng; hướng dẫn grid/object/pixel; cấu hình ONNX gồm metadata, số kênh, kích thước, tiền/hậu xử lý; xem metrics và ma trận nhầm lẫn [M5], [M6], [M7], [M8] | Tách task và input contract; model package có version/license; kết quả đánh giá gắn đúng lần train | ONNX đơn lẻ chưa đủ để chạy đúng; không suy ra tất cả model ONNX đều hỗ trợ |
| **Picterra Forge** | Training areas, accuracy areas; cảnh báo vùng train/test chồng nhau; quản lý kết quả và thuộc tính; báo cáo kết quả/monitoring có thống kê theo thời gian [M9], [M10], [M11], [M12] | Quy trình có hướng dẫn, cảnh báo tại vị trí lỗi, xem/sửa kết quả, thống kê và báo cáo dùng cùng dữ liệu | Detection area của Picterra có thể được đơn giản hóa; GeoAI cần giữ AOI đo đạc chính xác. Không dùng điểm accuracy trong sản phẩm thay cho kiểm định độc lập |
| **UP42** | Tìm và preview scene, chọn sản phẩm, quyền truy cập/EULA, xác nhận order và ngân sách, theo dõi dữ liệu giao; storage truy xuất bằng STAC [M13], [M14] | Tách catalog, quyền truy cập, mua dữ liệu và tải dữ liệu; mỗi trạng thái phải rõ | Đây là tham chiếu thu nhận/quản lý dữ liệu, không phải bằng chứng về pipeline AI của GeoAI |
| **Google Earth Engine** | Môi trường interactive và batch khác nhau; task có ID, trạng thái, hủy và retry; quota cho request, batch, bộ nhớ và storage [M15], [M16] | Preview nhẹ tách khỏi batch; job có vòng đời, giới hạn tài nguyên và lỗi có cấu trúc | Là xử lý từ xa; thuật ngữ batch “offline” của EE không có nghĩa chạy được khi mất Internet |
| **Trimble eCognition — tham chiếu lịch sử** | Trang sản phẩm mô tả OBIA + AI, ruleset, phối hợp raster/point cloud/GIS và batch; đồng thời ghi **“no longer actively sold”** [M17] | Gói nghiệp vụ nên kết hợp thuật toán, quy tắc hình học và chỉ tiêu thay vì chỉ gọi model | Không dùng làm lựa chọn mua mới đang được bán tích cực; không suy ra đã chấm dứt mọi hỗ trợ khách hàng cũ |

Ba dòng đầu là sản phẩm phân tích GeoAI gần nhất với trải nghiệm cần xây. UP42 và Earth Engine bổ sung tham chiếu về dữ liệu và vận hành. Những trang quảng bá về tốc độ/độ chính xác không được dùng làm ngưỡng nghiệm thu.

<a id="muc-3-3"></a>

### 3.3. Chuyển tham chiếu thành yêu cầu

| Mã | Yêu cầu cần làm rõ | Quyết định đề xuất | Căn cứ | Bằng chứng nghiệm thu |
| --- | --- | --- | --- | --- |
| R01 | Một model “được hỗ trợ” nghĩa là gì? | Có manifest, input contract, runtime profile và evaluation record | ArcGIS, ENVI | Chặn sai kênh/đơn vị/shape; chạy fixture CPU/GPU đúng ngưỡng |
| R02 | Độ chính xác áp dụng ở đâu? | Ghi vùng, thời gian, tập nhãn, phương pháp chia mẫu và metrics theo lớp | ArcGIS, ENVI, Picterra, [C2] | Truy được evaluation dataset; không dùng tập test để chỉnh threshold |
| R03 | Kết quả sai được xử lý thế nào? | Bản dự đoán bất biến + bản sửa của chuyên gia + trạng thái duyệt | ArcGIS review, Picterra | Đổi nhãn/geometry không ghi đè kết quả gốc; báo cáo trỏ đúng revision |
| R04 | Tìm thấy scene có nghĩa đã tải được chưa? | Capability và trạng thái truy cập/tải riêng | UP42 | Phân biệt preview-only, cần quyền, sẵn sàng đọc, đang tải và lỗi |
| R05 | Job thành công/hủy nghĩa là gì? | Hoàn tất khi artifact đã kiểm tra và công bố; hủy cần được xác nhận | Earth Engine | Crash/retry không tạo kết quả giả; worker cũ không công bố đè |
| R06 | Báo cáo dùng phiên bản nào? | ReportContext đóng băng result revision, metrics và template | Picterra + [A], [B] | Bản đồ/bảng/PDF khớp; báo cáo cũ không đổi khi rerun |
| R07 | Có cần mọi công nghệ ngay? | Một cấu hình local, một nghiệp vụ; mở rộng theo cổng nghiệm thu | [A], [B], [C2] | Danh sách hỗ trợ và bộ cài khớp năng lực đã kiểm tra |
| R08 | Có xử lý từ xa hoặc phát sinh chi phí không? | Hiển thị nơi chạy, quyền dữ liệu và dự toán khi có; thao tác mua riêng | UP42, Earth Engine | Search không tự đặt mua; không âm thầm gửi dữ liệu local lên cloud |
| R09 | Workflow ngành gồm những gì? | Domain Pack có dữ liệu, thuật toán, quy tắc, chỉ tiêu, quality gate và báo cáo | eCognition, [A], [B] | Một engine chạy được feature có phiên bản, không sao chép GPU logic |

Các chính sách bất biến, revision, quyền công bố và fencing ở dưới là **thiết kế đề xuất của GeoAI**; không tuyên bố các sản phẩm tham chiếu đều triển khai giống vậy.

---

**Tài liệu liên quan:**

- [Định hướng sản phẩm và cấu hình triển khai](01_dinh_huong_san_pham.md)
- [Nguồn tham khảo và lịch sử tài liệu](17_nguon_tham_khao_va_lich_su.md)

[A]: <../solution/de_xuat_kien_truc_he_thong_geoai.md>
[B]: <../solution/de_xuat_kien_truc_he_thong_geoai_copilot.md>
[C1]: <../solution/cam_nang_kien_truc_ung_dung_geoai_vien_tham.md>
[C2]: <../solution/Hướng dẫn xây dựng ứng dụng GeoAI cho viễn thám.md>
[M1]: https://doc.esri.com/en/arcgis-pro/latest/help/analysis/deep-learning/deep-learning-in-arcgis-pro.html
[M2]: https://doc.esri.com/en/arcgis-pro/latest/help/analysis/image-analyst/deep-learning-models-in-arcgis.html
[M3]: https://doc.esri.com/en/arcgis-pro/latest/tool-reference/image-analyst/compute-accuracy-for-object-detection.html
[M4]: https://doc.esri.com/en/arcgis-pro/latest/help/analysis/image-analyst/review-results-from-deep-learning.html
[M5]: https://www.nv5geospatialsoftware.com/docs/Introduction.html
[M6]: https://www.nv5geospatialsoftware.com/docs/OverviewENVIDeepLearning.html
[M7]: https://www.nv5geospatialsoftware.com/docs/ConfigureONNXModel.html
[M8]: https://www.nv5geospatialsoftware.com/docs/ViewTrainingMetrics.html
[M9]: https://docs.picterra.ai/detectors/annotations/
[M10]: https://docs.picterra.ai/detectors/detector-insights/
[M11]: https://docs.picterra.ai/detection_results/
[M12]: https://docs.picterra.ai/reports/
[M13]: https://docs.up42.com/data/catalog-process
[M14]: https://docs.up42.com/data-management/assets
[M15]: https://developers.google.com/earth-engine/guides/processing_environments
[M16]: https://developers.google.com/earth-engine/guides/usage
[M17]: https://geospatial.trimble.com/en/products/software/trimble-ecognition
[T1]: https://stacspec.org/en
[T2]: https://docs.ogc.org/is/21-026/21-026.html
