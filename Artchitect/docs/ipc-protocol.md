# Giao thức coordinator–worker, dự thảo 0.1.0

Đọc khi sửa worker/coordinator. Cơ sở: [job/IPC](../plans/08_job_tai_nguyen_va_phuc_hoi.md), [ADR-009](adr/ADR-009-ipc-attempts.md). Wire profile dự thảo đã có validator trong `backend/geoai/contracts/rpc.py` theo SPEC-001, với [bằng chứng metadata](evidence/codegen-2026-11-08/task-1-report.md). Transport, native stdout và scheduler còn thuộc SPEC-004; chưa có kiểm chứng runtime.

## Transport và framing

- JSON-RPC 2.0 qua stdin/stdout riêng mỗi worker. Một object JSON UTF-8 mỗi dòng, kết thúc đúng byte LF. Newline bên trong chuỗi phải escape; không pretty-print nhiều dòng.
- Giới hạn ban đầu 1.048.576 byte **gồm LF**. Đọc theo byte có giới hạn, xử lý partial read/EOF; dòng trống, UTF-8 sai, JSON lỗi, oversized hoặc dữ liệu native lạc vào là protocol error. Không chấp nhận JSON NaN/Infinity.
- Chưa hỗ trợ JSON-RPC batch. Request ID là string hoặc integer, không boolean/null; chỉ response lỗi parse/invalid request có thể id=null. Notification không có id.
- Một writer binary tuần tự hóa và flush; không để thread progress/heartbeat ghi xen. Coordinator đọc liên tục stdout/stderr với buffer giới hạn, tránh deadlock.
- Bootstrap trước GDAL/ORT/CUDA: flush, dup stdout cho protocol, dup2 stderr vào fd1; Windows kiểm CRT + SetStdHandle/handle cache. PYTHONUTF8 không thay binary mode. Launcher cấp pipe, CREATE_NO_WINDOW, nhóm Job Object; test native logging trên sidecar thật.

## Handshake, methods và events

Coordinator gọi `capabilities` trước `start`, gửi protocol/schema version. Worker chỉ nhận đúng version hỗ trợ; không tự bỏ trường/version lạ rồi chạy. Capability response phải ghi app/worker/runtime, feature và resume/cancel capability thực; chỉ model kỹ thuật không được công bố sẵn sàng nghiệp vụ.

| Method | Params | Hành vi |
| --- | --- | --- |
| capabilities | protocol_version/schema_version | Thương lượng version và capability; chưa nhận job |
| start | attempt key, job_spec_id, input_snapshot_id, access_context_id, access_context_sha256, resource_budget | Xác nhận accepted sau khi resolve/kiểm context/manifest/quyền/budget; kết quả sau bằng event |
| cancel | attempt key | Ghi nhận yêu cầu, dừng ở điểm an toàn; ack chưa là cancelled |
| shutdown | graceful boolean | Dừng nhận việc, hoàn tất/dừng theo policy; coordinator có deadline cấu hình |

Notification `heartbeat`, `progress`, `artifact_candidate`, `completed`, `error` có params chứa `attempt = {job_id, attempt_id, generation_token}`. Progress có phase và đơn vị công việc; total không biết thì không bịa phần trăm. Event error có structured error; artifact_candidate/completed chỉ mang ID/checksum/metadata, không tensor. Completed chưa tự đổi DB thành succeeded.

| Event | Payload dự thảo ngoài attempt | Ý nghĩa với coordinator |
| --- | --- | --- |
| heartbeat | Không cần tiến độ nghiệp vụ | Cập nhật liveness bằng thời gian monotonic phía nhận; không làm mới token đã thu hồi |
| progress | `phase`, `completed_units`, `total_units` khi biết | Integer không âm, completed ≤ total; UI có thể gộp, không dùng để quyết định publish |
| artifact_candidate | `candidate_manifest_id` | Candidate bất biến trong staging được cấp; cần resolve/kiểm bytes, chưa có publication |
| completed | `candidate_manifest_id` cuối | Worker xong tính/flush; coordinator còn bước validation và transaction publish |
| error | `error`: StructuredError | Ghi lỗi attempt còn hiệu lực, áp dụng retry policy của coordinator; không tự retry trong worker |

Các payload trên phải được định kiểu khi triển khai `rpc.py`; không thêm trường tùy ý mà bỏ qua version. Request `start` có thể accepted rồi thất bại ở event; response accepted không bảo đảm job thành công. Worker bận không nhận attempt thứ hai trên cùng slot; queue thuộc coordinator. Worker lỗi protocol bị cách ly/thu hồi attempt và dừng theo policy, không đọc tiếp chuỗi byte lệch framing như thể hợp lệ.

