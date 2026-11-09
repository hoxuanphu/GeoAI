# Job, tài nguyên và phục hồi

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Vòng đời job, attempt, hủy/retry, scheduler và giao thức worker.

<a id="muc-9"></a>

## 9. Job, tài nguyên và phục hồi

<a id="muc-9-1"></a>

### 9.1. Vòng đời

Trạng thái job: `queued → running → succeeded / failed`; hủy dùng `cancel_requested → cancelled` khi việc dừng đã được xác nhận. Retry tạo attempt mới trong cùng job, có backoff và giới hạn. Một job đã công bố thành công không bị đổi thành cancelled do yêu cầu đến muộn.

`phase` mô tả bước `resolve/validate/preprocess/infer/postprocess/measure/publish`, tách khỏi trạng thái job. Tiến độ đo bằng đơn vị công việc khi biết tổng; không hiển thị phần trăm giả cho bước chưa ước lượng được. SSE hỗ trợ reconnect; UI đọc lại trạng thái chuẩn từ API nếu bỏ lỡ sự kiện.

<a id="muc-9-2"></a>

### 9.2. Trách nhiệm và chống công bố trùng

- Một coordinator ghi trạng thái SQLite ở bản desktop; worker gửi event và artifact candidate. Hàng đợi không tạo một transaction cho từng pixel hoặc từng cửa sổ nhỏ.
- Mỗi attempt có ID, heartbeat và token thế hệ. Khi timeout/retry, token cũ hết hiệu lực; coordinator từ chối mọi yêu cầu công bố của worker cũ, kể cả worker đó vẫn chạy.
- Khóa idempotency chống lặp yêu cầu của client. Nó khác content cache key: người dùng vẫn có thể chủ động tạo một run mới với cùng input để đối chứng.
- Giới hạn retry cho lỗi tạm thời; sai CRS/band/operator, thiếu quyền hoặc model không tương thích không được lặp vô hạn.
- Checkpoint chứa cấu hình/input/model hash và danh sách chunk hoàn tất. Chỉ resume khi hợp đồng còn khớp; nếu không, khởi chạy lại có giải thích.
- Với model vật lý, khóa thêm PhysicalModelSpec/parameter/forcing/biên và solver version. Phép tính điểm/ô có thể checkpoint theo mảnh; solver thủy lực có trạng thái liên kết không gian/thời gian chỉ resume bằng checkpoint native đã kiểm chứng. Không chia solver liên kết thành các tile độc lập như suy luận Prithvi; nếu không có checkpoint an toàn thì ghi capability không hỗ trợ resume và chạy lại có giải thích.
- Sau crash, xác định attempt mất heartbeat, thu hồi tài nguyên, kiểm tra staging và đối chiếu artifact. Không coi file tồn tại là bằng chứng job thành công.

<a id="muc-9-3"></a>

### 9.3. Chính sách đóng ứng dụng

Mặc định đóng cửa sổ là yêu cầu thoát ứng dụng. Nếu có job đang chạy, người dùng chọn quay lại hoặc dừng có kiểm soát rồi thoát; không âm thầm tiếp tục xử lý nền. Worker dừng ở checkpoint; quá thời hạn dừng cho phép kết thúc nhóm tiến trình và đánh dấu attempt bị gián đoạn. “Chạy tiếp ở khay hệ thống” chỉ thêm sau khi có yêu cầu và kiểm chứng vòng đời riêng.

Trên Windows, shell quản lý sidecar và worker trong **Job Object**, cân nhắc `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` để thu hồi tiến trình khi shell chết [T15]. Launcher phải xác nhận các tiến trình con thực sự thuộc nhóm, không vô tình kế thừa handle giữ nhóm sống hoặc cho phép breakaway ngoài chính sách. Job Object là cơ chế thu hồi, không tự tạo checkpoint: thoát bình thường vẫn gửi yêu cầu dừng, chờ xác nhận có giới hạn rồi mới kết thúc nhóm. Crash/force-kill chỉ resume từ chunk đã ghi hoàn tất, checksum và input/model/config còn khớp; G1 kiểm tra cả shell crash và worker native treo.

<a id="muc-9-4"></a>

### 9.4. Resource scheduler

Ngân sách gồm CPU thread, RAM, VRAM, I/O, đĩa tạm và số request nguồn. Số job khác số thread GDAL/BLAS/PyTorch. Một worker chính trên mỗi GPU ở bản đầu; giữ phần tài nguyên cho viewer và hệ điều hành. Queue library không thay thế bộ điều phối GPU này.

Phạm vi điều phối bản đầu được cụ thể hóa ở [ADR-011](../docs/adr/ADR-011-local-execution-owner.md), trạng thái đề xuất có điều kiện G1: một phiên GeoAI giữ quyền thực thi tác vụ nặng cho một tài khoản Windows trên máy, kể cả nhiều project hoặc session đăng nhập của cùng tài khoản. Phiên sở hữu chỉ chạy một job nặng tại một thời điểm; instance khác không tự khởi động worker/model resident. Khóa quyền thực thi liên process khác khóa writer từng project và khác attempt fencing; timeout/heartbeat hết hạn chưa đủ để cấp lại tài nguyên khi worker cũ chưa được xác nhận dừng. Chưa cam kết điều phối nhiều tài khoản/ứng dụng ngoài GeoAI hoặc xây dịch vụ Windows toàn máy.

