# Định hướng sản phẩm và cấu hình triển khai

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Mục tiêu, nguyên tắc, nhóm người dùng và các cấu hình local/server.

<a id="muc-1"></a>

## 1. Định hướng sản phẩm và quyết định tổng thể

Xây dựng **ứng dụng GeoAI cho chuyên gia GIS và người phân tích nghiệp vụ**, giúp đi từ dữ liệu địa lý đến kết quả có thể kiểm tra, thống kê và lập báo cáo. Giá trị của sản phẩm nằm ở tính đúng địa lý, quy trình sử dụng rõ ràng, kết quả truy nguyên được và vận hành ổn định trên máy người dùng.

Kiến trúc chọn **modular monolith Python + worker tách tiến trình**, giao diện **Tauri 2 + React + TypeScript + Giro3D**. Bản desktop dùng **SQLite WAL + filesystem local**. CPU là cấu hình sử dụng chính thức; NVIDIA tăng tốc theo model đã kiểm chứng. Bản đầu có **Prithvi-EO-2.0 + decoder nghiệp vụ**, cùng baseline RF/boosting để đối chứng. Ưu tiên ONNX Runtime cho suy luận; PyTorch là đường tham chiếu và ngoại lệ phân phối khi có lý do. Bản server bổ sung PostgreSQL/PostGIS, object storage, hàng đợi và xác thực nhiều người dùng khi có nhu cầu thực tế.

Các nguyên tắc xuyên suốt:

1. Prithvi-EO-2.0 có mặt từ bản đầu; bài toán và dữ liệu quyết định cách tinh chỉnh, decoder và phạm vi sử dụng. Baseline đơn giản được giữ để kiểm tra, không thay thế yêu cầu tích hợp Prithvi.
2. Một lõi nghiệp vụ dùng lại giữa local/server; adapter thay đổi nhưng hợp đồng và bộ dữ liệu kiểm chứng phải giữ tương đương.
3. Tách dữ liệu nguồn, kết quả tính toán, chỉnh sửa của chuyên gia và báo cáo thành các phiên bản liên kết được.
4. UI phản hồi nhanh; suy luận, chuyển đổi dữ liệu và xuất báo cáo là job chạy nền.
5. Công bố năng lực theo tổ hợp dữ liệu, model, runtime và phần cứng đã kiểm chứng.
6. Chuẩn mở ở ranh giới trao đổi; không bắt buộc cài một hệ thống thương mại được dùng làm tham chiếu.

<a id="muc-1-1"></a>

### 1.1. Người dùng và sản phẩm bàn giao

| Nhóm | Công việc chính | Thông tin cần nhìn thấy |
| --- | --- | --- |
| Chuyên gia GIS | Chọn dữ liệu, kiểm tra CRS/QA, cấu hình và chạy phân tích | Nguồn, ngày ảnh, vùng quan sát hợp lệ, tham số, trạng thái job |
| Chuyên gia nghiệp vụ | Đối chiếu thực tế, duyệt/sửa kết quả, xác nhận chỉ tiêu | Định nghĩa lớp, sai số, vùng cần kiểm tra, nguồn gốc chỉnh sửa |
| Người dùng báo cáo | Đọc bản đồ, số liệu và giới hạn áp dụng | Thời điểm dữ liệu, phạm vi, chất lượng, trạng thái duyệt |
| Quản trị viên ở bản server | Quản lý truy cập, tài nguyên, sao lưu và phát hành model | Quyền project/asset, quota, nhật ký, phiên bản và tình trạng phục hồi |

Một người có thể kiêm nhiều vai trò ở bản desktop. Bản đầu không cần hệ thống tài khoản nhiều người dùng cục bộ chỉ để mô phỏng các vai trò này.

<a id="muc-1-2"></a>

### 1.2. Cấu hình triển khai

| Cấu hình | Nơi xử lý | Database/storage | Thứ tự ưu tiên |
| --- | --- | --- | --- |
| **Local Workstation** | API và worker trên Windows người dùng | SQLite và filesystem local | Phát hành đầu tiên |
| **Server + Web Client** | Worker trên máy chủ | PostgreSQL/PostGIS và filesystem hoặc object storage | Sau khi hoàn thiện một nghiệp vụ local |
| **Desktop Client** | Kết nối tới server; không kèm worker local | Dữ liệu nghiệp vụ trên server | Đóng gói bổ sung khi có người dùng cần |

Mở UI bằng trình duyệt trên loopback có thể phục vụ phát triển/chẩn đoán, chưa phải một cấu hình phát hành riêng. GPU trình duyệt dùng để render; GPU tính toán thuộc máy chạy worker. Offline chỉ áp dụng cho chức năng có đủ dữ liệu, runtime, model và tài nguyên local.

---

**Tài liệu liên quan:**

- [Phạm vi bản đầu và luồng sử dụng](03_pham_vi_ban_dau_va_luong_su_dung.md)
- [Kiến trúc thực thi và ranh giới module](04_kien_truc_thuc_thi_va_module.md)
- [Quyết định cần chốt và đánh đổi](16_quyet_dinh_can_chot_va_danh_doi.md)
