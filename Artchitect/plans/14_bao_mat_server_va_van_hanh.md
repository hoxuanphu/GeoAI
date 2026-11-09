# Bảo mật, hướng lên server và vận hành

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Bảo mật local/server, adapter triển khai, quyền, log và chẩn đoán.

<a id="muc-15"></a>

## 15. Bảo mật và hướng lên server

<a id="muc-15-1"></a>

### 15.1. Bảo mật local

Desktop API bind loopback, token phiên và kiểm tra origin; shell giới hạn lệnh/sidecar được phép. Asset API resolve ID đã đăng ký, không nhận path/URL tùy ý. Credential lưu trong kho hệ điều hành (Windows Credential Manager hoặc cơ chế tương đương đã kiểm chứng); log và manifest loại bỏ secret. Import archive/pack kiểm tra đường dẫn, kích thước và nội dung trước giải nén/kích hoạt.

[SPEC-009](../docs/specs/009-importer-worker-resolver.md) và [ma trận importer/resolver](../docs/importer-resolver-security.md) bổ sung ca kiểm archive traversal/ADS/reparse point, giới hạn giải nén, VRT tham chiếu phụ, URL/redirect/DNS theo provider policy và candidate khác project/attempt. Kiểm canonical path phải phối hợp handle/file identity để tránh đổi đích sau kiểm; input ngoài project đã được cấp quyền không bị cấm chỉ vì vị trí. Đây là tiêu chí phải thực hiện, chưa có importer hoặc test bảo mật đã pass.

Shell trao cổng loopback và token ngẫu nhiên đủ mạnh của phiên cho UI qua IPC Tauri được giới hạn quyền, không qua URL. Cổng ngẫu nhiên chỉ tránh xung đột/giảm khả năng đoán, không thay xác thực. Bind `127.0.0.1` và kiểm tra `Host` đúng địa chỉ/cổng đã cấp; nếu hỗ trợ IPv6 phải cấu hình bind và allowlist rõ. Không tin `X-Forwarded-Host` từ request local.

Kiểm tra `Origin` theo allowlist đúng phiên bản Tauri/WebView2, tách cấu hình phát triển khỏi bản phát hành; không dùng CORS wildcard như biện pháp bảo vệ. Request có Origin không hợp lệ bị từ chối. Với loader/native client có thể không gửi Origin, quy định rõ đường được phép và vẫn bắt buộc token/Host; không cho phép thiếu Origin để bỏ xác thực. Áp dụng nhất quán cho API điều khiển, SSE, tile, Range asset, export và report; transport progress phải gửi được token mà không đưa vào query string.

