# Interface adapter OS cho SPEC-010

**Ngày:** 10/11/2026. **Trạng thái:** contract nội bộ dự kiến của [SPEC-010](../../specs/010-ubuntu-foundation.md), chưa là code đã tạo. Đọc cùng [native profile](ubuntu-native-profile.md), [architecture](../../architecture.md), [contracts](../../contracts.md) và [worker resolver](../../worker-resolver.md).

## 1. Composition và ranh giới

`bootstrap` và `workers` chọn factory OS từ runtime tin cậy; module storage/jobs nhận dependency đã dựng. Không thêm module nền import ngược bootstrap hoặc rải `os.name` trong policy/coordinator/publisher. `storage` không được import `jobs`; native I/O và owner nằm trong storage, process implementation nằm trong jobs, Rust/user manager thuộc native launcher. Chỉ entrypoint được biết cả hai factory để ghép.

Tách Protocol nội bộ và lỗi chung khỏi `windows_io`/`native_process`. Giữ class Windows làm adapter, không rename toàn bộ rồi mất regression. Loại `isinstance(..., WindowsNativeRoot)` khỏi đường shared; thay bằng factory/registry cấp root tin cậy và contract interface. Có đủ method/duck typing **không chứng minh quyền**: API client/worker không được tự đưa object/boolean vào native registry để thành guard.

## 2. I/O interface

Các signature dưới là shape triển khai cần có; tên tham số và semantics dùng nhất quán. `deadline` là deadline monotonic tuyệt đối nội bộ; wrapper hiện dùng `deadline_seconds` chuyển đổi một lần tại boundary, không reset qua từng bước. `cancelled` là callable không nhận đối số.

| Interface/method | Input/output và lifetime |
| --- | --- |
| `NativeIdentity(volume_id: str, file_id: str)` | Dataclass/value nội bộ không syscall; Windows giữ encoding hiện có; Linux dùng `linux-dev:<st_dev decimal>` và `linux-ino:<st_ino decimal>` không leading zero trừ số 0 |
| `NativeReader.identity`, `.size_bytes` | Identity trên FD actual mở và size bytes đã kiểm; không suy từ tên path |
| `NativeReader.read(size=-1) -> bytes`, `seek(offset) -> int`, `close() -> None` | Context manager; close idempotent; không đưa writable handle cho caller; seek chỉ vị trí hợp lệ |
| `NativeRoot.open_read(relative_path, *, sha256, size_bytes, expected_identity=None, cancelled, deadline) -> NativeReader` | Root do factory đăng ký; giữ directory FD/containment/bytes ổn định trong lifetime reader; đóng sau dùng |
| `NativeRoot.create_file(relative_path, chunks, *, max_bytes, cancelled, deadline, max_chunk_bytes=1048576) -> (size_bytes, sha256)` | File mới no-overwrite, đo bytes thực; flush/fsync trước success; rollback đúng file đã tạo khi lỗi, không xóa target suy từ path lạ |
| `NativeRoot.ensure_directory(relative_path) -> None` | Tạo/mở directory tương đối đã kiểm, không follow link; không cấp root khác |
| `NativeRoot.move_verified(relative_path, destination_root, destination_path, *, sha256, size_bytes, cancelled, deadline) -> None` | Publish cùng filesystem, no-replace, bytes được kiểm và loại writer cũ; Linux semantics ở mục 5, không là transaction DB |
| `NativeRoot.delete_verified(relative_path, *, sha256, size_bytes, cancelled, deadline) -> None`, `close()` | Xóa đúng file/identity đã kiểm theo lease/retention; close không xóa input hoặc publication |

Factory chuẩn: `open_registered_root(root_id, absolute_path, *, purpose)` với purpose read/staging/publication đã cấp bởi composition root; root ID → object nằm trong registry native riêng, không lấy registration/path chỉ từ start payload. `purpose` là quyền ứng dụng nội bộ, không là field mới của wire. Root/staging hợp lệ vẫn phải binding project/attempt ở GrantRegistry.

