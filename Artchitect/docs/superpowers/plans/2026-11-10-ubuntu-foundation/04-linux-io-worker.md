# Linux Native IO and Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Worker thật đọc đúng snapshot, ghi đúng staging và Linux publisher có thể finalize bytes an toàn sau native stop.

**Architecture:** Factory đăng ký roots/permissions, Linux adapter giữ directory FD và dùng openat2. Input ổn định bằng private snapshots; artifact output dùng stop-then-copy và rename no-replace, transaction publication vẫn thuộc repository dùng chung.

**Tech Stack:** Python 3.12 os/fcntl/ctypes libc/openat2/renameat2/pidfd, unittest, existing JSON-lines RPC và GrantRegistry.

**Spec:** [SPEC-010](../../../specs/010-ubuntu-foundation.md), [adapter interfaces](../../../platforms/ubuntu/ubuntu-adapter-interfaces.md), [worker resolver](../../../worker-resolver.md), [security acceptance](../../../importer-resolver-security.md), [plan tổng](../2026-11-10-ubuntu-foundation.md), [catalog](interfaces-and-handoff.md).

## Global Constraints

G-01–G-16 áp dụng. openat2 BENEATH/NO_SYMLINKS/NO_MAGICLINKS/NO_XDEV; root FD không string prefix. Worker chỉ dependency đã cấp; packet ≤1_048_576bytes gồm LF, registry_delivery handle-snapshot. Không owner/writer/DB/publication writable FD tới worker; không EXDEV fallback; không dùng chmod thay byte ownership.

## Review Focus

RF-4 nằm D-04; D-01 kiểm FIFO/device trước read-open và mount; D-02 kiểm external source mutation/lease; D-03 kiểm destination collision/source identity/partial cleanup; D-05 kiểm import isolation và fixture không thành production job route. Test từng mục bên dưới.

---

### Task D-01: openat2/syscall layer và registered Linux roots

**Read:** native_io A-01, Windows name/path policy, security matrix IMP-01–06/09–11; không sửa taxonomy/GIS/model files.

**Files:** Create `backend/geoai/storage/linux_syscalls.py`, `backend/geoai/storage/linux_io.py`, `tests/storage/test_linux_io.py`.

**Interfaces:** open_beneath/rename_noreplace/identity và LinuxIOFactory/Root/Reader trong catalog. Task này thực hiện root/path/pinned metadata; reader streaming ở D-02, writes ở D-03. Chỉ publish methods đã có logic, không tạo method stub trả success.

- [ ] **Step 1: Test đỏ containment.** `test_registered_root_has_actual_device_inode`, `test_symlink_magic_link_parent_traversal_are_rejected`, `test_hardlink_alias_is_rejected`, `test_portable_names_share_existing_unicode_case_policy`, `test_fifo_and_device_are_rejected_without_blocking`, `test_ancestor_swap_does_not_escape_pinned_root`, `test_nested_mount_is_rejected`, `test_missing_openat2_fails_without_realpath_fallback`. Mỗi ca tạo sentinel ngoài root và kiểm hash giữ nguyên; test mount cần fixture mount thật/dedicated VM, thiếu quyền ghi skip đúng case, không skip toàn suite.

```python
self.assertEqual(root.identity.volume_id, f'linux-dev:{os.fstat(root_fd).st_dev}')
self.assertEqual(root.identity.file_id, f'linux-ino:{os.fstat(root_fd).st_ino}')
with self.assertRaises(StorageIOError):
    root.open_metadata('../outside/sentinel.bin')
self.assertEqual(hash_file(sentinel), expected_hash)
```

