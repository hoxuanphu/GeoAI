# Catalog interface và gói bàn giao cho AI

Đọc cùng [plan tổng](../2026-11-10-ubuntu-foundation.md) và [interface spec](../../../platforms/ubuntu/ubuntu-adapter-interfaces.md). Mọi tên dưới là quyết định triển khai **dự kiến**, chưa là API đã tồn tại. Types/adapter không cấp quyền chỉ vì thỏa duck typing.

## 1. Types và owner của interface

| Nguồn/tạo ở task | Signature hoặc shape chính xác | Consumer |
| --- | --- | --- |
| A-01 `storage/native_io.py` | `NativeIdentity(volume_id: str, file_id: str)` frozen dataclass; `StorageIOError(ValueError)` chỉ chứa reason code (giữ base của Windows hiện có theo ruling A-01) | Windows/Linux I/O, resolver |
| A-01 cùng file | `NativeReader` và `NativeRoot` Protocol có đúng properties/methods ở interface spec; native method nhận `deadline: float` tuyệt đối, `cancelled: Callable[[], bool]`; `open_read`, create/move/delete không reset deadline | A-02, D |
| A-01 cùng file | `NativeIOFactory.open_registered_root(root_id: str, absolute_path: Path, *, purpose: Literal['read','staging','publication']) -> NativeRoot`; `require_root(root: NativeRoot, *, purpose: str) -> None`; `open_external(registration: ExternalRegistration, *, sha256: str, size_bytes: int, cancelled, deadline: float) -> NativeReader` | Trusted composition, shared resolver/publisher |
| A-01 cùng file | `ExternalRegistration(path: Path, identity: NativeIdentity)` chuyển từ io_resolver; io_resolver re-export tên cũ để caller hiện tại không mất import; factory giữ strong references tới roots đã tạo và purpose | A-02, worker entry |
| A-03 `storage/native_owner.py` | `OwnershipError(RuntimeError)`; `ExecutionOwner` Protocol: `owner_id`, `owner_epoch`, `acquire_project(project_id: str, project_root: Path) -> WriterGuard`, `recovery_evidence() -> OwnerStopEvidence`, `close() -> None`; guards import từ guards.py | Composition, process factory |
| A-03 `jobs/process.py` | `NativeProcessError(RuntimeError)`; `WorkloadStopEvidence.assert_stopped(project_id: str, attempt: AttemptKey) -> None` Protocol | E-01 publisher; khác OwnerStopEvidence recovery |
| A-03 cùng file | `ManagedProcess` Protocol: pipes stdin/stdout/stderr, pid, stderr_bytes_seen; `wait(deadline: float) -> bool`, `start_stderr_drain(max_count: int=65536) -> None`, `terminate_group(deadline: float) -> bool`, `group_stopped(deadline: float) -> bool`, `close() -> None` | WorkerTransport |
| A-03 cùng file | `ProcessFactory.launch_worker(executable: Path, packet: WorkerLaunchPacket, *, owner: ExecutionOwner, deadline: float) -> ManagedProcess`; `stop_evidence(process: ManagedProcess, *, project_id: str, attempt: AttemptKey) -> WorkloadStopEvidence` | Transport, E-01 |
| B-01 `session.rs` | `SessionDescriptor { base_url: String, token: String }`, `validate(&self) -> Result<(), &'static str>` giữ validator hiện có, không Debug secret | Main/Windows/Linux/supervisor |
| B-01 `linux_runtime/runtime.rs` | `RuntimePaths { supervisor: PathBuf, python: PathBuf, backend: Option<PathBuf> }`; `resolve_runtime(resource_root: &Path, dev: Option<DevRuntimePaths>) -> Result<RuntimePaths, NativeError>`; `DevRuntimePaths { supervisor: PathBuf, python: PathBuf, backend: PathBuf }` chỉ native build/test config | B-02/B-07 |
| B-02 `linux_runtime/identity.rs` | `ProcessIdentity { pid: u32, start_ticks: u64, boot_id: String }`; `PinnedProcess` giữ OwnedFd pidfd và identity; `pin(pid: u32) -> Result<PinnedProcess, NativeError>`, `signal(&self, signal: i32) -> Result<(), NativeError>`, `exited(&self) -> Result<bool, NativeError>` | Manager/control/cleanup |
| B-02 `linux_runtime/manager.rs` | `UnitIdentity { main: ProcessIdentity, invocation_id: String, cgroup_path: PathBuf, cgroup_identity: (u64,u64) }`; `UserManager::connect(deadline: Instant)`, `start(&self, paths: &RuntimePaths, creator: &ProcessIdentity, deadline: Instant) -> Result<UnitIdentity, NativeError>`, `query(&self, deadline: Instant) -> Result<UnitIdentity, NativeError>` | Shell core; không stop(name) method |
| B-03 `linux_runtime/control.rs` | `connect_owner(unit: &UnitIdentity, deadline: Instant) -> Result<OwnerConnection, NativeError>`; `OwnerConnection` giữ stream và supervisor PinnedProcess; `read_descriptor(&mut self, deadline: Instant) -> Result<SessionDescriptor, NativeError>`, `close(&mut self)` | B-04/B-07 |
| B-04 `linux_runtime/supervisor.rs` | `run_supervisor(paths: RuntimePaths, creator: ProcessIdentity) -> Result<(), NativeError>`; giữ owner FD/listener/creator pidfd, child API và event loop | Thin binary entry |
| B-05 `storage/linux_bootstrap.py` | `LinuxOwnerBootstrap` nội bộ giữ owner FD đã pin, parent pidfd/identity, invocation/cgroup/root identities; `validate_inherited_owner(owner_fd: int, supervisor_pid: int) -> LinuxOwnerBootstrap`; `close()` không LOCK_UN | C-02 owner, root bootstrap |
| B-06 `tests/support/linux_runtime.py` | `LinuxRuntimeHarness` context manager: `.descriptor` (secret, không log), `.api_pid`, `.invocation_id`, `.cgroup_path`, `.close_shell()`, `.kill_component(name: str)`, `.assert_workload_empty()`, `.assert_unit_gone()`; constructor probe/skip rõ | Linux integration suites |
| C-01 `storage/project_epochs.py` | `PriorOwner(owner_id: str, owner_epoch: int, needs_stop_evidence: bool)` frozen dataclass; `ProjectEpochState(max_epoch: int, prior_owners: tuple[PriorOwner,...])`; `read_project_epochs(project_root: Path, project_id: str) -> ProjectEpochState` read-only | Linux owner acquire_project |
| C-02 `storage/linux_owner.py` | `LinuxOwnerSession.from_inherited(bootstrap: LinuxOwnerBootstrap)`; `.lock_project(project_id: str, project_root: Path) -> LinuxProjectLock`; lock có `.assert_held()`, `.retain()`, `.close()`, chưa là WriterGuard | C-03 |
| C-03 cùng file | `LinuxExecutionOwner.from_inherited(bootstrap: LinuxOwnerBootstrap, *, epoch_reader: Callable[[Path,str],ProjectEpochState]) -> LinuxExecutionOwner`; instance thực hiện ExecutionOwner Protocol; owner properties lỗi project_not_claimed trước claim | Root composition |
| D-01 `storage/linux_syscalls.py` | `open_beneath(dir_fd: int, relative_path: str, *, flags: int, mode: int=0) -> int`; `rename_noreplace(source_dir_fd: int, source_name: str, destination_dir_fd: int, destination_name: str) -> None`; `identity(fd: int) -> NativeIdentity` | Linux I/O; đóng FD ở owner của FD |
| D-01 `storage/linux_io.py` | `LinuxIOFactory` thực hiện NativeIOFactory; `LinuxNativeRoot`, `LinuxNativeReader` thực hiện protocols; FD/mutex/registry là quyền nội bộ, không serialize | D-02–D-05 |
| D-04 `jobs/linux_process.py` | `LinuxProcessFactory` thực hiện ProcessFactory; LinuxManagedProcess methods dùng absolute deadline. Adapter classmethod `launch(executable, argv, *, environment, inherited_fds, owner)` theo spec gọi từ factory | Transport |
| D-05 root `bootstrap.py` | `compose_native_runtime(*, linux_bootstrap: LinuxOwnerBootstrap | None = None)` trả `NativeRuntime(io_factory, process_factory, owner)` dataclass đặt root bootstrap; storage/jobs không import kiểu này ngược | API và fixture driver |
| E-01 `jobs/transport.py` | `WorkerTransport.launch(..., process_factory: ProcessFactory, owner, bootstrap_timeout=10)` giữ positional executable/packet; lưu proof binding, thêm `stop_evidence() -> WorkloadStopEvidence` sau startup | E-01 driver/publisher |

