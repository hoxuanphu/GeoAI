# Profile native Ubuntu cho SPEC-010

**Ngày:** 10/11/2026. **Trạng thái:** đặc tả kỹ thuật đề xuất, chưa triển khai. Đây là phần bắt buộc của [SPEC-010](../../specs/010-ubuntu-foundation.md), cụ thể hóa [ADR-012](../../adr/ADR-012-ubuntu-desktop.md). Các giá trị timeout/byte limit dưới đây là cấu hình kỹ thuật của foundation/fixture, không phải SLO hoặc budget nghiệp vụ G0.

## 1. Namespace và service

| Thành phần | Giá trị/quy định |
| --- | --- |
| Unit | `geoai-execution.service` trong user manager của UID; cùng tên cho mọi bản cài tuân protocol v1 |
| Runtime root | `/run/user/<uid>/geoai-execution-v1`, UID từ OS; directory `0700`, owner lock và socket private `0600` |
| Khóa owner | `owner.lock`, `flock(LOCK_EX|LOCK_NB)` trên FD `O_CLOEXEC`; không unlink/recreate inode trong lúc dùng |
| Socket shell | `control.sock`, pathname `AF_UNIX/SOCK_STREAM`; không abstract namespace, không path do project/UI chỉ định |
| State ledger | Home từ user database OS, nhánh `.local/state/geoai/execution-v1/ledger.json`; không dùng HOME/XDG do project hoặc từng session override để đổi namespace |
| Project writer | `.geoai-writer.lock` tại root project local đã được cấp; khóa theo directory identity `st_dev/st_ino`, không theo tên path hoặc project ID đơn lẻ |

Profile v1 yêu cầu runtime/state/project local và primitive đã probe; fixture chính ext4. Kiểm ancestor/ownership/mode trước tạo/mở; từ chối symlink, runtime root lạ, path tương đối hoặc namespace không thống nhất. Home network chưa có cấu hình state local tin cậy thì execution chưa được hỗ trợ; không tự chuyển ledger sang thư mục cache/session. Model/data/config thông thường vẫn theo XDG trong kiến trúc, ngoại lệ namespace này nhằm giữ khóa/epoch đồng nhất.

Shell dùng D-Bus user manager `StartTransientUnit` với mode `fail`, ExecStart absolute từ runtime manifest tin cậy; không qua shell command string. Properties v1: `Type=exec`, `KillMode=control-group`, `Restart=no`, `RemainAfterExit=no`, `TimeoutStopSec=5s`, `SendSIGKILL=yes`, `CollectMode=inactive-or-failed`, không Delegate/linger hoặc system service. Khi unit còn chạy/đang stop/không truy vấn được thì không tạo unit thay tên để vượt owner. Thất bại UnitExists/khóa bận là báo bận hoặc recovery; không stop owner khác đang hợp lệ. D-Bus ứng dụng chỉ create/query; không StopUnit/ResetFailed/replace theo tên để tránh race đổi invocation.

Chỉ caller đã tạo đúng unit invocation mới giữ quyền điều khiển phiên đó. Trusted Tauri wrapper tự lấy `creator_pid`, `creator_start_ticks` từ kernel và `creator_boot_id`, truyền bằng ba flag ExecStart native không chứa secret; webview không cung cấp các giá trị này. Supervisor kiểm actual peer PID/start time/boot ID trùng creator trước attach. Bản cài thứ hai không replace unit hay đổi executable dưới workload đang chạy. Root/supervisor không nhận arbitrary executable/project path/command từ webview; cấu hình test đi qua harness tách khỏi sản phẩm.

## 2. Handshake shell–supervisor

Supervisor Rust headless là main process. V1 yêu cầu pidfd cho creator/supervisor/API/worker identity cần signal; thiếu syscall/quyền thì native runtime chưa khả dụng. Shell đối chiếu `SO_PEERCRED` UID/PID với MainPID và InvocationID từ user manager trước và sau handshake, pin pidfd và đối chiếu start time/boot ID để tránh race pidfd_open/PID reuse. Supervisor kiểm peer kernel identity trùng creator của ExecStart. UID trùng hoặc echo challenge chỉ là một phần kiểm; không tự chứng minh đúng instance. Chỉ một owner connection được attach; cùng UID bị chiếm quyền không thuộc bảo đảm sandbox của profile.

Protocol control v1 là hằng byte native, **không thêm JSON DTO/public RPC**:

