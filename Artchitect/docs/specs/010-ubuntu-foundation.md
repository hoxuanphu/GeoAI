# SPEC-010 — Ubuntu foundation: adapter, lifecycle và luồng fixture

**Ngày:** 10/11/2026. **Trạng thái đặc tả:** hoàn tất rà soát và kiểm tài liệu, sẵn sàng làm đầu vào gen code foundation; [bằng chứng](../evidence/spec010-2026-11-10/review.md). **Trạng thái code/runtime:** chưa bắt đầu. Người dùng yêu cầu hoàn thiện spec trước; đây không phải lệnh triển khai code hoặc quyết định nghiệm thu Ubuntu. Các lựa chọn kỹ thuật vẫn ở trạng thái đề xuất theo ADR-012.

**Mục tiêu:** một checkout chạy cùng API/coordinator/contracts trên Windows và Ubuntu; trên Ubuntu 22.04 LTS và 24.04 LTS, shell mở phiên native và một job tổng hợp đi qua worker thật → staging → publisher → SQLite, giữ owner, cancel/retry và fencing đúng.

Nguồn: [ADR-012](../adr/ADR-012-ubuntu-desktop.md), [architecture](../architecture.md), [IPC](../ipc-protocol.md), [resolver](../worker-resolver.md), [security acceptance](../importer-resolver-security.md). Hai phần bắt buộc của spec là [profile lifecycle/bootstrap](../platforms/ubuntu/ubuntu-native-profile.md) và [interface adapter](../platforms/ubuntu/ubuntu-adapter-interfaces.md); không tự chọn lại protocol trong lúc gen code.

## 1. Phạm vi và dependency

**Kế hoạch thực thi tiếp nối:** [plan tổng Superpowers](../superpowers/plans/2026-11-10-ubuntu-foundation.md) và 5 phần A–E/26 task có catalog signatures, test steps và handoff. Người dùng hiện yêu cầu lập plan thật kỹ; chưa triển khai code. Bằng chứng lập/kiểm plan tại [hồ sơ riêng](../evidence/ubuntu-plan-2026-11-10/review.md), không thay bằng chứng đặc tả phía trên hoặc đóng 010.1–010.3.

| Trong SPEC-010 | Ngoài nghiệm thu SPEC-010 |
| --- | --- |
| Interface OS nội bộ và composition root; regression Windows | Công bố support matrix sản phẩm hoặc đóng toàn bộ SPEC-003/004/009 |
| Supervisor headless, user service/cgroup, session và FD/bootstrap Linux | GIS/Prithvi/PDF/viewer nghiệp vụ hoặc chất lượng model |
| Owner/project writer/epoch/recovery, native file I/O và job fixture | Provider live, credential, dữ liệu khách hàng hoặc ngân sách G0 |
| SQLAlchemy/Alembic thật, candidate/publish/backup fixture local | `.deb` phát hành, máy sạch/offline/upgrade/uninstall G3 |

Được làm trước G0 với dữ liệu tổng hợp/offline và policy fixture có giới hạn. Thiếu executor/dependency không cấm viết phần thuần và test tương ứng; kiểm native/DB chưa chạy phải ghi fail/skip/chưa kiểm đúng thực tế. Không dùng fixture in-memory thay bằng chứng SQLite/native.

Dependency đầu vào: kiểu SPEC-001; phần nền SPEC-003/004/009 hiện có và semantics đã mô tả, **không đòi ba spec hoàn tất toàn bộ trước**. SPEC-010 triển khai nhánh Ubuntu của các spec đó và chạy lại integration liên quan. SPEC-005/007/008/006 và G3 tiêu thụ nền đã kiểm sau này; không tạo vòng dependency.

Các quyết định kỹ thuật ở đây là cấu hình thiết kế đề xuất của đợt spec. Việc viết spec xong không nâng ADR-012 thành Accepted. Review thiết kế/fixture có thể diễn ra trước nghiệm thu sản phẩm; không chờ toàn bộ UB-01–20 mới bắt đầu triển khai phần đủ dependency.

## 2. Các quyết định dùng làm đầu vào code