Linux `openat2` dùng `RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS|RESOLVE_NO_MAGICLINKS|RESOLVE_NO_XDEV`; root FD đã mở/pin từ đường tin cậy. Chỉ regular file, policy tên portable, kiểm `fstat`, mode, identity và nlink thích hợp. ENOSYS/EPERM/flag thiếu/FS chưa hỗ trợ → native_io_unavailable, không fallback so prefix/realpath. Root có thể ở mount riêng; cấm vượt mount trong root, không giả prefix đồng nghĩa cùng filesystem.

`linux-dev/linux-ino` là encoding adapter của hai chuỗi FileIdentity hiện có, không là field/schema mới. Inode tái sử dụng hoặc size/mtime khớp chưa chứng minh bytes; bắt buộc hash và provenance/registration. Format này chỉ dùng đúng host/registration, không portable identity sau restore hoặc thay OS.

## 3. Owner và process interface

Tái sử dụng `storage/guards.py`: WriterGuard, GuardLease và OwnerStopEvidence. Không tạo public DTO đóng vai trò guard. Guard API giữ native FD và parent/unit proof theo profile; worker không được nhận owner/project writer FD.

| Interface/method | Semantics |
| --- | --- |
| `ExecutionOwner.acquire() -> ExecutionOwner` | Chỉ từ API được supervisor khởi động; xác minh owner FD/cgroup/parent/invocation trước dựng native object; factory Windows giữ acquire hiện có |
| `.acquire_project(project_id, project_root) -> WriterGuard` | Khóa theo root identity; chặn project thứ hai; hoàn thiện owner ID/epoch theo ledger/project rồi mới trả guard; không nạp worker trước bước này |
| `.owner_id`, `.owner_epoch` | Chỉ đọc sau generation project đã hoàn thiện; trước đó báo project_not_claimed, không phát epoch 0 ra context |
| `.assert_held(project_id)`, `.retain(project_id) -> GuardLease` | Guard kiểm FD/unit/parent/project binding thực; retain giữ lifetime, close chờ/không phá lease đang dùng theo contract hiện có |
| `.recovery_evidence() -> OwnerStopEvidence` | Native observer binding journal generation đúng project root/owner/epoch, kiểm OS hiện tại theo native profile rồi tạo proof; `assert_stopped(project_id, owner_id, owner_epoch)` kiểm lại, không nhận bool do caller khai. Thiếu record/nhóm chưa rõ phải fail closed |
| `.close()` | Từ chối nhả quyền khi workload/retained guard chưa sạch; không unlink kernel lock đang dùng |
| `ManagedProcess.launch(executable, argv, *, environment, inherited_fds, owner) -> ManagedProcess` | Executable/args từ registry runtime tin cậy; tạo child trong unit hiện có, pass FD allowlist, không shell=True; constructor kiểm containment |
| `.stdin`, `.stdout`, `.stderr`, `.pid`, `.wait(deadline)` | Pipe tách biệt; exit code chỉ chứng minh process cha đã exit |
| `.start_stderr_drain(max_count)`, `.terminate_group(deadline)`, `.group_stopped(deadline)` | Bounded drain; signal chỉ nhóm/process đã xác minh; group_stopped trên Linux đòi census workload cgroup theo profile, không chỉ killpg/PID wait |
| `.close()` | Idempotent sau dọn/đóng FD; không tự báo stopped khi không có native evidence |

`NativeIdentity`, `StorageIOError`, OwnershipError và NativeProcessError ở package nền chung; adapter chuyển errno/Win32 error sang mã nội bộ đã lọc. Không để repository phụ thuộc process factory; composition đưa OwnerStopEvidence vào repository recovery như interface hiện có.

## 4. Input ổn định và external input hợp lệ

