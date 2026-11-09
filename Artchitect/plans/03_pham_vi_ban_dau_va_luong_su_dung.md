# Phạm vi bản đầu và luồng sử dụng

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Chọn nghiệp vụ G0, phạm vi phát hành đầu, phần hoãn và luồng giao diện.

<a id="muc-4"></a>

## 4. Phạm vi bản đầu và luồng sử dụng

<a id="muc-4-1"></a>

### 4.1. Lát cắt nghiệp vụ và đánh đổi tại G0

Phạm vi khởi đầu đã được người dùng xác nhận: **bản đồ lớp phủ trên HLS S30 v2 ở 30 m, dùng Prithvi-EO-2.0 đã gắn decoder và tinh chỉnh cho bộ 7 lớp, kèm chỉ số NDVI/EVI/NDMI/MNDWI, thống kê theo vùng và PDF tiếng Việt**. HLS phù hợp với miền dữ liệu tiền huấn luyện của Prithvi hơn việc mặc định dùng trực tiếp Sentinel-2 L2A 10 m [P1]. AOI có thể vẽ, lấy từ footprint/ảnh import hoặc import Shapefile; geometry/CRS/hash phải giữ trong snapshot. Crosswalk WorldCover/JAXA và profile T=3 cần QC/kiểm định; T=1 chỉ cho spike kỹ thuật. Các gate vẫn phải chốt tại G0; yêu cầu có Prithvi từ bản đầu giữ nguyên.

**Ghi nhận G0 từng phần, 08/11/2026:** người dùng chốt chia đợt; đợt đầu như trên, sau đó bổ sung giám sát rừng/mất rừng, đất ngập nước/ngập lụt và profile 10/5/1 m. Chỉ tiêu định lượng chuyên sâu về đất/cây trồng bổ sung sau. Ưu tiên nguồn mở/miễn phí, ảnh thương mại khi có quyền và ngân sách; mục tiêu nguồn ảnh toàn cầu được thực hiện qua adapter và product profile có kiểm chứng, không là cam kết truy cập mọi nguồn. HLS chỉ ở 30 m; mức 10/5/1 m cần nguồn/profile/model và kiểm định riêng, resample không tạo chi tiết quan trắc mới. Mục tiêu máy ít nhất 20 GB RAM/8 GB VRAM chưa phải cấu hình đã benchmark. [Decision record G0](../docs/evidence/g0/decision-record.md) lưu phát biểu và phần còn thiếu; G0 chưa đạt.

| Phương án | Lợi thế | Chi phí/rủi ro | Quan hệ với Prithvi và quyết định G0 |
| --- | --- | --- | --- |
| Lớp phủ HLS 30 m | Khớp sáu kênh và nguồn tiền huấn luyện; kiểm chứng được pipeline và thống kê | Mây, pixel hỗn hợp, cần nhãn đúng lớp và thời điểm; không phù hợp đối tượng nhỏ | Khuyến nghị nếu có AOI/nhãn phù hợp; bắt đầu HLS S30, L30 thêm sau khi xác minh profile |
| Lớp phủ Sentinel-2 L2A | Có thể phù hợp hơn khi cần độ phân giải cao hơn | Band/GSD/normalization khác HLS; resample không tự tạo tính tương đương | Chỉ thay profile HLS khi đã fine-tune và kiểm định riêng; không đưa ảnh 10 m vào checkpoint HLS rồi mặc định chất lượng giữ nguyên |
| Nước/ngập từ quang học HLS | Có thể dùng Prithvi cho phân đoạn nhị phân và thống kê | Vẫn chịu mây; cần phân biệt nước thường xuyên với ngập mới và có nhãn sự kiện | Phương án Prithvi khác nếu nghiệp vụ/nhãn thuận lợi hơn lớp phủ; vẫn chỉ chọn một feature đầu |
| Ngập Sentinel-1 RTC | Không phụ thuộc mây quang học; baseline ngưỡng hữu ích cho mặt nước | Bóng địa hình, ngập đô thị/dưới tán, nước thường xuyên và khác biệt tiền xử lý; dataset công khai không thay kiểm định địa phương | Không đưa trực tiếp VV/VH vào Prithvi quang học. Feature S1 đơn lẻ không đáp ứng yêu cầu Prithvi từ bản đầu; chọn sau hoặc lập phạm vi riêng nếu cần |

G0 so sánh nhu cầu, khả năng quan sát theo mùa, nguồn ảnh, nhãn địa phương, độ phân giải, chất lượng và ngân sách CPU. Có dataset công khai hoặc ít lớp hơn chưa đủ để kết luận bài toán ngập luôn dễ hơn. Cấu hình flood mẫu của dự án Prithvi dùng sáu kênh quang học; tên dataset Sen1Floods11 không có nghĩa model đó nhận trực tiếp SAR [P3].