| Chủ đề | Quy định của SPEC-010 |
| --- | --- |
| Target kỹ thuật | Ubuntu 22.04/24.04 LTS, `x86_64`, local ext4, cgroup v2 và user manager truy cập được; target khác phải báo chưa hỗ trợ |
| Topology | Tauri shell ngoài unit; supervisor Rust headless là main process trong transient user service; Python API là child; API tạo worker trong cùng cgroup |
| Namespace | Một `geoai-execution.service` trong user manager của UID; runtime `/run/user/<uid>/geoai-execution-v1`; không suffix project/app version |
| Kênh shell | Unix socket pathname `SOCK_STREAM`, kiểm peer và invocation, handshake một lần rồi giữ kết nối sống; D-Bus ứng dụng chỉ tạo/truy vấn unit |
| FD | V1 truyền bootstrap bằng anonymous pipe kế thừa có allowlist giữa cha–con; không nhận FD ancillary qua socket shell |
| Quyền chạy | Một owner/UID, một project writer, một workload nặng; owner còn hợp lệ thì báo bận, không stop unit để giành quyền |
| Schema | Dùng SessionDescriptor, WorkerLaunchPacket/context/RPC hiện có; ledger mới là private DTO dự kiến, phải định kiểu Pydantic và sinh artifact trong task code liên quan trước sử dụng |
| Worker v1 | Không resident sau attempt; worker và mọi workload con phải được xác nhận dừng trước finalize/publish hoặc cấp compute mới |
| Runtime/build | Python 3.12 riêng, dependency resolve/lock thực theo executor; build ABI theo guide Ubuntu. Không ghi phiên bản patch/lock giả trong spec |

## 3. Input, output và file đích

Input fixture gồm JobSpec/InputSnapshot/WorkerAccessContext/WorkerLaunchPacket hợp lệ, manifest bytes/hash cố định, file nhỏ managed và external, SQLite temp project, policy quota/deadline fixture. Giữ fixture artifact hiện có `FIXTURE_ARTIFACT_BYTES` hoặc thêm fixture version mới rõ ràng; không giả dữ liệu/model Prithvi.

| Deliverable dự kiến | Nội dung |
| --- | --- |
| `backend/geoai/storage/native_io.py`, `native_owner.py` | Protocol/factory nội bộ và lỗi nền; tận dụng `storage/guards.py`, không tạo WriterGuard thứ hai |
| `backend/geoai/storage/linux_io.py`, `linux_owner.py` | Linux FD/root/snapshot/publish I/O và owner/project writer/stop evidence |
| `backend/geoai/jobs/process.py`, `linux_process.py` | Process contract và Linux launcher/observer; giữ worker framing trong `jobs/protocol.py` |
| `storage/{io_resolver,extraction,gc}.py`, `jobs/{transport,publisher}.py` | Dùng adapter đã cấp, bỏ phụ thuộc/`isinstance` kiểu Windows khỏi đường dùng chung |
| `backend/geoai/bootstrap.py`, `workers/{bootstrap,main}.py` | Composition theo OS và private bootstrap; không import native Windows vô điều kiện trên Linux |
| `backend/geoai/contracts/native.py` | Private LinuxOwnerLedger dự kiến, registry/fixture/exporter/checks đồng bộ SPEC-001; không chứa syscall hoặc logic cấp quyền |
| `apps/desktop/src-tauri/src/linux_native.rs`, `linux_runtime/` | Native session wrapper và logic manager/control dùng chung cho shell/supervisor |
| `apps/desktop/src-tauri/src/bin/geoai-supervisor.rs`, composition Rust cần thiết | Entry point headless; không khởi tạo WebKit/Tauri window trong user manager |
| Các suite ở mục 7; README dev/build và lock sinh thật | Fixture/native/DB/regression, setup hai LTS, provenance và kết quả |

Các đường dẫn này là output tương lai. Chỉ thêm package/file khi có logic/test; không tạo skeleton trống để báo triển khai. Dependency Rust/Python mới cần resolve thực, license và lock; không đưa binary, weights hoặc credential vào Git.

## 4. Interface và bất biến bắt buộc