1. Chỉ sau khi xác minh đây là invocation shell vừa tạo, shell connect socket đã kiểm inode/owner. Supervisor gửi đúng 8 byte magic `GEOAIU1` + NUL, tiếp theo 32 byte challenge từ CSPRNG mới cho kết nối.
2. Shell đọc đủ 40 byte, kiểm magic rồi echo chính 40 byte. Supervisor so challenge constant-time, chỉ dùng một lần; sai/timeout/EOF/trailing byte thì đóng connection chưa attach. Chỉ thành công một lần trong invocation; không resume bằng challenge cũ.
3. Supervisor tạo API child sau handshake, trong cgroup từ lúc exec. Đọc đúng một dòng SessionDescriptor do API sinh trên stdout private và validate bằng schema hiện có; chuyển nguyên một dòng UTF-8 JSON + LF tới shell. Dòng tối đa **8192 byte gồm LF**; JSON không có field lạ/NaN, descriptor phải loopback/cổng hợp lệ và token phù hợp native validator.
4. API chỉ trả descriptor sau bind socket và Uvicorn startup. Shell vẫn kiểm `/v1/health`/capabilities có token. systemd unit active hoặc challenge thành công chưa là API ready.
5. Sau descriptor, shell giữ socket mở và không gửi dữ liệu nữa. Close/EOF hoặc byte ngoài protocol từ owner connection yêu cầu stop; supervisor không nhận command/FD mới hay attach lại vào runtime cũ. Connection thứ hai bị đóng, không làm mất owner hợp lệ.

V1 không dùng `SCM_RIGHTS` trên socket shell: các FD bootstrap được tạo bởi cha thực sự của API/worker nên dùng inheritance có allowlist. Mọi ancillary FD phải bị đóng và connection bị từ chối; dùng `recvmsg` để không bỏ sót control data. Socket shell/liveness tuyệt đối không được API/worker giữ bản sao làm trì hoãn EOF. UDS không thay HTTP API hoặc worker JSON-RPC.

Startup dùng **một deadline monotonic 30s** từ lúc bootstrap bắt đầu, gồm D-Bus/create/connect/challenge/API descriptor/health, không reset qua retry; challenge riêng không quá 5s và không vượt deadline tổng. Supervisor tự thoát nếu không có attach hợp lệ trong 30s. Khi cần cưỡng bức dừng, shell chỉ signal supervisor qua pidfd đã pin của phiên mình; pidfd đã exit/ESRCH không fallback sang PID hoặc StopUnit(name). Kiểm InvocationID rồi gọi StopUnit(name) vẫn có race và bị cấm trong implementation này.

Các native error trả về caller là mã đã lọc theo SPEC-010; connection lỗi đóng, supervisor báo reason qua đường chẩn đoán không chứa token/challenge/path. Không gửi stdout/stderr API như log ra journal/terminal vì descriptor chứa secret; supervisor consume pipe private, stderr được drain có giới hạn/redaction.

## 3. FD ownership và bootstrap con

| Kênh/FD | Ai giữ | Quy tắc |
| --- | --- | --- |
| Owner lock | Supervisor và một bản sao có chủ đích trong API | Cùng open file description/inode; API xác minh parent sống, unit/cgroup/invocation và lock trước dựng guard; worker không kế thừa |
| API stdin/stdout | Supervisor ↔ API | Anonymous pipe; stdin EOF yêu cầu shutdown; stdout chỉ một SessionDescriptor, không log native |
| API stderr | API → supervisor drain | Bounded buffer, không block descriptor/liveness; lọc secret; không merge stdout |
| Worker bootstrap read FD | API tạo, worker nhận một đầu đọc | `pass_fds`/allowlist; FD number có thể qua argv vì không phải secret/quyền tự thân, nội dung packet không qua argv/env |
| Worker RPC stdin/stdout và stderr | API ↔ worker | JSON-lines đúng IPC, stderr riêng; handle bootstrap không thay stdin/stdout protocol |
| Writer lock/root FD | API, chỉ read/staging FD thực sự cần mới tới worker | Không để worker nhận DB FD, owner FD, project writer lock hoặc publication writable FD |

API dùng `WorkerLaunchPacket` hiện có qua pipe, packet tổng sau encode phải nằm trong giới hạn framing **1,048,576 byte gồm LF**, không chỉ kiểm từng chuỗi con. `registry_delivery="handle-snapshot"` giữ giá trị draft vì descriptor OS ở đây cũng là inherited handle; không thêm enum `fd-snapshot`. Worker kiểm raw bytes/hash, worker/launch_nonce/owner/project/attempt và dependency như SPEC-009 trước accepted.