`ExecutionOwner.acquire()` trong spec là thao tác factory ở composition, được bind input tin cậy trước; Linux implementation dùng `from_inherited` để dependency/FD hiện rõ, không module global hoặc env cấp quyền. Windows wrapper ánh xạ `acquire_project` → `acquire_writer`, `recovery_evidence()` → bằng chứng của writer hiện tại; không đổi lifetime/semantics Windows gốc.

Chữ ký Publisher tương lai: giữ positional args hiện có, thêm keyword-only `io_factory: NativeIOFactory, workload_evidence: WorkloadStopEvidence` cạnh `validator`. Shared code gọi `workload_evidence.assert_stopped(project_id, attempt)` trước đọc/finalize và trước commit, không nhận bool. Windows adapter proof quan sát Job Object thật; fixture fake chỉ dành unit test đã ghi rõ.

Giữ wrapper `deadline_seconds` ở các API hiện tại để tương thích caller; đổi sang `deadline = monotonic()+seconds` **một lần tại boundary**. Native protocols dùng deadline tuyệt đối. Windows wrapper phải chuyển remaining seconds đúng một lần khi gọi legacy implementation đang nhận duration; không truyền absolute value vào hàm Windows cũ. Cập nhật test bằng fake clock.

## 2. File test bổ sung cho shared adapter

