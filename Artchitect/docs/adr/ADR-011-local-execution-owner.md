# ADR-011: Quyền thực thi local dùng chung giữa project và instance

**Trạng thái:** đề xuất triển khai có điều kiện kiểm chứng G1; chưa Accepted, chưa có implementation.
**Ngày:** 08/11/2026. **Nguồn:** [bản tổng hợp v1.4, mục 9.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [SPEC-003](../specs/003-desktop-shell.md), [SPEC-004](../specs/004-jobs-and-publish.md).

**Mở rộng Ubuntu 10/11/2026:** [ADR-012](ADR-012-ubuntu-desktop.md) đề xuất namespace owner theo UID, user manager/cgroup và `flock` với recovery workload thật. Phạm vi tài khoản Windows/primitive Windows bên dưới không tự áp dụng sang Linux; bất biến một owner/project/job nặng, khóa writer, attempt fencing và pin/lease tiếp tục tách biệt. Chưa nghiệm thu adapter Linux.

## Bối cảnh

Khóa một writer/project ngăn ghi DB trùng nhưng không ngăn hai project khác nhau cùng nạp Prithvi hoặc giữ GPU/RAM. Quy tắc một worker/GPU phải có chủ sở hữu liên process; giới hạn thread trong từng worker chưa đủ. Cần giới hạn có thể kiểm chứng cho bản đầu, chưa có yêu cầu xử lý đồng thời nhiều người dùng.

## Lựa chọn

Đề xuất một **execution owner** cho mỗi tài khoản Windows trên máy, có hiệu lực qua các session đăng nhập của cùng tài khoản và các bản cài GeoAI tuân thủ cùng protocol khóa. Một phiên chỉ có một project được quyền ghi/thực thi; trong phiên đó chỉ một job nặng chạy tại một thời điểm. Các project khác được mở xem kết quả đã công bố hoặc báo đang bận; không tự nhận queue ghi, import, tạo worker hoặc nạp model resident. Xem không ghi project và không tạo tác vụ nặng nền; nếu cần chuyển đổi/tile/report nặng thì yêu cầu owner hoặc từ chối rõ.

Job nặng gồm import/download/giải nén, preprocess/inference, solver, tạo metrics/report/tile dẫn xuất và công việc khác đã khai budget. Các phase của một job được dùng số thread/batch trong ResourceBudget, không đồng nghĩa một thread duy nhất. Viewer/HTTP read-only vẫn có cache RAM/buffer giới hạn; chưa hứa hai viewer trên hai phiên cùng đạt p95 đã đo cho một phiên.

Shell/API coordinator phải nhận khóa trước khi mở project writer, chạy migration hoặc tạo worker. Thứ tự nhận quyền: execution owner → khóa writer/project → transaction DB cấp attempt/token và dependency lease → cấp worker access context. Khóa owner là primitive hệ điều hành liên process; khóa project và attempt fencing tiếp tục độc lập. Thiết kế này mở rộng ADR-002/009, không thay thế chúng hoặc thay đổi yêu cầu Prithvi ở ADR-008.

## Phương án đã cân nhắc

| Phương án | Đánh đổi |
| --- | --- |
| Mỗi project tự lập lịch | Đơn giản trong project nhưng không giới hạn tổng RAM/VRAM giữa các instance; không đáp ứng ranh giới bản đầu |
| Một owner và một job nặng theo tài khoản | Giới hạn đồng thời rõ, không cần dịch vụ cài thêm; giảm throughput, phải xử lý khóa/crash liên session |
| Dịch vụ điều phối toàn máy hoặc broker đa project | Có thể chia quota giữa nhiều tài khoản/phiên; tăng lifecycle/auth/IPC và vận hành, chỉ mở khi có nhu cầu |

Không coi “mỗi app chỉ mở một project” là khóa liên process: hai app vẫn có thể tranh một GPU.

## Hệ quả

- SPEC-003 phải thử primitive khóa xuyên session trên Windows bằng tài khoản thường, ACL theo SID và namespace chung không phụ thuộc đường cài. Không dùng session-local mutex rồi tuyên bố đã chặn mọi instance cùng tài khoản. Chưa kiểm được phạm vi nào thì chặn cấu hình đó và ghi support matrix, không tự hạ policy.
- Metadata owner gồm owner ID/epoch mới mỗi lần cấp, PID kèm thời điểm tạo process, session ID, project ID và nhóm tiến trình được quản lý. Không chứa token API/credential; không coi PID hoặc file lock cũ đơn thuần là nguồn thẩm quyền.
- Mất heartbeat hoặc mutex abandoned chỉ kích hoạt recovery. Thu hồi attempt token, kiểm và dừng/đợi nhóm sidecar/worker cũ; chỉ cấp job mới khi xác nhận không còn workload cũ trong phạm vi quản lý. Chưa xác định được thì báo resource busy/recovery required, không đoán worker đã chết.
- Owner giữ quyền cho tới khi worker/model resident đã giải phóng và project writer đóng. Chuyển project phải dừng nhận việc, drain/cancel, giải phóng worker/handle/lease theo retention rồi mới cấp quyền project mới; checkpoint được giữ không có nghĩa worker còn giữ compute.
- Lease tài nguyên compute là trạng thái runtime thuộc owner; pin/dependency lease bền vững thuộc project/run/checkpoint. Nhả GPU không tự bỏ pin dữ liệu; GC chỉ chạy sau reconcile đúng inventory.
- Phạm vi hỗ trợ là GeoAI của cùng tài khoản trên máy. Tài khoản khác, bản GeoAI cũ không theo khóa hoặc ứng dụng ngoài GeoAI vẫn có thể chiếm tài nguyên; phải probe tài nguyên khả dụng và fail rõ. Chưa cam kết nhiều tài khoản cùng compute, không khóa toàn OS hoặc tuyên bố sandbox bảo mật.

## Bằng chứng và người chốt

Kỹ thuật backend/native chịu trách nhiệm khóa và recovery; QA kiểm process thật qua SPEC-003/004. Chủ dự án chốt phạm vi đồng thời sau khi có bằng chứng; chưa gán tên người hoặc cấu hình phần cứng giả.

Ca bắt buộc: hai project khởi động đồng thời, hai bản cài/cùng tài khoản, cùng tài khoản ở session khác, owner crash khi worker native còn sống, PID tái sử dụng, owner đóng bình thường, chuyển project có model resident, GPU hết tài nguyên do ứng dụng ngoài và dependency lease còn cần resume. Log phải chứng minh không có hai job nặng GeoAI đồng thời trong phạm vi hỗ trợ; pass schema không chứng minh điều này.

## Điều kiện xem lại

Khi có nhu cầu nhiều project/tài khoản chạy đồng thời, workload nhẹ bị chặn quá mức hoặc khóa xuyên session không đáp ứng trên môi trường mục tiêu. ADR này còn đề xuất nên được sửa có lịch sử; nếu được chấp thuận rồi thay đổi, lập ADR thay thế có liên kết và giữ bằng chứng cũ. Chưa xây service/broker đa người dùng trong đợt chỉ viết tài liệu.