`open_metadata(relative_path: str) -> NativeIdentity` là private/test-visible helper của LinuxNativeRoot cho task này; không thêm method này vào wire hoặc quyền đọc dữ liệu cho worker. Tests không lấy fd từ public root API; root_fd chỉ test fixture pin riêng cùng directory để đối chiếu identity.
- [ ] **Step 2: Red.** `python -m unittest discover -s tests/storage -p test_linux_io.py -v`; missing syscall/adapter là đỏ khi Linux phù hợp, Windows skip native cases rõ.
- [ ] **Step 3: Implement syscall wrappers/probe.** Dùng ctypes libc `syscall` openat2 x86_64 number437, struct open_how với uint64 fields size24, errno được bắt và lọc. Check arch Linux x86_64 trước; ENOSYS/EPERM/unsupported flags → native_io_unavailable. renameat2 dùng libc ABI đã probe, RENAME_NOREPLACE; không fallback overwrite/path-prefix. LinuxIdentity từ fstat FD, decimal canonical không leading zero.
- [ ] **Step 4: Implement root registry/pinning.** Trusted root absolute path từ composition; walk/pin ancestors O_DIRECTORY/O_NOFOLLOW, xác minh permission/ownership, cho phép mount tại **root đã chọn** nhưng NO_XDEV cho mọi resolve bên dưới root. Relative path dùng policy thuần hiện có `storage.importer._name(value, 64)` như Windows _relative, max4096 ký tự, NFKC/case/portable reserved names; không import Windows adapter hoặc viết validator yếu riêng. Mở metadata O_PATH|O_CLOEXEC, fstat regular file và nlink==1 (directory không áp dụng nlink==1), không read-open FIFO/device trước validate. D-02 có thể reopen đúng O_PATH FD đã pin qua `/proc/self/fd/<owned-fd>` nội bộ, so fstat identity lại; đây là chuyển FD kernel đã kiểm, không nhận proc path từ caller và không fallback cho user magic-link bị chặn. FD phải còn owned/pinned, không lookup số FD đã close/reuse.
- [ ] **Step 5: Green/checkpoint D-01.** Native tests path/metadata + architecture, record syscall/FS/mount scope. Commit `feat(storage): resolve Linux registered roots by directory FD`; handoff root/metadata methods đã có, không claim open_read/create_file chưa triển khai.

### Task D-02: Stable managed/external readers và snapshot leases

**Files:** Modify linux_io.py, test_linux_io.py; Extend tests/storage/test_worker_io.py; shared io_resolver chỉ sửa nếu adapter contract cần integration đã nêu A-02.

**Interfaces:** LinuxNativeRoot.open_read theo native protocol; factory.open_external theo catalog. Private `reopen_verified_file(path_fd: int, *, flags: int) -> int` trong linux_syscalls.py nếu cần, chỉ caller có owned FD đã kiểm regular file. Snapshot entries giữ FD/hash/size/lease/refcount; NativeReader.identity là **copy thực**.

- [ ] **Step 1: Test đỏ snapshot semantics.** `test_external_registered_input_positive`, `test_source_mutation_during_copy_rejects_wrong_version`, `test_source_mutation_after_snapshot_does_not_change_reader`, `test_snapshot_reader_identity_is_copy_identity`, `test_snapshot_not_deleted_while_another_lease_holds_it`, `test_worker_cannot_open_ungranted_sidecar`.

```python
with resolver.open_read(context_id, attempt, ref_id) as reader:
    self.assertEqual(reader.read(), expected_bytes)
    self.assertNotEqual(reader.identity, original_source_identity)
    mutate_original_source()
    reader.seek(0)
    self.assertEqual(reader.read(), expected_bytes)
```

Helpers setup register real GrantRegistry/roots/external FileIdentity from pinned FD; mutation local test thread synchronized by events, không sleep để đoán race. Ca wrong registration identity/hash phải reject trước accepted read.
- [ ] **Step 2: Red.** Target Linux I/O suite và worker_io. Expected thiếu streaming/snapshot behavior; không sửa expected identity thành source để test xanh.
- [ ] **Step 3: Implement reader stability.** Open/path identity/regular/nlink check; expected bytes/hash/size một version; copy bounded vào snapshot private, rehash actual copy. Kiểm registration identity/source state trước/sau copy, mismatch expected version reject. Snapshot dir không writable FD tới worker; fchmod/read-only chỉ defense thêm, không proof. Managed data chỉ dùng trực tiếp nếu factory có byte ownership/stability thật; nếu chưa chứng minh, snapshot managed input theo cùng cơ chế, không hứa deny-write Linux.
- [ ] **Step 4: Lifetime/cancel/deadline.** Một absolute deadline xuyên open/hash/copy/rehash/read initial validation; checks trước/sau chunks, chunk bound1_048_576, size overflow/quota reject. Reader seek/read range và close idempotent; refcount giữ snapshot đến hết reader/run pins/leases; close root khi reader còn sống theo same lifetime contract Windows. Cache key gồm expected content identity/root registration, không path+mtime đơn thuần.
- [ ] **Step 5: Green/checkpoint D-02.** Linux positive/external mutation/sidecar/sentinel tests, Windows worker_io regression qua factory. Commit `feat(storage): provide stable Linux snapshot readers`; ghi snapshot disposition/cleanup không xóa data pin.

### Task D-03: Writes/delete/finalize cùng filesystem, không overwrite