Linux không có cơ chế deny-write/delete sharing giống Windows. Trước grant, importer/coordinator materialize remote hoặc external input đã đăng ký vào managed snapshot riêng, đọc nguồn bằng FD đã kiểm, kiểm registration identity trước/sau copy và SHA-256/size của bản copy đúng expected version. File đổi làm bytes/hash không còn đúng thì từ chối; không update snapshot âm thầm.

Path external/read entry đã có trong draft vẫn hợp lệ về metadata. Nếu WorkerIOResolver nhận external-registered-local ở Linux, native factory tạo snapshot read-only có giới hạn từ đúng registration và trả reader trên copy, sau khi kiểm identity/hash nguồn; reader.identity phản ánh FD copy thực, không giả identity của nguồn. Ưu tiên materialize trước dispatch để grant dùng managed-local, giữ ref ID và provenance nguồn. Worker chỉ dùng dependency được cấp, không tìm thêm sidecar hoặc mở mọi file cùng thư mục.

Root snapshot không cấp writable FD cho worker; mode/chmod không thay proof bytes. Cache/snapshot copy sống theo lease của reader/run; close một reader không xóa bản còn pin/lease. Các ca dương external và source thay bytes ở UB-10/IMP-07/08 là bắt buộc; không cấm toàn bộ external input để tránh kiểm race.

## 5. Publish Linux

Foundation dùng worker kết thúc theo attempt. Sau candidate/completed, coordinator đợi workload dừng bằng native observer; `completed` hoặc pipe EOF đơn lẻ chưa cho phép finalize. Linux publisher chỉ tiếp tục khi census còn đúng supervisor/API; nếu không chứng minh được thì giữ candidate chưa công bố và đi cleanup/recovery.

Linux `move_verified` kiểm source bằng directory FD, identity/hash/size và regular-file/no-link policy, rồi copy có giới hạn vào file private do publisher tạo trên filesystem đích. Copy này là bước cố định bytes/loại writable FD cũ, không phải fallback cross-volume: phải kiểm cùng filesystem trước, EXDEV bị từ chối. Rehash bản copy, fsync file, renameat2 `RENAME_NOREPLACE`, fsync directory đích; chỉ sau thành công mới unlink đúng source đã kiểm và fsync directory nguồn. Thiếu rename no-replace/durability primitive thì fail rõ; không overwrite publication.

`create_file` cho manifest cũng fsync file/directory. Worker không có publication FD; API giữ output roots và verified readers đến commit. Hash/readonly FD không thay ownership nếu còn writer khác; v1 đòi stop workload + copy private, không dùng chmod làm bằng chứng thu hồi FD. Giới hạn chống cùng UID bị chiếm quyền vẫn như architecture.

Nhiều artifact có thể để lại file mồ côi nếu lỗi giữa các rename; API chỉ phục vụ publication DB đã commit. Repository transaction kiểm active AttemptKey/owner/state/cancel/uniqueness lần cuối; cancel muộn sau rename làm commit từ chối, orphan được reconcile trước GC. Backup/restore và crash fault injection phải dùng SQLite/file thật; process kill không chứng minh durability mất điện.

## 6. Schema và compatibility

Trong đợt spec không thay Pydantic hoặc schema/client. Khi triển khai ledger dự kiến, thêm private model vào registry theo SPEC-001 và đồng bộ fixture/exporter/tests trước khi writer dùng. WorkerBootstrap/LaunchPacket/SessionDescriptor giữ source Pydantic hiện có; mọi nhu cầu đổi chúng phải được review trong task contracts cùng code, không nối thêm field JSON tự do.

Windows adapter giữ nguyên semantics deny-write sharing/handle list; regression phải kiểm trên Windows thực cho đường native đã chạm tới. Linux không import windows_io/windows_owner từ shared modules, Windows không bị ép cài user manager/DBus hay package Linux. Không hạ assertion, bỏ test hoặc hardcode skip để tổng suite xanh.