1. `storage/native_io.py` và `jobs/process.py` định nghĩa interface không import adapter OS. `bootstrap`/worker entry chọn factory; module nền không import ngược bootstrap hoặc Tauri.
2. Chỉ thay dependency OS; dữ liệu JobSpec, RPC, attempt token, transaction publish, content hash và retention giữ semantics chung. Không gửi ORM/DB connection qua pipe.
3. WriterGuard là guard native có lifetime, không là bool trong DTO. API nhận owner FD từ supervisor, tự xác minh fd/inode/cgroup/parent identity; FD không tới worker. Khóa project dùng file identity, không chỉ tên project.
4. Owner epoch bền vững và lớn hơn epoch cũ của project trước cấp context/attempt; xem profile. Mất heartbeat/lock lấy được không đủ chứng minh workload cũ đã dừng.
5. `openat2`/directory FD giữ containment; Linux không mô phỏng deny-write sharing của Windows. Input bên ngoài được cố định thành snapshot kiểm hash; publish đợi workload dừng rồi tạo bản riêng do publisher sở hữu.
6. Candidate chỉ là ID/manifest đã binding. Publisher kiểm bytes/profile/context và transaction kiểm lại state/token/uniqueness; file rename trước commit chưa là publication.
7. Không thêm route job/import fixture vào production API. Integration driver dùng cùng composition/coordinator/repository qua fixture entrypoint chỉ trong tests; UI acceptance của spec là bootstrap/health/error/close.
8. CapabilitiesResponse hiện dùng Literal false cho native/owner/writer/inference. Giữ nguyên đến task schema/API có kiểm riêng; không flip field để chứng minh SPEC-010 đạt. Nếu thay DTO trong task code phải đồng bộ Pydantic, docs, fixtures, schema/client và tests cùng lần.

## 5. Luồng fixture hoàn chỉnh

1. Shell kiểm môi trường, nhận quyền tạo unit mới rồi handshake với supervisor đúng invocation; nhận SessionDescriptor qua kênh private, gọi health/capabilities có token đúng.
2. API dựng factory Linux, nhận native owner proof, khóa project, hoàn thiện epoch và migrate/reconcile SQLite qua WriterGuard trước nhận việc.
3. Driver enqueue JobSpec, repository cấp AttemptKey/token và lease; context/packet mới gắn đúng owner/project/attempt. Worker khởi động trong cgroup, đọc packet qua FD private, negotiate RPC rồi accepted.
4. Worker kiểm dependency/hash, ghi artifact trong staging và gửi candidate/completed. Coordinator thu hồi quyền start thêm, đóng pipe và đợi workload thực sự dừng; input/model pin vẫn theo policy.
5. Publisher kiểm/finalize artifact, fsync và rename no-replace cùng filesystem; repository transaction recheck token/state, commit publication duy nhất. Driver truy vấn publication và đọc lại bytes/hash đúng.
6. Ca cancel/retry/crash lặp lại với attempt/context mới; attempt cũ không thể publish. Shell close/crash dọn nhóm; lần mở sau chỉ chạy sau khi workload cũ đã xác nhận dừng và DB reconcile hoàn tất.

Thành công của luồng này là foundation kỹ thuật, không phải G1 đầy đủ hoặc sản phẩm Prithvi. Không đổi grid/nhãn/tolerance/business budget để đạt fixture.

## 6. Lỗi và giới hạn

| Lỗi native nội bộ | Hành vi | StructuredError hiện có nếu đi qua API/RPC |
| --- | --- | --- |
| `linux_runtime_unavailable`, `native_io_unavailable` | Không spawn compute; báo thiếu capability cụ thể đã lọc | `missing_resource`, không retry tự động |
| `execution_busy` | Chỉ trạng thái bận; không nhập project ở writer mode | `resource_exhausted`, không retry tự động |
| `recovery_required`, `containment_unverified` | Chặn grant/publish/compute mới; giữ pin và bằng chứng | `internal_error`, không retry tự động |
| `bootstrap_rejected`, `protocol_mismatch` | Đóng kết nối chưa được cấp quyền; không dùng token cũ | `invalid_input`, không retry tự động |
| `bootstrap_timeout` | Dừng supervisor qua pidfd đúng phiên do caller tạo, không StopUnit(name); timeout không đủ chứng minh dọn xong | `internal_error`, không retry tự động |
| `stale_attempt`, bytes/context/identity không khớp | Từ chối thao tác; giữ snapshot đã khóa | `stale_attempt` hoặc `invalid_input` theo nguyên nhân |

Đây là mã nội bộ launcher/adapter; không thêm literal vào StructuredError bằng văn bản. Job retry đã định trong SPEC-004 tiếp tục áp dụng sau khi coordinator có stop evidence và retry policy; bảng không biến lỗi thiếu quyền thành retry vô hạn. Không đưa raw path, argv, environment, token, nonce hoặc signed URL vào UI/log.

## 7. Bộ kiểm phải có khi triển khai