**Files:** Modify linux_io.py/linux_syscalls.py/test_linux_io.py; Create `tests/integration/test_linux_publish.py` cho byte-finalize cases chưa cần repo integration E-01.

**Interfaces:** ensure_directory/create_file/delete_verified/move_verified theo native spec. move_verified chỉ byte/FS operation, không tự commit DB. Caller E-01 phải cung cấp native workload stop trước gọi; adapter không nhận boolean caller tự khai làm proof.

- [ ] **Step 1: Test đỏ writes/finalize.** `test_create_file_is_exclusive_bounded_and_fsynced`, `test_finalize_private_copy_changes_inode_and_preserves_expected_bytes`, `test_destination_collision_never_overwrites`, `test_exdev_is_rejected_without_copy_fallback`, `test_cancel_or_io_failure_cleans_only_created_temp`, `test_delete_captures_and_verifies_file_before_unlink`.

```python
self.assertEqual(hash_file(destination), expected_sha256)
self.assertNotEqual(source_identity, actual_identity(destination))
self.assertEqual(events, ['copy', 'verify_copy', 'fsync_file', 'rename_noreplace',
                          'fsync_destination_dir', 'unlink_verified_source', 'fsync_source_dir'])
```

Fault hooks trong test không thành production API. Collision/swap cases kiểm sentinel/collision file hash không đổi; candidate path còn writerFD sẽ được E-02 kiểm native refusal trước finalize.
- [ ] **Step 2: Red.** Target test_linux_io/test_linux_publish; record fail đúng thiếu no-replace/private copy/fsync, không chỉ mocked callback order.
- [ ] **Step 3: Implement creation/deletion.** Create pinned parent directories, no symlink, O_CREAT|O_EXCL, chunk/maxbytes/cancel/deadline kiểm xuyên vòng; fsync file/dir trước success. Delete chỉ file app quản lý đã cấp lease policy; pin parent và capture entry bằng rename no-replace vào private quarantine cùng FS, kiểm actual identity/hash/size rồi mới unlink. Nếu capture nhầm do race thì giữ/quarantine hoặc restore no-replace khi an toàn, không xóa file sai, không overwrite để rollback. Không recursive delete root/project/source external.
- [ ] **Step 4: Implement move_verified.** Kiểm source/dest cùng FS **trước copy**; source regular/nlink/identity/hash/size; tạo private publisher-owned temp trên FS đích, copy giới hạn, rehash, fsync, renameat2 NOREPLACE, fsync destination dir; unlink đúng source captured/verified rồi fsync source dir. Copy luôn là byte isolation trong same-FS, không EXDEV fallback. Đối chiếu deadline/cancel ở mọi phase; lỗi giữa nhiều files để orphan chưa published, không tự promote. Không chmod-only hoặc hardlink làm private output.
- [ ] **Step 5: Green/checkpoint D-03.** Native FS tests trên ext4, actual bytes/inodes và injected failure phases. Commit `feat(storage): finalize Linux artifacts with isolated durable bytes`; process kill tests chưa là power-loss proof, ghi phạm vi.

### Task D-04: Linux process/FD packet bootstrap và transport

**Read:** WorkerLaunchPacket fixture, jobs/protocol.py/transport.py, workers/bootstrap.py/main.py; B/C harness và owner handoff.

**Files:** Create `backend/geoai/jobs/linux_process.py`, `tests/integration/test_linux_worker_transport.py`; Modify workers/bootstrap.py, workers/main.py, transport.py chỉ logic factory-neutral, tests/jobs/test_process_factory.py và existing worker transport regressions.

**Interfaces:** LinuxProcessFactory/LinuxManagedProcess theo catalog; `read_launch_packet(handle: int, *, deadline_seconds: float=10) -> WorkerLaunchPacket` giữ một entrypoint, Windows handle conversion chỉ ở nhánh Windows, Linux nhận inherited read FD. Concrete ManagedProcess.launch environment/inherited_fds/owner phải verify containment từ lúc child exec; factory.launch_worker tính remaining từ caller deadline.