Khi hết VRAM, giảm batch và retry có giới hạn; không tự đổi kích thước cửa sổ trái ModelSpec. Mặc định worker tự đọc asset/checkpoint đã được cấp quyền bằng cửa sổ và ghi output vào staging của attempt. Giữa các tiến trình chỉ truyền tham chiếu và điều khiển theo [mục 9.5](08_job_tai_nguyen_va_phuc_hoi.md#muc-9-5). Ưu tiên giảm I/O thừa, prefetch có giới hạn và giữ model resident trước khi tối ưu kernel.

<a id="muc-9-5"></a>

### 9.5. Giao thức điều khiển worker và đường dữ liệu

Chọn **JSON-RPC 2.0 qua stdin/stdout riêng của từng worker** cho coordinator local; UI–API giữ HTTP/SSE. Đây là lựa chọn triển khai local của GeoAI: đặc tả JSON-RPC không quy định transport [T9]. Worker giữ model resident qua nhiều task nếu ngân sách cho phép.

- Framing local: UTF-8, mỗi thông điệp JSON trên một dòng, newline trong chuỗi được escape; giới hạn ban đầu 1 MiB/thông điệp. Schema/protocol version được thương lượng lúc khởi động; thông điệp sai/thiếu dòng hoặc vượt giới hạn gây lỗi có thể chẩn đoán.
- Các lệnh tối thiểu: `capabilities`, `start`, `cancel`, `shutdown`; event gồm heartbeat, phase/progress, artifact candidate và structured error. Mọi thông điệp của attempt có `job_id`, `attempt_id`, generation token; `start` trả xác nhận nhận việc, kết quả hoàn tất gửi sau.
- `stdout` chỉ dành cho protocol; log đi `stderr` hoặc file theo job. Bắt/định tuyến output của thư viện native; dữ liệu lạc vào stdout được coi là lỗi protocol, không bỏ qua rồi tiếp tục đoán trạng thái.
- Bootstrap worker trước khi import GDAL/ONNX Runtime/CUDA: flush các buffer, giữ bản sao stdout gốc cho writer protocol nhị phân, rồi chuyển fd 1 sang stderr bằng cơ chế tương đương `os.dup(1)` và `os.dup2(2, 1)`. Writer duy nhất tuần tự hóa UTF-8 với byte LF, khóa ghi giữa các thread và flush sau thông điệp; không để thư viện dùng descriptor protocol.
- Trên Windows, kiểm tra cả CRT file descriptor và Win32 standard handle; cập nhật `SetStdHandle` khi cần để native code lấy handle mới ghi đúng đích. Handle đã cache có thể không theo thay đổi [T12], nên không coi hai lệnh `dup` là bảo đảm cho mọi DLL. Launcher cấp đủ stdin/stdout/stderr pipe và dùng `CREATE_NO_WINDOW` khi tạo worker console; `PYTHONUTF8=1` chỉ hỗ trợ encoding Python, không thay chế độ binary hoặc định tuyến native. G1 kiểm tra sidecar đóng gói với log Python, CRT và Win32 đồng thời, kể cả giai đoạn import; bộ nhận vẫn fail rõ khi protocol nhiễm dữ liệu.
- Bộ nhận lệnh và heartbeat vẫn hoạt động khi suy luận. Coordinator đọc liên tục cả stdout/stderr, giới hạn buffer và giảm tần suất progress khi cần; không để log đầy pipe làm worker treo. Timeout nhận lệnh khác timeout chạy job; quá hạn request không tự chứng minh job đã dừng.
- Lệnh truyền `asset_id`, manifest, window/grid và resource budget. Worker resolve tham chiếu qua hợp đồng storage được cấp bởi coordinator; đường dẫn tùy ý từ UI không được chuyển thẳng vào worker. Kết quả là manifest/URI nội bộ của artifact đã ghi, không phải tensor nhúng JSON.
- [Worker resolver](../docs/worker-resolver.md) cụ thể hóa bootstrap tin cậy và access context tạm theo project/attempt; `start` của wire draft bổ sung context ID/hash. Coordinator materialize input remote trước start; worker bản đầu chỉ đọc manifest/input/model đã đăng ký và được cấp, không đọc SQLite/credential hay tự tìm lại catalog. File local ngoài project vẫn được phép nếu được đăng ký và xác minh; staging/output chỉ trong vùng ghi được cấp cho attempt. Mã/schema chưa được thay theo draft này; SPEC-001/009 phải đồng bộ trước triển khai runtime.
- Memmap/shared memory là tối ưu tùy chọn khi đo thấy việc chia sẻ tensor đã tiền xử lý có lợi. Khi dùng phải có owner/lease theo attempt, shape/dtype, quyền đọc/ghi, thời hạn sử dụng, close/cleanup khi crash. Chỉ truyền descriptor; không đưa cơ chế này thành dependency của luồng bản đầu.

Worker server về sau dùng queue/lease và storage adapter phù hợp; giao thức stdin/stdout không được coi là transport qua nhiều máy.

---

**Tài liệu liên quan:**

- [Kiến trúc thực thi và ranh giới module](04_kien_truc_thuc_thi_va_module.md)
- [Hợp đồng dữ liệu và versioning](05_hop_dong_du_lieu_va_versioning.md)
- [Lưu trữ, artifact và project di động](09_luu_tru_artifact_va_project.md)
- [Runtime CPU/NVIDIA và hiệu năng](12_runtime_cpu_nvidia_va_hieu_nang.md)
- [Bảo mật, hướng lên server và vận hành](14_bao_mat_server_va_van_hanh.md)

[T9]: https://www.jsonrpc.org/specification
[T12]: https://learn.microsoft.com/en-us/windows/console/getstdhandle
[T15]: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
