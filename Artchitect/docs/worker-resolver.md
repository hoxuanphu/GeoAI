# Worker resolver và cấp quyền đọc/ghi, dự thảo 0.1.0

**Trạng thái:** đã có typed context/bootstrap/read entries và schema sinh từ Pydantic trong [SPEC-001](specs/001-contracts-baseline.md), [bằng chứng](evidence/codegen-2026-11-08/task-1-report.md). Chưa có registry/bootstrap/native resolver thực thi; [SPEC-009](specs/009-importer-worker-resolver.md) tiếp tục I/O và tích hợp SPEC-004.

Mục tiêu là worker nhận ID từ `start` có thể đọc đúng input/model/manifest và ghi đúng staging, không dùng SQLite session, path từ UI hoặc provider URL như quyền truy cập. [ADR-011](adr/ADR-011-local-execution-owner.md) giới hạn phiên thực thi; [IPC](ipc-protocol.md) giữ fencing/cancel/publish.

## Phương án bản đầu và bootstrap

1. Execution owner/coordinator nhận khóa writer/project, resolve input remote qua catalog rồi materialize phần dữ liệu đủ preprocessing/context vào local cache được lease. Provider credential/signed URL chỉ ở catalog/session; worker bản đầu không nhận credential, không tự HTTP download hoặc tìm lại scene. File local ngoài project có thể được đăng ký read-only; SMB/network input phải staging local trước khi cấp cho worker ở profile này.
2. Launcher tạo worker thuộc Job Object và namespace context/staging riêng, không lấy root từ request UI. Truyền bootstrap descriptor qua handle đọc được kế thừa có chủ đích, không qua URL/command-line chứa secret; chỉ kế thừa các handle đã liệt kê. Descriptor có worker ID, launch nonce, protocol/schema versions và đường nội bộ tới context registry do coordinator quản lý. Không truyền environment chứa credential; allowlist env/DLL/data path từ runtime pack đã khóa.
3. Coordinator ghi access context bất biến cho mỗi attempt vào registry riêng của worker: ghi tạm/flush rồi rename, tính SHA-256 của chính bytes được truyền. Gửi `start` có `access_context_id`, `access_context_sha256` cùng attempt/job/snapshot/budget. ID chỉ được tra trong registry tin cậy, không nối path tùy ý hoặc đọc context của worker/project khác.
4. Worker kiểm worker/launch identity, hash/context/schema, đủ AttemptKey và execution owner epoch, job/snapshot hashes, reference list và budget trước trả accepted. Đọc manifest qua allowlist trong context; dữ liệu lớn vẫn đọc theo window, không qua JSON. `capabilities` chưa cấp quyền đọc input hoặc khởi tạo model nặng trước khi owner cho phép.
5. Resolver trả input handle/read descriptor và staging descriptor trong nội bộ worker. Candidate event chỉ chứa ID; coordinator đối chiếu candidate ID với registry theo project/attempt rồi kiểm file thực trước publish. Worker resident chỉ tái sử dụng cho cùng project; xong attempt đóng input handles/caches không còn lease và nhận context mới cho attempt tiếp, không giữ allowlist cũ như quyền cho job sau.

Descriptor và context là trạng thái runtime tạm, không là manifest project được export. Không log/dump đường dẫn cá nhân/launch metadata hoặc tái dùng context từ project package. Các đường nội bộ trong context không mở thành field cho API client nhập. Quy tắc fields ở dưới được định kiểu trong `contracts/access.py` và giữ trạng thái draft; Pydantic chưa thay native enforcement.

## Access context dự kiến

| Nhóm trường | Quy tắc |
| --- | --- |
| `schema_version`, `created_at`, `access_context_id` | Draft 0.1.0, UTC; ID duy nhất trong registry worker và không dùng lại cho attempt khác |
| `project_id`, `worker_id`, `launch_nonce`, `execution_owner_id`, `owner_epoch`, `attempt` | Gắn đúng project/worker/owner đang giữ quyền, đủ job/attempt/generation token; epoch không thay attempt fencing |
| `job_spec_id`, `job_spec_sha256`, `input_snapshot_id`, `input_snapshot_sha256` | Khóa bytes manifest và danh tính; start/job/context phải cùng tham chiếu, không lấy latest |
| `read_entries` | Mỗi ref ID có kind manifest/input/model/checkpoint/profile, content hash, size bytes, location được đăng ký và permission read-only. Ref ID duy nhất; dependency closure đủ cho job và model/runtime được cấp |
| `staging_id`, `resource_budget` | Một vùng ghi riêng cho attempt; budget khớp JobSpec/start. Worker không được ghi context registry, input, model pack, DB hay publication root |

`location` chỉ thuộc context private: managed-local hoặc external-registered-local. External entry phải có đăng ký/cấp quyền rõ với file identity/content hash; không cấp quyền toàn bộ thư mục cha chỉ để đọc một file. Manifest/sidecar files như band/QA/mask/model config phải được liệt kê; asset ID không tự cấp quyền cho mọi dependency mà driver GIS có thể mở.

### Trường draft cụ thể trong Pydantic SPEC-001