- [ ] **Step 1: Test đỏ packets/process.** `test_launch_packet_uses_only_allowlisted_pipe_fd`, `test_partial_bootstrap_failure_closes_only_owned_fds`, `test_packet_limit_includes_lf_and_rejects_trailing_json_nan`, `test_native_stdout_is_redirected_away_from_rpc`, `test_stderr_flood_remains_bounded`, `test_cancel_and_heartbeat_work_while_handler_busy`, `test_setsid_grandchild_blocks_group_stopped`. Assert packet.registry_delivery handle-snapshot, accepted/context/job/snapshot hashes đúng và mismatch reject.
- [ ] **Step 2: Red.** `python -m unittest discover -s tests/integration -p test_linux_worker_transport.py -v`; protocol pure suite chạy riêng để biết framing baseline không regress.
- [ ] **Step 3: Implement native launch.** API trong verified unit tạo anonymous pipe O_CLOEXEC; pass_fds allowlist chỉ bootstrap read FD, stdio riêng, executable/argv/worker path từ runtime registry. Packet encode trước spawn hoặc kiểm size trước write, không env/argv payload; nonsecret FD number qua argv được phép. Verify worker current cgroup/invocation ngay từ inherited topology và sau spawn, pin pidfd; không spawn ở ngoài rồi migrate cgroup. Đóng API read end ngay, writer có absolute deadline/partial write cancellation; cleanup đóng FD đúng một lần, không daemon thread treo giữ pipe.
- [ ] **Step 4: Implement child bootstrap/runtime.** Linux kiểm FD anonymous pipe, không stdio/file/socket tùy ý; poll/read bounded đến một packet+LF và EOF, strict JsonLines/schema/hash/nonce/context, không ghi log trước tách stdout. `_protocol_output()` POSIX giữ protocol fd, dup2 nativestdout→stderr trước heavy imports; stderr drain bounded. Worker factories chọn tại entrypoint; không import Windows từ shared modules. Shutdown worker không resident sau attempt; confirm workload sạch bằng census chỉ pinned API/supervisor, không chỉ waitpid/killpg.
- [ ] **Step 5: Green/checkpoint D-04.** New native suite + jobs/protocol + Windows transport/native process regressions. Assert owner/writer/DB/output FD absent trong `/proc/<worker>/fd`, process setsid không thoát cgroup. Commit `feat(linux): launch bounded workers through inherited FD snapshots`; giữ owner/attempt proof để E-01 consume.

### Task D-05: Composition chọn OS và integration resolver/extraction

**Files:** Modify root bootstrap.py, workers/main.py, extraction/GC callsites nếu còn concrete dependency; Extend tests/architecture/test_native_adapters.py, tests/storage/test_extraction.py, test_linux_io.py, test_linux_worker_transport.py. Tạo NativeRuntime dataclass tại root bootstrap, không kéo nó vào storage.

**Interfaces:** compose_native_runtime + NativeRuntime(io_factory,process_factory,owner) trong catalog. Root entrypoint biết OS và dựng factory; storage/jobs không import bootstrap. Worker composition từ trusted inherited packet roots, không nhận thêm public path registry.

- [ ] **Step 1: Test đỏ import/factory.** `test_shared_imports_never_load_concrete_os_adapter`, `test_linux_factory_requires_verified_native_bootstrap`, `test_unsupported_os_reports_capability_unavailable`, `test_extraction_linux_sentinel_and_quota_cancel`, `test_external_registration_remains_supported`. Windows path must return Windows factories without importing Linux user-bus package.

```python
self.assertIsInstance(runtime.io_factory, LinuxIOFactory)
self.assertIsInstance(runtime.process_factory, LinuxProcessFactory)
self.assertNotIn('geoai.storage.windows_io', fresh_process_modules)
```

isinstance ở test chọn concrete OS hợp lệ; shared production code không dùng nó làm authorization.
- [ ] **Step 2: Red.** Architecture + Linux worker/I/O targeted suites; existing extraction fixtures phải giữ expected quota/CRC/envelope behavior.
- [ ] **Step 3: Compose actual adapters.** LinuxInheritedProof → owner.from_inherited(epoch_reader=C-01), factoryroots/purposes và processfactory; Windows wrappers theo A. API native mode không tự mở arbitrary project từ webview; fixture driver E-01 sẽ claim test project qua cùng composition. Worker chỉ tạo permitted root registrations từ trusted launch packet đã validate; owner object không truyền worker.
- [ ] **Step 4: Verify importer/GC regression.** ZIP malicious names/symlink/mount/Unicode/case/CRC/expansion/cancel test sentinel ngoài staging giữ hash. Garbage collector chỉ app disposable có policy và repo pin/lease check sau native stop, không xóa managed input còn retained. NET fixture regression khi importer đổi, không claim live/provider pass.
- [ ] **Step 5: Green/checkpoint D-05.** Architecture/contracts/core/targeted storage/transport suites và exporters check; Windows native regression liên quan. Commit `feat(bootstrap): compose OS adapters without shared platform imports`; D complete chưa đóng010.3 cho tới E thật.