```json
{"jsonrpc":"2.0","id":"cap-1","method":"capabilities","params":{"protocol_version":"0.1.0","schema_version":"0.1.0"}}
```

```json
{"jsonrpc":"2.0","id":"start-1","method":"start","params":{"attempt":{"job_id":"job:1","attempt_id":"attempt:1","generation_token":"generation:1"},"job_spec_id":"job:1","input_snapshot_id":"snapshot:1","access_context_id":"access:1","access_context_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","resource_budget":{"cpu_threads":2,"ram_bytes":1073741824,"temporary_bytes":2147483648}}}
```

```json
{"jsonrpc":"2.0","id":"start-1","result":{"accepted":true}}
```

```json
{"jsonrpc":"2.0","method":"progress","params":{"attempt":{"job_id":"job:1","attempt_id":"attempt:1","generation_token":"generation:1"},"phase":"infer","completed_units":3,"total_units":10}}
```

```json
{"jsonrpc":"2.0","id":"start-2","error":{"code":-32001,"message":"Worker cannot execute this schema version","data":{"code":"unsupported_schema","message":"Unsupported schema version","retryable":false}}}
```

Request/response id chỉ correlate transport. Attempt key xác định lần thực thi và quyền công bố; không dùng request id hoặc idempotency key thay generation token. Trong version 0.1.0, start.job_spec_id phải khớp attempt.job_id vì JobSpec dùng job_id làm danh tính record.

Bổ sung wire draft sau review: access context được coordinator cấp và lưu trong registry tin cậy của worker theo [worker resolver](worker-resolver.md); `start` bắt buộc ID/hash context và kiểm khớp project/worker/owner epoch/attempt/job/snapshot/budget trước accepted. Bootstrap truyền registry qua handle riêng do launcher cấp; không nhận registry path từ params. Hash ví dụ là giả. RPC/fixture/exporter và typed context đã có ở SPEC-001; registry/runtime và toàn bộ kiểm đối chiếu start thực còn ở SPEC-009/004, không tuyên bố tương thích với client đã phát hành.

## State machine và publish

`queued → running → succeeded/failed`; `running → cancel_requested → cancelled` khi xác nhận dừng. Cancel queued có thể chuyển cancelled khi coordinator chứng minh chưa worker nào nhận; lỗi/race cụ thể kiểm trong task job. Retry tạo attempt/token mới, token cũ bị thu hồi. Một job đã succeeded không chuyển cancelled vì cancel muộn.

Worker không ghi SQLite. Publish phải kiểm candidate/bytes/hash/grid/coverage, token còn hiệu lực và chưa hủy; transaction kiểm lại token/state và uniqueness trước đăng ký. File rename và DB không là transaction chung: chỉ phục vụ artifact đã đăng ký, startup reconcile candidate/file mồ côi và metadata thiếu file.

Heartbeat/cancel reader còn hoạt động khi inference/solver đang chạy. Timeout request khác timeout job; mất heartbeat không chứng minh worker đã chết. Thu hồi token trước retry, chờ/terminate có giới hạn và chỉ resume checkpoint input/model/config khớp. Deadline/interval nằm trong cấu hình scheduler cần thử G1, không đặt ngưỡng thời gian nghiệp vụ từ fixture test.

Quyền tạo worker/job nặng tuân [ADR-011](adr/ADR-011-local-execution-owner.md). Execution owner lock không thay token attempt; token bị thu hồi cũng không chứng minh RAM/VRAM đã giải phóng. Context cũ không được replay sau retry/restart, kể cả content hash input giống nhau. Khi owner crash, chỉ cấp compute mới sau recovery xác nhận worker cũ đã dừng; lease/pin giữ byte cho checkpoint được xử lý riêng.

### Chuyển trạng thái và xử lý race

| Trạng thái / sự kiện | Quyết định bền vững của coordinator |
| --- | --- |
| queued → nhận việc | Transaction cấp attempt/token mới, lease và running; chỉ gửi start sau khi metadata đủ để recovery |
| queued → cancel | Chuyển cancelled chỉ khi chưa giao worker; thu hồi assignment nếu race với dispatch, không chỉ đổi UI |
| running → cancel | Ghi cancel_requested và chặn quyền publish trong transaction; gửi cancel cho đúng attempt |
| cancel_requested → dừng đã xác nhận | Thu hồi token, ghi cancelled, xử lý checkpoint/staging theo retention; ack cancel đơn thuần chưa đủ |
| running → completed | Kiểm candidate, chuẩn bị output bất biến rồi transaction recheck token/state/uniqueness; thành công mới là succeeded |
| running → error/crash | Thu hồi token, ghi attempt failed và reason; nếu còn retry hợp lệ thì queued với attempt mới, không dùng lại token |
| succeeded → cancel muộn | Giữ succeeded và publication; trả trạng thái hiện tại, không xóa kết quả |
| attempt cũ → heartbeat/progress/candidate | Không đổi state/progress/publication của attempt mới; ghi chẩn đoán đã lọc nếu cần |