Đầu ra G0 phải có khảo sát coverage HLS theo [mục 7.5](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md#muc-7-5), đường truy cập đã thử và kế hoạch nhãn bắt đầu ngay trong G0. Chốt ngưỡng chất lượng tuyệt đối, ngân sách thử nghiệm và quy tắc dừng tại [mục 8.5](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-5); không yêu cầu Prithvi phải thắng baseline mới được nghiệm thu. Spike kỹ thuật G1 có thể chạy song song với gán nhãn theo [mục 13.2](12_runtime_cpu_nvidia_va_hieu_nang.md#muc-13-2), nhưng kết quả với decoder ngẫu nhiên không thay nghiệm thu model nghiệp vụ.

Điều kiện nghiệm thu feature: có AOI, nguồn, bộ lớp, dữ liệu huấn luyện/kiểm định phù hợp và model nghiệp vụ đạt quality gate. Nếu chưa đủ nhãn, có thể làm prototype để kiểm chứng kỹ thuật, nhưng chưa hoàn thành điều kiện phát hành phân tích nghiệp vụ. Không thay yêu cầu Prithvi bằng một demo tái tạo ảnh hoặc chỉ có mục chọn model trên giao diện.

Năng lực bản đầu:

- Project, import raster/vector, AOI, chọn scene và xem metadata/QA.
- Một adapter STAC được khóa collection/product profile HLS đã chọn; không cam kết tích hợp mọi provider ngay. Import COG local của cùng profile phục vụ offline.
- Một feature dùng **Prithvi-EO-2.0 + decoder có trọng số nghiệp vụ**, chạy từ dữ liệu đến bản đồ/báo cáo; baseline RF/boosting dùng cùng tập kiểm tra để đối chứng.
- Công thức đo diện tích/coverage và tập chỉ số phổ được chọn cho baseline theo [mục 8.7.1](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-7-1). Danh mục mô hình toán–vật lý ở [mục 8.6](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-6) được tích hợp theo Domain Pack và dữ liệu kiểm định; các feature LAI, ET, dòng chảy, thủy lực, xói mòn, sinh khối/carbon là mở rộng G4, không đồng loạt trở thành điều kiện phát hành feature lớp phủ đầu.
- CPU chạy được feature Prithvi trên workload tối thiểu đã chốt; NVIDIA kiểm chứng trên cùng model nghiệp vụ. Model nhỏ giả lập không thay thế bài nghiệm thu Prithvi.
- Bản đồ nguồn/kết quả, bảng thuộc tính, vùng thiếu dữ liệu, thống kê; hai trạng thái chưa duyệt/đã duyệt. Sửa thuộc tính trong app, sửa hình học qua QGIS/GeoPackage.
- DEM COG và COPC ở mức đọc/hiển thị để kiểm chứng viewer; phân tích AI LiDAR là giai đoạn sau.
- Job nền, hủy, khôi phục sau lỗi, export COG/vector phù hợp và PDF có provenance.
- Bộ cài Windows x64 Standard; profile Offline chỉ công bố sau khi vượt bài kiểm tra ngắt mạng.

Hoãn: huấn luyện sâu ngay trong desktop, AMD AI runtime, InSAR/SLC, marketplace plugin, chat agent tự thực thi, cloud mua ảnh tự động, nhiều ngành cùng lúc, microservices, Kubernetes và đồng bộ project nhiều người dùng theo thời gian thực.

<a id="muc-4-2"></a>

### 4.2. Luồng giao diện

**Mở project → nhập/tìm dữ liệu → chọn AOI/scene → kiểm tra dữ liệu → chọn feature/model → xem cấu hình chạy → chạy nền → kiểm tra/sửa/duyệt → thống kê → xuất báo cáo.**

Trước khi chạy, hiển thị nguồn/ngày ảnh, vùng quan sát hợp lệ, model và lớp đầu ra, nơi xử lý, backend, dung lượng đĩa ước tính nếu có. ETA chỉ hiển thị khi có số liệu đo; ghi rõ là ước tính. Các điều kiện không tương thích phải chỉ ra nguyên nhân và cách sửa.

Workspace lấy bản đồ làm trung tâm; các panel Dữ liệu, Phân tích, Kết quả, Báo cáo và Tài nguyên dùng cùng project state. Đổi panel giữ camera, AOI, layer, selection, filter, timeline và job. Trình tự có hướng dẫn phục vụ người mới; người có kinh nghiệm có thể mở lại từng bước.

---

**Tài liệu liên quan:**

- [Định hướng sản phẩm và cấu hình triển khai](01_dinh_huong_san_pham.md)
- [Model Prithvi, dữ liệu nhãn và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md)
- [Viewer GIS/3D và kiểm tra kết quả](10_viewer_gis_3d_va_kiem_tra_ket_qua.md)
- [Lộ trình và cổng nghiệm thu](15_lo_trinh_va_cong_nghiem_thu.md)

[P1]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL/raw/63adbd39c271da4c42f447e69b1a7c91a338cdc9/README.md
[P3]: https://raw.githubusercontent.com/NASA-IMPACT/Prithvi-EO-2.0/main/configs/sen1floods11.yaml