`contracts/access.py` định kiểu metadata private: `WorkerReadEntry` gồm `ref_id`, `kind`, `sha256`, `size_bytes`, `permission="read_only"`, `location`. `location.kind="managed-local"` có `root_id`, `relative_path`; `location.kind="external-registered-local"` có `registration_id`, `absolute_path`, `file_identity={volume_id,file_id}`. Hai giá trị file identity là chuỗi không rỗng do adapter native cấp, không suy từ tên file. `owner_epoch` là integer dương; `read_entries` có ref duy nhất và phải liệt kê manifest job/snapshot với hash khớp các trường context. Dependency closure model/input/profile còn do resolver kiểm với nội dung JobSpec/ModelSpec thực.

`WorkerBootstrap` private có `schema_version`, `protocol_version`, `worker_id`, `launch_nonce`, `context_registry_path`; truyền qua handle riêng của launcher. Bootstrap không là record bền vững; WorkerAccessContext có version/UTC để kiểm metadata nhưng vẫn là grant runtime tạm. Registry `PRIVATE_CONTEXT_MODELS` tách khỏi record project `CONTRACT_MODELS` và wire `WIRE_MODELS`; schema sinh chung chỉ phục vụ kiểm kiểu. Path private là chuỗi metadata, chưa có bảo đảm canonicalization, confinement, file identity, hash bytes, quyền hoặc fencing từ việc pass Pydantic. Public RPC start chỉ nhận ID/hash context, không nhận location hoặc registry path. Các tên trường này là draft chưa phát hành; native I/O/bootstrap/resolver vẫn thuộc SPEC-009.

Hash input xác minh theo file bytes đã cố định và provenance; với file lớn, coordinator có thể materialize immutable managed copy để tránh đọc lại hash từng window. Nếu giữ external mutable file thì phải mở đúng file identity, xác minh nội dung ổn định trong lúc dùng hoặc chuyển sang managed copy; thiếu bảo đảm thì chặn, không chỉ kiểm mtime/size rồi gọi là immutable. Input bị thay đổi tạo version mới; retry không đổi snapshot để chạy tiếp.

## Quyền và đường dẫn

| Đối tượng | Cho phép | Từ chối |
| --- | --- | --- |
| Manifest/input/model trong read_entries | Mở read-only đúng file/version/hash/identity; managed path dưới root đã cấp | Ref lạ, path/URL từ params, model khác hash, ancestor bị reparse ngoài policy |
| External registered input | Đọc file cụ thể người dùng đã chọn/đăng ký; pin offline chỉ khi đủ bytes được giữ | Tự đọc file lân cận/ổ đĩa khác hoặc cho rằng ở ngoài project là tự được phép |
| Staging của attempt | Tạo file với tên tương đối đã kiểm, ghi/flush/đóng rồi đăng ký candidate | Absolute/UNC/device/ADS path, traversal, ghi root khác, hardlink/reparse đổi đích, overwrite publication |
| Candidate từ worker | ID được coordinator cấp/đăng ký trong staging hiện tại; hash/size/profile/project/attempt khớp | Candidate của project/attempt khác, token thu hồi, file chưa hoàn chỉnh hoặc đổi bytes sau thông báo |
| Dữ liệu remote/VRT phụ thuộc | Catalog materialize trước; dependency local được kiểm và liệt kê | Worker tự follow HTTP/VSI URL/VRT nguồn ngoài allowlist hoặc dynamic code/pixel function |

Canonicalize và so prefix chuỗi chưa đủ trên Windows. Adapter cần policy path theo volume/case/file identity, kiểm ancestor/reparse và handle thực sau open, bảo vệ race đổi symlink/junction giữa check và use. Vùng staging không được cho worker khác ghi. Các phép kiểm và giới hạn cụ thể ở [ma trận bảo mật](importer-resolver-security.md).

## Thu hồi, retry và lỗi

Coordinator thu hồi quyền start/publish khi cancel/retry/owner mất hiệu lực; không gửi thêm grant. Context mới có ID/attempt/token mới; worker cũ không được publish bằng context của lần mới. File context tĩnh không thể tự thu hồi handle read đang mở: dừng worker/đóng handle và reconcile được yêu cầu trước cấp tài nguyên lại; không tuyên bố capability file là sandbox chống tiến trình cùng tài khoản bị chiếm quyền.

RPC vẫn dùng StructuredError hiện dự thảo: schema không hỗ trợ → unsupported_schema; ref/path/context mismatch → invalid_input hoặc stale_attempt theo nguyên nhân; bytes/version không còn → missing_resource; model/profile sai → incompatible_model; vượt quota → resource_exhausted. Chi tiết audit được lọc, không gửi raw path/URL/credential; permission violation không retry tự động. Mất nguồn remote được catalog xử lý theo identity, không để worker thay input.

## Ranh giới task và kiểm chứng

SPEC-001 chịu trách nhiệm kiểu và version, đã kiểm metadata/round-trip/manifest binding; SPEC-009 chịu bootstrap/context/path/import/catalog policy; SPEC-004 tích hợp start/recovery/publish/lease; SPEC-005/008 cung cấp dependency/model inventory đúng profile. SPEC-009 có thể dùng worker fixture và dữ liệu tổng hợp trước G0, không cần weights thật. Ca chấp nhận runtime gồm context/hash/version/worker/project/attempt sai, context cũ replay, input ngoại project hợp lệ, đổi file sau grant, staging escape, redirect/VRT và candidate cross-project/cross-attempt; các ca native/process này chưa chạy.