G1/G3 thử request sai Host/Origin, thiếu/sai token, token của phiên cũ sau khởi động lại và các đường loader/web worker theo [mục 11](10_viewer_gis_3d_va_kiem_tra_ket_qua.md#muc-11). Token phiên không lưu trong project, gói chẩn đoán hoặc manifest; log phải lọc cả header. Cơ chế loopback bảo vệ ranh giới truy cập ứng dụng, không được mô tả là chống mọi tiến trình độc hại chạy cùng tài khoản hệ điều hành.

<a id="muc-15-2"></a>

### 15.2. Hướng lên server

| Thành phần | Local Workstation | Server |
| --- | --- | --- |
| Job store | SQLite/coordinator | PostgreSQL; đánh giá Procrastinate làm queue adapter |
| Metadata và truy vấn không gian | SQLite index + dịch vụ GIS | PostgreSQL/PostGIS; pgSTAC nếu cần catalog service |
| Artifact | Filesystem | Filesystem hoặc S3-compatible theo quy mô |
| Runtime | Worker local CPU/CUDA | Worker CPU/CUDA kiểm chứng riêng trên Linux |
| Identity | Phiên local, quyền hệ điều hành | HTTPS, OIDC, project roles, audit và quota |
| UI | Tauri | Browser hoặc Desktop Client |

Server vẫn có scheduler RAM/VRAM/I/O; không coi Procrastinate là bộ lập lịch GPU. SQLite và PostgreSQL không thay thế trong suốt: kiểm tra semantics của claim, migration và truy vấn; dùng cùng fixture để so sánh kết quả nghiệp vụ, không bắt buộc bit-identical giữa mọi backend số học.

Quyền phải được kiểm tra trên job, tile, Range asset, export và report. Nếu triển khai quyền theo AOI, không chỉ lọc danh sách item: phải bảo đảm tile/crop/download không trả dữ liệu ngoài phạm vi được phép. Bản server đầu có thể dùng project/asset authorization; quyền theo AOI chỉ phát hành sau khi có đường phục vụ dữ liệu đáp ứng được.

Không tự gửi ảnh/nhãn ra ngoài máy. Chức năng remote compute cần nơi chạy, dữ liệu gửi, quyền truy cập và chi phí khi có được hiển thị rõ. Chính sách license lưu theo nguồn/model và điều kiện export; các kết luận pháp lý cụ thể cần xác minh theo hợp đồng và bối cảnh triển khai, không suy ra chỉ từ tên nguồn “mở”.

<a id="muc-15-3"></a>

### 15.3. Vận hành, chẩn đoán và kiểm tra phát hành

Log có cấu trúc, thời gian UTC, level/event/error code, `project_id`, `job_id`, `attempt_id`, phase và correlation ID. Lỗi model ghi version/backend/precision, lỗi địa lý ghi `TransformSpec` ID; không ghi credential, signed URL hoặc dump toàn bộ input. Rotation/retention và quota log được cấu hình; thiếu đĩa phải được phát hiện trước job và không làm log vô hạn chiếm chỗ artifact.

Gói chẩn đoán do người dùng xuất gồm phiên bản app/OS/runtime/driver, capability report, health, mã lỗi, log đã lọc và manifest rút gọn cần tái hiện. Mặc định loại ảnh, nhãn, geometry nhạy cảm và đường dẫn cá nhân; cho xem nội dung trước khi chia sẻ. Crash report local lưu exit code/signal hoặc lỗi native thu được, last heartbeat/phase và correlation ID. Không tự upload gói chẩn đoán hoặc crash dump; dump bộ nhớ chỉ thu theo chế độ hỗ trợ riêng vì có thể chứa dữ liệu.

Mỗi lỗi hiển thị được nguyên nhân có thể xử lý, trạng thái dữ liệu/job và bước khắc phục: thiếu runtime, sai band/CRS, thiếu grid, hết RAM/VRAM/đĩa, mất nguồn, protocol lỗi. Hướng dẫn hỗ trợ dùng job/attempt ID và gói chẩn đoán, không yêu cầu người dùng suy đoán model hoặc chạy lại nhiều lần.

Kiểm tra tự động gồm:

- CI CPU cho schema, CRS/normalization, job/IPC, report, packaging và fixture suy luận nhỏ trên các thay đổi liên quan. Benchmark workload lớn chạy định kỳ hoặc trước release, không bắt mọi sửa tài liệu chạy model lớn.
- Khi tạo/tách package backend, kiểm tra hướng import tại [mục 5.1](04_kien_truc_thuc_thi_va_module.md#muc-5-1); với repository/migration, chạy SQLite contract và upgrade/restore tại [mục 5.2](04_kien_truc_thuc_thi_va_module.md#muc-5-2). PostgreSQL bổ sung khi làm adapter server; lịch GPU hàng đêm chỉ thêm nếu tần suất thay model và ngân sách cần đến.
- Trước phát hành compute pack/model mới: chạy bài kiểm tra tự động trên NVIDIA reference bằng GPU runner **hoặc máy kiểm thử chuyên dụng**. Kiểm tra gói cuối trên Windows sạch; không xem việc pass trong môi trường phát triển là bằng chứng installer đủ dependency.
- Bộ **golden fixture/output có phiên bản** gồm input hash, ModelSpec, preprocessing tensor tham chiếu, logits/probability phù hợp, nhãn, grid/coverage và metrics. Tách fixture kỹ thuật G1 với decoder ngẫu nhiên khỏi golden output nghiệp vụ của checkpoint thật theo [mục 13.2](12_runtime_cpu_nvidia_va_hieu_nang.md#muc-13-2). So CPU/ONNX/CUDA/PyTorch với tolerance tuyệt đối/tương đối và ngưỡng chất lượng theo lớp khi có model nghiệp vụ; không yêu cầu bit-identical giữa mọi backend.
- G1 chốt tolerance trước tối ưu. Cập nhật golden output phải có lý do, review và version mới; không tự ghi đè output chuẩn để làm test pass. Thay runtime, band mapping, quantization hoặc decoder phải chạy lại các kiểm tra bị ảnh hưởng.

---

**Tài liệu liên quan:**

- [Kiến trúc thực thi và ranh giới module](04_kien_truc_thuc_thi_va_module.md)
- [Job, tài nguyên và phục hồi](08_job_tai_nguyen_va_phuc_hoi.md)
- [Lưu trữ, artifact và project di động](09_luu_tru_artifact_va_project.md)
- [Stack và bộ cài Windows](13_stack_va_bo_cai_windows.md)
- [Lộ trình và cổng nghiệm thu](15_lo_trinh_va_cong_nghiem_thu.md)