| ID | Suite dự kiến và ca quyết định | Bao phủ UB |
| --- | --- | --- |
| 010-T01 | `tests/architecture/test_native_adapters.py`: shared imports không kéo Windows trên Linux; OS factory chọn đúng; Windows behavior/regression giữ nguyên | UB-01–03 |
| 010-T02 | `tests/contracts/test_native_ledger.py`: private DTO/registry/exporter, epoch/version/unknown fields; SessionDescriptor/WorkerLaunchPacket không bị đổi ngầm | UB-02/09 |
| 010-T03 | `tests/integration/test_linux_session.py`: Tauri/WebKitGTK dev+production, handshake/frame/nonce/peer/invocation/creator PID-start-boot sai, FD ancillary, stale token, Origin/Host, SSE/Range theo route có thật | UB-04/05/09 |
| 010-T04 | `tests/integration/test_linux_owner.py`: hai bản cài/project/session, khác XDG env, cùng inode project qua alias, lock rò/unlink, ledger corrupt/mất, epoch project cao hơn ledger, journal A→B crash trước reconcile A, đổi project/reboot/record thiếu/đầy; không giành owner hợp lệ | UB-06/08 |
| 010-T05 | `tests/integration/test_linux_lifecycle.py`: kill shell/supervisor/API/worker; grandchild `setsid`, FD rò giữ EOF, process kẹt, cgroup chưa rỗng; pidfd cũ không kill invocation mới dù cùng tên unit/PID reuse | UB-07/08 |
| 010-T06 | `tests/integration/test_linux_worker_transport.py`: packet FD allowlist, log native stdout/stderr, partial/oversized/NaN, cancel/heartbeat, pipe đóng, bootstrap deadline | UB-09 |
| 010-T07 | `tests/storage/test_linux_io.py`: managed/external input dương, source đổi, symlink/magic-link/hardlink/ancestor swap/FIFO/device/mount, sentinel ngoài staging; thiếu primitive không fallback yếu | UB-10/11 |
| 010-T08 | `tests/integration/test_linux_publish.py`: SQLite thật, stale/cross-attempt candidate, writer FD còn mở, copy finalize, fsync/rename/commit fault points, EXDEV/no-replace, cancel/publish race | UB-02/12/13 |
| 010-T09 | `tests/integration/test_ubuntu_foundation.py`: luồng mục 5, reopen/reconcile/retry, backup/restore fixture; không chỉ mock kết quả | UB-02/04/06/09–13 |

Các suite là deliverable, chưa tồn tại/chưa chạy nếu chưa được kiểm kê. NET fixture hiện có chạy regression khi importer đổi; UB-14 không được ghi full pass từ policy thuần. UB-15–20 thuộc các task/gate tiếp theo; không dùng thiếu model/GPU/installer để chặn mọi test nền.

## 8. Thứ tự thực hiện và điều kiện đóng

| Mốc | Việc và điều kiện chuyển |
| --- | --- |
| 010.1 Interface + baseline | Tách adapter và thu thập contracts/core/frontend/DB baseline trên hai LTS, regression Windows; ghi đầy đủ pass/fail/skip. Chưa có native proof thì capability vẫn chưa sẵn sàng |
| 010.2 Native lifecycle + FD | Triển khai profile và 010-T02–06; có log chứng minh một owner, đúng invocation và không có workload mồ côi. Không cấp quyền I/O/publish từ metadata-only mock |
| 010.3 I/O + fixture integration | 010-T07–09 qua file/process/SQLite thật trên cả hai LTS, các ca âm và sentinel; review không còn lỗi chặn invariants |

**Đóng SPEC-010** khi đủ các mốc và bằng chứng thực tương ứng, gồm Windows regression của đường shared đã sửa. Không đóng chỉ vì source đã gen hoặc tests bị skip. X11/Wayland ghi subcase riêng; thiếu môi trường nào ghi chưa kiểm và chưa công bố profile đó.

Lệnh nền có thật: `PYTHONPATH=backend python -m unittest discover -s tests/contracts -v`, các suite `tests/architecture`, `tests/storage`, `tests/integration`; exporter contracts/API `--check`; frontend `npm test`, `npm run typecheck`, `npm run build`. Khi thêm suite Linux, README phải có lệnh `unittest` cụ thể tương ứng và lệnh native Tauri thực; không báo pass trước khi chạy. Dependency/lock/build/OS/cgroup/FS/fixture hash, exit code và log đã lọc theo [testing strategy](../guides/testing-strategy.md).

**Tình trạng tại đợt đặc tả:** 010.1–010.3 chưa bắt đầu; ADR kỹ thuật vẫn đề xuất; UB runtime chưa chạy. Phần review và kiểm tài liệu được lưu ở [báo cáo SPEC-010](../evidence/spec010-2026-11-10/review.md), tách khỏi kết quả triển khai tương lai.