`tests/storage/test_native_factory.py` (A-01), `tests/jobs/test_process_factory.py` (A-03), `tests/storage/test_project_epochs.py` (C-01), `tests/architecture/test_native_adapters.py` (A-02), `tests/architecture/test_foundation_runner.py` (A-05). Các suite 010-T01–09 giữ đúng đường dẫn trong SPEC-010; test phụ không thay test integration native thật.

`tests/support/ubuntu_foundation.py` (E-01) cung cấp `FoundationFixture` context manager với `.repo`, `.writer`, `.owner`, `.packet`, `.transport`, `.publisher`, `.read_artifact() -> bytes`, `.run_worker_to_candidate()`, `.stop_worker_observed()`, `.publish(publication_id: str)`, `.confirm_stopped()`; dùng factory D-05 và fixture packet hiện có **bên trong API child đã validate native bootstrap**. `tests/support/ubuntu_foundation_driver.py`/`ubuntu_foundation_scenarios.py` chạy fixture/scenarios; process unittest bên ngoài chỉ dùng `LinuxRuntimeHarness.run_scenario(name: str) -> dict` và quan sát cgroup/results. Helper không tạo production route hoặc native proof từ bool.

Rust feature `runtime-test-harness` chỉ cho debug fixture driver, production/release cấm feature/fixture flag và không bundle examples/tests. Scenario IDs là enum/registry allowlist giữa test driver và example, không executable/path/command do UI cung cấp. Result/milestone dưới test-owned runtime directory gắn invocation, không secret; test crash thiếu result phải reopen và kiểm persistent state, không tự pass.

## 3. Mẫu prompt giao một task

```text
Bạn triển khai duy nhất task <A-01> trong <đường dẫn plan phần>.
Đọc AGENTS.md, roadmap, SPEC-010, native profile, adapter interfaces,
plan tổng, catalog interface và task được giao. Đọc source trong Files của task.
Scope: <file allowlist>. Task trước đã bàn giao tại <path>, dependency đã kiểm <list>.
Giữ signatures/constraints; thực hiện từng checkbox red → green → regression → handoff.
Không sửa task tiếp theo, không hạ test/skip/capability, không đổi namespace/protocol.
Nếu thiếu Linux/native dependency: làm phần độc lập, ghi not_run/skip với nguyên nhân;
không gọi mock thành OS proof. Nếu thiếu quyết định spec: ghi câu hỏi cụ thể, giữ
phần phụ thuộc chưa làm; không tự thay thiết kế bảo mật/ownership.
Kết quả: diff giới hạn, lệnh+exit/count/log, check đã chạy và chưa chạy,
interface đã tạo, việc còn chờ và đường dẫn handoff. Không in secret.
```

## 4. Mẫu handoff bắt buộc

Lưu dưới `Artchitect/docs/evidence/ubuntu-foundation-<ngày-thực-thi>/<task-id>/handoff.md`; không ghi đè hồ sơ spec/plan lịch sử. Khi task tiếp theo bắt đầu, người điều phối điền đường dẫn thật, không để `<...>` trong hồ sơ đã bàn giao.

```text
Task: A-01; trạng thái: verified / partial / blocked_dependency (ghi đúng)
Revision/dirty baseline: commit + diff hash; OS/interpreter/toolchain đã lọc
Scope thực tế: file tạo/sửa; thay đổi có sẵn được giữ
Input interface/version: file task trước, signature đã dùng
Output interface: file + symbol; consumer tiếp theo
Red: command, exit, failure đúng behavior thiếu
Green/regression: command, exit, passed/failed/skipped count, log path/hash
Native proof: có/không; OS/FS/cgroup/DB thật hay unit fake
Review Focus/global constraints: mục đã đối chiếu, finding còn mở
Chưa kiểm: test/subcase/env + nguyên nhân và bước mở khóa
Rủi ro/việc còn chờ: task ID tiếp nhận
Tracker/spec/roadmap: mốc đã cập nhật, chưa đóng vì lý do gì
```

## 5. Quy tắc resume và nâng cấp AI

Nếu context đầy, dừng sau substep có log và ghi file/symbol/test còn đỏ; AI kế tiếp đọc handoff và chạy lại đúng test đang đỏ. Không đọc lại lịch sử chat thay cho evidence. Không lặp cài toolchain thất bại không có thay đổi môi trường.

Nếu AI không giải thích được vì sao retained pidfd an toàn, open file description không được LOCK_UN, journal A còn cần sau B, hoặc vì sao native stop không được revoke token trước publish, chuyển task đó cho reviewer có năng lực native/storage cao hơn. Không đơn giản hóa bằng bool/killpg/path-prefix/sleep dài hoặc tăng timeout vô hạn.
