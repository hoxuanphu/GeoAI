# Lưu trữ, artifact và project di động

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** SQLite/filesystem, publish, backup/export, pin/retention và tái lập offline.

<a id="muc-10"></a>

## 10. Lưu trữ, công bố artifact và project di động

<a id="muc-10-1"></a>

### 10.1. Phân loại dữ liệu

| Loại | Nơi lưu/nguồn sự thật | Quy tắc |
| --- | --- | --- |
| Project registry, hàng đợi, attempt, audit trạng thái | SQLite trong thư mục ứng dụng local | Một coordinator; không đặt DB đang mở trên network share/thư mục đồng bộ |
| Input gốc | Tham chiếu có kiểm tra hoặc bản copy do người dùng chọn | Không âm thầm nhân đôi kho ảnh; ghi rõ chế độ import |
| Input snapshot, run/revision manifest và artifact đã công bố | Thư mục project local có cấu trúc | Bất biến; database lưu chỉ mục và quan hệ để truy vấn |
| Cache tile/raster/model engine | Cache local có quota, cache key và pin/lease | Chỉ LRU trên dữ liệu đủ điều kiện xóa; artifact kết quả không thuộc cache |
| Staging/checkpoint | Theo job/attempt | Có owner, hạn mức và quy tắc dọn; không public trực tiếp |

SQLite WAL yêu cầu các tiến trình truy cập ở cùng máy; tài liệu SQLite không hỗ trợ WAL qua network filesystem [T5]. Bản đầu dùng một project writer; mở project để sửa từ instance thứ hai phải bị chặn bằng khóa do hệ điều hành quản lý, không dựa vào PID cũ đơn thuần.

Bản đầu hỗ trợ **project đang xử lý, staging, cache và database trên ổ local**; không ghi project đang hoạt động trực tiếp trên SMB/network share hoặc thư mục đồng bộ. Ổ mạng có thể là nguồn chỉ đọc hoặc đích lưu trữ/export. Với nguồn mạng, benchmark đọc theo cửa sổ và chọn staging local khi cần; không kết luận mọi SMB đều chậm. HTTP Range thuộc chặng viewer–asset API; backend mở file SMB là chặng filesystem khác. Thiết kế phải xử lý mất kết nối và kiểm tra input identity trước khi tiếp tục.

<a id="muc-10-2"></a>

### 10.2. Công bố kết quả

1. Worker ghi vào staging theo attempt; kiểm tra metadata, khả năng mở, coverage và checksum.
2. Coordinator xác nhận attempt còn hiệu lực, chưa bị hủy và đủ artifact cần thiết.
3. Chuyển output hoàn chỉnh trong cùng volume sang vị trí bất biến; đăng ký manifest và metadata trong transaction. Transaction kiểm tra lại token/trạng thái attempt và ràng buộc duy nhất của lần công bố để xử lý cạnh tranh với cancel/retry.
4. API chỉ phục vụ kết quả có bản ghi công bố hợp lệ. Startup reconcile output chưa đăng ký và metadata thiếu file; kết quả thiếu file bị báo lỗi khả dụng, không hiển thị như dữ liệu đầy đủ.

Filesystem và SQLite không tạo thành một transaction chung. Quy trình dựa trên bước có thể lặp an toàn và reconcile, không hứa thực thi đúng một lần. Server dùng object bất biến + con trỏ manifest; không mô phỏng rename filesystem trên S3.

<a id="muc-10-3"></a>

### 10.3. Export project và backup

Project export có manifest liệt kê file/hash, version, kết quả/revision/báo cáo, dữ liệu nguồn được kèm và dữ liệu còn tham chiếu ngoài. Export metadata-only phải được gắn rõ; không quảng bá là bản sao tự chạy offline. Gói chia sẻ không chứa credential hoặc đường dẫn bí mật của máy gốc.

Backup metadata dùng cơ chế backup SQLite phù hợp hoặc dừng ghi/checkpoint theo quy trình; không copy riêng `.db` đang mở rồi bỏ qua WAL. Backup project bao gồm artifact và nguồn cần thiết, có retention và thử restore trên thư mục/máy khác. Có thể tái dựng chỉ mục artifact từ manifest; không giả định manifest có đủ lịch sử job/audit để thay thế backup database.

<a id="muc-10-4"></a>

### 10.4. Pin, retention và khả năng tái lập

Snapshot cố định danh tính và cách chọn dữ liệu; việc giữ byte nguồn là một chính sách riêng. Người dùng thấy trạng thái: **đủ dữ liệu để tái lập offline**, **cần lấy lại nguồn**, hoặc **thiếu nguồn/phiên bản**. Xuất lại báo cáo từ artifact/snapshot đã lưu không đồng nghĩa chạy lại được toàn bộ phân tích.

| Nhóm | Chính sách giữ dữ liệu | Điều kiện giải phóng |
| --- | --- | --- |
| Job đang chạy hoặc checkpoint còn hiệu lực | Pin/lease các input local, intermediate/checkpoint và model/runtime version cần dùng; thông tin lease được lưu bền vững | Job kết thúc và hết nhu cầu resume theo retention; crash phải reconcile lease trước GC |
| Run được chọn “giữ để tái lập offline” | Pin dependency closure có kiểm kê: input/window đủ cho pipeline, mask/grid, model + decoder hoặc PhysicalModelSpec/parameter/forcing/biên, cấu hình và runtime/solver cần thiết | Chỉ bỏ pin theo lựa chọn rõ ràng hoặc chính sách lưu trữ đã chấp thuận; kiểm tra những run khác còn dùng |
| Snapshot lịch sử chỉ giữ tham chiếu | Giữ manifest/version/hash và artifact kết quả; không mặc định pin toàn bộ scene mãi mãi | Cache nguồn có thể bị dọn; chạy lại phải resolve đúng phiên bản và xác minh nội dung |
| Cache có thể tái tạo | LRU/quota chỉ áp dụng khi không có pin/lease hoặc dependency được bảo vệ | Không được xóa artifact kết quả, báo cáo, nguồn do người dùng quản lý hoặc model đang dùng |

Pin chỉ có hiệu lực với dữ liệu GeoAI quản lý. File ngoài project/ổ mạng có thể bị chủ sở hữu thay/xóa; chế độ offline phải copy phần cần thiết vào kho quản lý, xác minh hash và kiểm tra quyền sao chép. Không gọi một URL hoặc tên scene là bản backup.

Coordinator quản lý pin theo ID nội dung và danh sách chủ sở hữu để các run dùng chung dữ liệu. GC phải phối hợp với việc tạo lease để không xóa file vừa được job nhận dùng. Có quota cho dữ liệu được giữ; khi thiếu đĩa thì dừng nhận job/copy và cho người dùng quản lý retention, không tự gỡ pin để chạy tiếp. Chỉ giữ các cửa sổ cần thiết nếu chúng đủ để tái lập preprocessing/context; không tự cho rằng một crop nhỏ luôn thay được toàn scene.

---

**Tài liệu liên quan:**

- [Hợp đồng dữ liệu và versioning](05_hop_dong_du_lieu_va_versioning.md)
- [Job, tài nguyên và phục hồi](08_job_tai_nguyen_va_phuc_hoi.md)
- [Revision, Domain Pack và báo cáo](11_revision_domain_pack_va_bao_cao.md)
- [Bảo mật, hướng lên server và vận hành](14_bao_mat_server_va_van_hanh.md)

[T5]: https://sqlite.org/wal.html