Terminal của một attempt không đổi ngược. Retry có giới hạn/backoff đã cấu hình, cùng input/config đã khóa; cancelled chỉ chạy lại khi người dùng yêu cầu. Sửa input/tham số đổi ý nghĩa công việc tạo JobSpec/run mới. Idempotency scope theo project và nội dung request: cùng key/cùng payload trả cùng job, cùng key/khác payload là conflict; lưu digest/cách chuẩn hóa payload có version, không chỉ so key.

Cancel và publish được phân xử bằng commit có điều kiện: cancel_requested ghi trước thì publication bị từ chối; publish đã commit trước thì cancel muộn không đổi succeeded. Không có lời hứa “click hủy là chắc chắn chưa có kết quả” khi hai thao tác đang tranh chấp. Mất worker/heartbeat phải thu hồi quyền công bố trước khi cấp attempt mới, dù process cũ chưa được hệ điều hành xác nhận đã chết.

### Trình tự publish và recovery

1. Worker ghi vào staging gắn project/job/attempt, đóng/flush output rồi gửi candidate manifest ID. Resolver chỉ cấp đường trong workspace, không nhận path tuyệt đối do event tự khai.
2. Publisher resolve candidate, kiểm input/config/grid/reference/hash/coverage, model/readiness phù hợp loại job và token/state hiện tại. Technical job có thể publish artifact kỹ thuật nhưng không bật business capability.
3. Chuyển output hoàn chỉnh cùng volume tới tên bất biến duy nhất theo attempt/run, không ghi đè artifact của lần khác. Transaction repository kiểm lại active token/state và constraint một publication cho job trước khi đăng ký output và succeeded.
4. Commit thất bại do stale/cancel/conflict thì không phục vụ file vừa chuyển; giữ để reconcile/dọn sau khi kiểm ownership/lease. Trạng thái UI/API lấy từ DB, không từ tồn tại file hoặc event completed.
5. Startup giữ khóa writer, reconcile active attempt/lease và file/metadata trước nhận job/GC. File mồ côi không tự được promote; publication thiếu bytes/hash phải bị đánh dấu không khả dụng và ngăn phục vụ, không tái tạo giả rồi giữ nguyên hash.

Hash khớp không tự bảo đảm dữ liệu/không gian đúng; còn kiểm profile, GridSpec, mask, coverage và quan hệ JobSpec. Atomic rename cùng volume không tạo transaction file/DB hoặc cam kết chống mọi mất điện; độ bền filesystem/backup/restore phải được kiểm trong nền tảng và G3.

## Lỗi

JSON-RPC dùng -32700 parse error, -32600 invalid request, -32601 unknown method, -32602 invalid params, -32603 internal error. Domain error -32001…-32099 có `data.code`, message và retryable; worker không tự quyết retry vô hạn. Các code dùng chung ban đầu: unsupported_schema, invalid_input, missing_resource, stale_attempt, incompatible_model, resource_exhausted, cancelled, internal_error. Message/data không chứa secret hoặc signed URL.

Dispatch phân biệt parse/envelope/method/params trước khi gọi handler; method lạ trả -32601, không biến mọi ValidationError thành -32603. Unsupported protocol/schema version là lỗi thương lượng trước start, không hạ version âm thầm. Notification không nhận response; nếu notification lỗi cấu trúc, xử lý như lỗi protocol của worker. Timeout `start` không chứng minh start chưa được nhận: phải reconcile attempt đã lưu, không tạo job khác để thử mù.

## Kiểm chứng bắt buộc

SPEC-001 đã kiểm IDs, envelope result/error, required attempt/context key, progress bounds và method params; xem [report](evidence/codegen-2026-11-08/task-1-report.md). SPEC-004 phải có ca partial/oversized/UTF-8/NaN, log native, stderr đầy, timeout/pipe đóng, cancel khi infer, stale candidate và crash trước/sau rename/commit. Pass schema không chứng minh stdout/native handle hoặc fencing đã được triển khai.