`close_fds`/CLOEXEC và allowlist áp dụng cả lỗi spawn/timeout/partial write. API kiểm parent pidfd/MainPID và cgroup trước cấp guard; metadata trong launch packet không tự cấp quyền native. Worker child/grandchild vẫn phải nằm trong unit cgroup; `setsid` không làm chúng hợp lệ ngoài lifecycle.

## 4. Owner epoch và project writer

SUP giữ kernel lock cho toàn phiên. API nhận FD native đã xác minh và là bên duy nhất cập nhật ledger/project writer dưới mutex nội bộ. Ledger là nhật ký generation, **không ghi đè chỉ giữ owner mới nhất**. Các private Pydantic model sau dự kiến tạo trong task code; phải có source/registry/fixture/exporter tests cùng SPEC-001 trước serialize, hiện schema chưa có:

| Model dự kiến | Fields và invariant |
| --- | --- |
| `LinuxOwnerLedger` | Private Contract có `schema_version="0.1.0"`, `created_at` UTC, `epoch_high_watermark: PositiveInt`, `generations: tuple[LinuxOwnerGeneration,...]` ít nhất 1 record; owner ID và epoch duy nhất; high watermark không nhỏ hơn bất kỳ record; giới hạn kỹ thuật foundation 1024 records/1,048,576 encoded bytes gồm LF |
| `LinuxOwnerGeneration` | `project_id`, `owner_id` là Identifier; `owner_epoch: PositiveInt`; `project_root_identity: FileIdentity`; `boot_id` UUID; `invocation_id` 32 hex lowercase; `supervisor_pid`, `supervisor_start_ticks` là PositiveInt; `cgroup_path` canonical absolute dưới user unit được OS xác minh; `cgroup_identity: FileIdentity` từ directory FD kernel; `state` active/closed chỉ để chẩn đoán |

Journal là provenance/counter, không là stop evidence hoặc nội dung project export. Hai model thuộc private registry dự kiến `PRIVATE_NATIVE_MODELS`, không thuộc CONTRACT_MODELS/WIRE_MODELS của record project/public RPC. V1 giữ records, không tự GC record generation, kể cả khi đổi project; đầy giới hạn thì chặn generation mới và báo resource_exhausted, không xóa record chưa reconcile. Sau này compact cần task/policy riêng có bằng chứng, không sửa budget nghiệp vụ bằng giới hạn fixture này.

Trước mỗi generation nhận project:

1. Giữ owner FD và nhận writer lock không blocking cho root project đã kiểm. API chưa cấp context/worker/attempt.
2. Đọc ledger và max owner epoch bền vững của project dưới writer lock, trước migration/claim: lấy max không-null trong Job, Attempt và DependencyLease của đúng project theo schema hiện có. Project mới/chưa có DB bắt đầu max bằng 0; DB có schema/version lạ không tự coi là mới. Helper SQLAlchemy đọc metadata phải theo schema/version có thật; không ghi DB trong bước quan sát này, không mở project người dùng khác làm chỗ thử.
3. Sinh owner ID mới bằng UUID hex, đặt epoch bằng `max(epoch_high_watermark, project_max_epoch)+1`; append record generation gắn project root và native invocation/cgroup hiện tại, giữ nguyên mọi record trước. Ghi ledger temp/flush/fsync/rename/fsync directory trước dựng WriterGuard và mọi ghi project. Ledger thiếu chỉ fresh khi đã quan sát project không có attempt/lease active cần evidence và không có workload cũ; ledger hỏng hoặc DB có generation active thiếu record thì recovery_required, không reset.
4. Migrate/reconcile qua guard. Context/attempt chỉ được cấp khi current owner/epoch, writer lock, parent/unit vẫn hợp lệ; nếu API hoặc supervisor chết, generation không được tái dùng. API chỉ close bản sao owner FD, không gọi `flock(LOCK_UN)` trên open file description đang được supervisor giữ; unlock sớm trên FD dùng chung sẽ phá khóa toàn phiên.

Project import từ máy/OS khác hoặc epoch cao hơn ledger phải đi cùng bước rebase; không đặt epoch lại 1 sau logout/reboot. Foundation chỉ nhận backup/bundle quiescent từ máy khác; không tự xác nhận dừng workload ở máy nguồn. Chuyển project phải drain/stop toàn workload, đóng repo/lease runtime và writer trước tạo generation mới. Không sửa snapshot/JobSpec để làm epoch phù hợp.

Nếu state mất/hỏng, project có owner cũ thiếu native provenance, hoặc DB schema chưa biết: chặn nhận việc. Recovery v1 là khôi phục journal tin cậy cùng project phù hợp, hoặc restore backup project quiescent đã kiểm inventory qua quy trình restore được hỗ trợ; không sửa bool active/token hay fabricate OwnerStopEvidence. Reboot giúp xác nhận process của boot cũ đã chết nhưng không tự khôi phục project/owner binding bị mất.

## 5. Dừng, crash và stop evidence

Normal close: shell đóng owner socket → supervisor đóng API stdin → API ngừng cấp việc, persist cancel/revoke khi còn ghi DB được, shutdown worker → xác nhận workload dừng → đóng repository/writer/FD → API thoát → supervisor thoát → user manager hoàn tất cleanup. Tổng budget cleanup kỹ thuật **10s**, grace tối đa 5s, phần còn lại dùng stop/quan sát; cưỡng bức dừng không tự tạo checkpoint.

Supervisor giám sát API exit và shell connection độc lập với compute; API chết thì đóng listener, ngừng attach và thoát để manager thu hồi toàn unit. Supervisor bị kill thì manager xử lý các process còn trong cgroup. Shell còn sống sau grace signal đúng supervisor pidfd, manager thu hồi nhóm của main process đó. Không dùng StopUnit theo tên, không kill PID suy từ metadata; identity không xác minh được thì báo recovery.

Trước publish hoặc cấp workload kế tiếp, native observer phải xác nhận **không còn workload con**, gồm grandchild đã reparent/setsid. Với foundation, census cgroup chỉ được còn supervisor và API đúng identity đã pin; PID lạ/không đọc được danh sách là chưa dừng. Worker parent exit/process group rỗng không đủ. Có thể signal process/group đã xác minh để hỗ trợ dừng; nếu không chứng minh sạch workload trong deadline thì stop toàn invocation, không coi là cancel thành công.

Trước owner mới, cần xác nhận unit cũ không chạy/đang stop và cgroup cũ thật sự rỗng/đã biến mất sau quan sát đúng invocation. Nhóm rỗng hoàn toàn chỉ sau API/supervisor exit. Process D-state hoặc manager lỗi giữ trạng thái recovery; owner FD lấy được hoặc heartbeat hết hạn không bỏ qua kiểm này.

Nếu API chết trước persist revoke, coordinator mới chỉ reconcile attempt/lease sau native stop evidence và epoch mới; xong transaction recovery mới nhận job. Với mỗi tuple DB cũ `(project_id, owner_id, owner_epoch)`, observer lấy record journal đúng project root/tuple để biết nguồn native, rồi kiểm trực tiếp OS:

- Boot ID đã đổi: process của boot cũ đã chết; record vẫn phải binding đúng tuple/root và được ghi từ composition tin cậy.
- Cùng boot/cùng invocation hiện tại: chỉ xác nhận generation cũ sau census không còn workload con ngoài đúng supervisor/API; không dựa state closed trong journal.
- Cùng boot/invocation cũ: supervisor PID+start time cũ đã exit; manager không còn chạy/stop invocation cũ; cgroup directory cũ đã biến mất hoặc identity kernel khác chứng minh nhóm cũ đã bị loại bỏ. Nếu cgroup identity còn mơ hồ/reuse hoặc có workload chưa biết thì chưa có proof, giữ recovery_required; có thể kiểm lại sau reboot với journal còn nguyên.

Evidence object được observer native tạo trong lần recovery hiện tại, gắn đúng tuple và kiểm lại khi `assert_stopped`; không deserialize bool từ journal làm quyền. Do records A vẫn còn khi append B, crash sau ghi B trước reconcile DB A hoặc đổi project không mất binding A. File staging/candidate không tự được phục vụ. Pin input/checkpoint vẫn theo retention; không GC theo timeout hoặc xóa mọi bytes để làm sạch trạng thái.

## 6. Nguồn và giới hạn

Đối chiếu upstream ngày 10/11/2026: [systemd v249 D-Bus API](https://github.com/systemd/systemd/blob/v249/man/org.freedesktop.systemd1.xml), [kill/control-group](https://github.com/systemd/systemd/blob/v249/man/systemd.kill.xml), [Unix sockets/peer credentials](https://man7.org/linux/man-pages/man7/unix.7.html). Đây là căn cứ thiết kế, không chứng minh implementation GeoAI đúng. Native profile có thể chạy fixture trước G0; các giá trị kỹ thuật không trở thành cam kết hiệu năng/sản phẩm.
