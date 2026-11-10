# Ubuntu Supervisor and Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shell native tạo đúng một supervisor invocation, trao descriptor qua kênh private và dọn descendant khi shell/API/supervisor chết.

**Architecture:** Library Rust chứa session validator và Linux runtime core không import Tauri window APIs. Binary supervisor mỏng chạy trong user service, shell wrapper ngoài service. API chỉ được coi native sau kiểm inherited owner FD/parent/cgroup, không từ flag đơn lẻ.

**Tech Stack:** Rust 2021/std OwnedFd, zbus blocking cho user D-Bus, nix/libc cho Unix/poll/FD, CSPRNG từ getrandom; Python 3.12 và blocking user-bus client Linux; Tauri 2.

**Spec:** [SPEC-010](../../../specs/010-ubuntu-foundation.md), [native profile](../../../platforms/ubuntu/ubuntu-native-profile.md), [plan tổng](../2026-11-10-ubuntu-foundation.md), [catalog](interfaces-and-handoff.md).

## Global Constraints

G-01–G-16 áp dụng. Unit `geoai-execution.service`, socket `SOCK_STREAM`, namespace canonical theo UID; handshake `b"GEOAIU1\0"` + 32 bytes; descriptor ≤8192 bytes gồm LF. Startup30s/challenge5s/cleanup10s/grace5s; D-Bus chỉ create/query, force stop retained pidfd. Không cho API/worker giữ control socket.

## Review Focus

RF-1 thuộc B-07; RF-4 thuộc B-03/B-04. B-02 thêm PID reuse/unknown unit; B-03 thêm ancillary FD/creator mismatch; B-05 thêm flag không kèm native FD; B-06 thêm all-skip harness. Tests ở từng task, không kết luận toàn native từ Rust unit test.

---

Lệnh verification có CWD root; sau khi target tương ứng đã được tạo:

| Task | Lệnh targeted đầy đủ | Expected green |
| --- | --- | --- |
| B-01 | `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib` | Test library chạy >0, không failure |
| B-02 | `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib linux_runtime::identity` và `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib linux_runtime::manager` | Identity/payload tests pass; native probe result riêng |
| B-03 | `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib linux_runtime::control` | Peer/frame/ancillary negative cases pass |
| B-04 | `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib linux_runtime::supervisor` và `cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --bin geoai-supervisor` | Unit tests pass và headless binary compile |
| B-05/B-06/B-07 | `python -m unittest discover -s tests/integration -p test_linux_session.py -v` và `python -m unittest discover -s tests/integration -p test_linux_lifecycle.py -v` | Mỗi native case required thực chạy, không all-skip |

Rust tests trong modules dùng cùng tên filter; không filter thành0 test rồi coi pass.

### Task B-01: Rust library và runtime paths tin cậy

**Read:** main.rs, windows_native.rs validator/runtime/launch; Cargo.toml, build.rs, tauri.conf.json; A-03/A-05 handoff.

**Files:** Create `apps/desktop/src-tauri/src/lib.rs`, `src/session.rs`, `src/linux_runtime/mod.rs`, `src/linux_runtime/runtime.rs`; Modify main.rs/Cargo.toml/build.rs chỉ khi cần cfg/build inputs. Cargo.lock chỉ sinh khi resolve thực.

**Interfaces:** SessionDescriptor/RuntimePaths/DevRuntimePaths trong catalog; `NativeError` là enum nội bộ reason codes từ SPEC-010, Display chỉ code, không Debug/Display descriptor/token. `lib.rs` export session và `#[cfg(target_os="linux")] linux_runtime`; main import SessionDescriptor nên Windows `super::SessionDescriptor` tiếp tục hoạt động.

- [ ] **Step 1: Viết Rust unit test đỏ trong session/runtime modules.** `descriptor_accepts_valid_loopback`, `descriptor_rejects_userinfo_query_fragment_unknown_fields`, `runtime_rejects_path_outside_resource_root`, `dev_runtime_is_native_build_configuration_only`. Giữ token validator43 ký tự và mọi validation hiện có; test serde reject unknown fields. Assert `std::mem::size_of::<SessionDescriptor>() > 0` không là test behavior, không thêm loại test này.

```rust
assert!(descriptor("http://127.0.0.1:49231", &"a".repeat(43)).validate().is_ok());
assert!(descriptor("http://127.0.0.1:49231/?token=x", &"a".repeat(43)).validate().is_err());
assert!(descriptor("http://example.org:49231", &"a".repeat(43)).validate().is_err());
```

- [ ] **Step 2: Chạy đỏ đúng target.** `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib`. Trước lib.rs có thể báo “no library targets”; sau thêm test-only lib phải có assertion/module missing đỏ thực. Nếu Rust/dependency thiếu ghi not_run và vẫn viết test/source; không claim red runtime từ lỗi network.
- [ ] **Step 3: Tách validator và resolve paths.** Debug inputs native compile-time `GEOAI_DEV_SUPERVISOR`, `GEOAI_DEV_PYTHON`, `GEOAI_DEV_BACKEND`; giữ hai key Windows hiện có. Release layout foundation cố định dưới resource root: `geoai-runtime/bin/geoai-supervisor` và `geoai-runtime/python/bin/python3.12`, package geoai được cài trong runtime đó; backend=None. Đây là fixture layout phục vụ build smoke, chưa chọn freeze/installer G3. Không nhận path từ invoke. Resolve canonical executable/root, kiểm containment/ownership và không executable writable bởi principal không tin cậy; thiếu pack báo runtime unavailable.
- [ ] **Step 4: Resolve crates và cfg.** zbus/nix/libc/getrandom chỉ target Linux. Chọn versions tương thích Rust/MSRV và API từ resolver thật; lưu Cargo.lock/toolchain version/license. Không viết code theo API crate phỏng đoán rồi sửa version pin để che compile. Thêm `default-run="geoai-desktop"` trước khi thêm bin thứ hai để cargo/Tauri không chọn nhầm supervisor. Library không khởi tạo Tauri/WebKit; dependency link chưa phải GUI startup.
- [ ] **Step 5: Green/checkpoint B-01.** Cargo lib tests trên Linux/Windows khi đủ dependency; frontend build không thay native compile. Commit `refactor(desktop): share session validation with native runtime`; ghi resolved versions hoặc chưa resolve, không tạo lock giả.

### Task B-02: Kernel identities, pidfd và user manager create/query

**Files:** Create `src/linux_runtime/identity.rs`, `manager.rs`; Modify mod.rs/runtime tests trong `apps/desktop/src-tauri/`. Rust unit tests nằm cùng module.

**Interfaces:** PinnedProcess/ProcessIdentity/UnitIdentity/UserManager đúng catalog. Private manager test double chỉ unit tests; product connector dùng user bus canonical `/run/user/<uid>/bus`, UID thực từ OS. Không expose method stop/reset/replace-by-name.

- [ ] **Step 1: Viết test đỏ properties và race.** `unit_name_and_properties_are_exact`, `start_uses_fail_mode`, `different_xdg_does_not_change_namespace`, `pin_rejects_pid_start_time_change`, `exited_pidfd_never_signals_replacement`, `manager_unknown_state_blocks_launch`. D-Bus fake ghi method/property payload, assert unit properties từng giá trị G-04, không chỉ assert method called.
- [ ] **Step 2: Chạy đỏ.** Cargo lib tests với filter `linux_runtime::manager`, rồi `linux_runtime::identity`; expected missing symbols/incorrect payload. Ghi test cùng boot giả riêng với test pidfd syscall thật.
- [ ] **Step 3: Implement pin identity.** Đọc `/proc/<pid>/stat` start_ticks bằng parser xử lý comm có space/dấu `)`; đọc boot ID kernel; pin pidfd rồi đọc lại identity/kiểm exited để chống reuse giữa hai bước. OwnedFd RAII, pidfd_send_signal không raw kill fallback. `signal()` trên process đã exit trả native reason/ESRCH đã lọc, không lookup PID mới. Thêm parser test comm `name ) with spaces`.
- [ ] **Step 4: Implement manager create/query.** D-Bus call argv/ExecStart là absolute trusted executable + native flags creator_pid/start_ticks/boot_id, không shell string. Một deadline30s truyền từ caller; mọi call dùng remaining budget. Start mode fail, query ActiveState/SubState/MainPID/InvocationID/ControlGroup; canonical cgroup directory identity từ FD, không chỉ string. UnitExists báo execution_busy hoặc recovery theo query; manager unavailable/unknown chặn, không dùng alternate unit.
- [ ] **Step 5: Green/checkpoint B-02.** Cargo lib tests + native pidfd test child thật (không cần systemd). Ghi D-Bus fixture tests chưa chứng minh user manager thực; B-06 sẽ chạy. Commit `feat(linux): bind execution units to kernel process identities`.

### Task B-03: Control socket/creator handshake và descriptor framing

**Files:** Create `src/linux_runtime/control.rs`; Modify mod.rs; Rust tests trong control module.

**Interfaces:** connect_owner/OwnerConnection trong catalog; private `accept_creator(stream, creator, deadline)` phía supervisor chia sẻ parser. `PinnedProcess` giữ supervisor, stream lifetime không clone sang child.

- [ ] **Step 1: Test đỏ framing/security.** Dùng Unix socket pair cho parser tests; pathname/private inode tests dùng temp root owned test. Tạo `control_rejects_wrong_magic_challenge_replay_and_extra_bytes`, `control_rejects_creator_pid_start_boot_mismatch`, `control_rejects_scm_rights_and_closes_received_fds`, `descriptor_limit_includes_lf`, `partial_frames_share_one_deadline`. Với 8192/8193 bytes kiểm framing trước validate DTO (padding JSON whitespace hợp lệ nếu cần).

```rust
assert_eq!(CONTROL_MAGIC, *b"GEOAIU1\0");
assert_eq!(CHALLENGE_BYTES, 32);
assert_eq!(DESCRIPTOR_MAX_BYTES, 8192);
```

Assertions behavior thêm fake clock30s total/challenge5s; đưa 1 byte mỗi bước không gia hạn deadline. Kiểm fd count trước/sau ancillary case và bị reject dù ordinary bytes hợp lệ.
- [ ] **Step 2: Red.** Cargo lib tests filter `linux_runtime::control`; missing parser/validation là đỏ dự kiến.
- [ ] **Step 3: Implement shell connect/peer proof.** Kiểm runtime dir/socket ownership/mode/no symlink, SO_PEERCRED PID/UID khớp MainPID, pin supervisor pidfd/start/boot; query invocation trước và sau handshake. Supervisor kiểm peer chính creator kernel identity đã bound ExecStart; UID đúng/challenge đúng nhưng PID sai vẫn reject. Chỉ owner connection được attach; connection khác không dừng phiên hợp lệ.
- [ ] **Step 4: Implement recvmsg framing.** Đọc đúng40 byte, echo constant-time phía server, challenge CSPRNG một lần; descriptor strict UTF-8/JSON/deny_unknown_fields, loopback validator. Mỗi recvmsg thu/close ancillary FDs, từ chối MSG_CTRUNC/control data. Sau descriptor không nhận thêm bytes/commands, EOF hoặc byte ngoài protocol trên owner connection yêu cầu stop. Không SCM_RIGHTS bootstrap qua shell socket.
- [ ] **Step 5: Green/checkpoint B-03.** Parser/socket tests + identity tests. Commit `feat(linux): authenticate the creator control connection`; handoff đầy đủ state machine accepted/attached/closed và deadline math cho supervisor.

### Task B-04: Headless supervisor và inherited API FD

**Files:** Create `src/linux_runtime/supervisor.rs`, `src/bin/geoai-supervisor.rs`; Modify lib/mod exports/Cargo.toml nếu target cần khai báo; Rust tests trong supervisor module.

**Interfaces:** run_supervisor trong catalog; thin binary chỉ parse trusted native flags/runtime layout, gọi library, exit code lọc. API launch args giữ `--native-stdio-handoff --no-console`, thêm nonsecret `--owner-fd <int> --supervisor-pid <int>`; packet/token/descriptor không qua argv/env.

- [ ] **Step 1: Test đỏ lifecycle với child fixture.** `api_not_spawned_before_creator_auth`, `api_exit_stops_supervisor`, `creator_exit_during_attach_stops_supervisor`, `owner_socket_not_inherited_by_api`, `api_receives_only_owner_and_stdio_fds`, `stderr_flood_does_not_block_descriptor`, `partial_api_descriptor_is_bounded`. Child fixture được khai báo trong Rust tests bằng executable fixture riêng, không general arbitrary-command product flag.
- [ ] **Step 2: Red.** Cargo lib tests filter `linux_runtime::supervisor`; `cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --bin geoai-supervisor` chỉ thực hiện sau target có source, ghi compile fail đúng implementation thiếu.
- [ ] **Step 3: Implement startup ownership và API spawn.** Supervisor xác minh đang là user unit MainPID/cgroup đúng profile, tạo/mở private root/owner.lock ổn định, flock nonblocking; giữ inode/FD đến hết lifecycle, không unlink/recreate lock. Khi chưa handshake hợp lệ chỉ giữ lock/listener. Sau attach spawn Python child ngay trong cgroup, stdin/out/err anonymous pipes, pass có chủ đích một duplicate owner open file description. Các socket/listener/creator/supervisor pidfd khác CLOEXEC. Nếu dùng pre_exec chỉ thao tác async-signal-safe dup2/fcntl/close; không allocate/log/DBus trong pre_exec.
- [ ] **Step 4: Implement event loop độc lập compute.** Drain stderr bounded, read descriptor bounded trong thread/poll, giám sát creator pidfd/control EOF/API pidfd đồng thời. API stdout chỉ descriptor, không forward journal; không buffer vô hạn. No attach30s thì exit. Normal close đóng API stdin, grace≤5s; nếu chưa dừng, supervisor kết thúc để user manager cleanup nhóm, tổng10s; state chưa chứng minh dừng vẫn recovery. Signal shell chỉ retained supervisor pidfd; unit name không dùng để stop.
- [ ] **Step 5: Green/checkpoint B-04.** Unit/lifecycle child tests + build binary. Test user service còn để B-06. Commit `feat(linux): supervise the API without a desktop window`; ghi FD ownership table thực tế và cleanup failure path, không claim cgroup cleanup từ direct child tests.

### Task B-05: API xác minh inherited owner trước native mode

**Read:** root bootstrap serve/main, API session policy, guards; native profile mục 3 và5.

**Files:** Create `backend/geoai/storage/linux_bootstrap.py`; Modify `backend/geoai/bootstrap.py`, `pyproject.toml` Linux native optional extra, `tests/integration/test_shell_lifecycle.py`; Create `tests/integration/test_linux_session.py` cho các ca bootstrap đầu tiên.

**Interfaces:** LinuxOwnerBootstrap/validate_inherited_owner từ catalog. Chọn blocking user-bus client `jeepney` trong extra `native-linux` với platform marker Linux; version/lock khóa từ resolve thật, Windows không cần cài. Private query helper đọc manager properties trên canonical user bus với deadline; không subprocess shell/systemctl string hay trust env INVOCATION_ID tự khai.

- [ ] **Step 1: Test đỏ bypass native.** `test_native_flag_without_owner_fd_rejected`, `test_regular_file_or_unlocked_owner_fd_rejected`, `test_parent_pid_or_invocation_mismatch_rejected`, `test_dev_pipe_mode_remains_metadata_only`, `test_descriptor_waits_for_server_started`. Native integration cần harness B-06 mới chạy đủ; unit validation dùng OS file/pipe/child và manager fake ghi rõ scope.
- [ ] **Step 2: Red.** `python -m unittest discover -s tests/integration -p test_linux_session.py -v`; dev regression `... -p test_shell_lifecycle.py -v`. Test chỉ skip phần Linux khi không có OS, không skip metadata/dev tests.
- [ ] **Step 3: Implement inherited proof.** FD phải là owned lock regular file private, inode khớp canonical owner.lock và parent FD/kernel lock binding, API PPid/start/boot khớp supervisor MainPID, invocation/cgroup API thuộc đúng unit. Pin parent pidfd, kiểm lại trước trả bootstrap object. Đọc fdinfo/proc/kernel binding có lỗi thì fail closed; không `LOCK_UN` để probe, không nhận bool hoặc chỉ gọi flock thành công rồi coi như proof. D-Bus/cgroup đọc bằng helper native có deadline, không theo XDG_* override.
- [ ] **Step 4: Split root bootstrap composition.** Bỏ import windows_owner vô điều kiện; dev mode vẫn metadata-only. Native Windows gọi wrapper A-03; Linux validate bootstrap rồi giữ proof object đến finally. Owner/project chưa được cấp khi C chưa xong; không tự claim một project giả để bật flag. Chỉ stdout private descriptor sau socket bind/Uvicorn started, stderr SanitizedLogFilter. Close duplicate owner FD trong API không LOCK_UN; giữ supervisor FD sống.
- [ ] **Step 5: Green/checkpoint B-05.** Dev lifecycle/security tests + bootstrap invalid cases; native thành công chuyển B-06. Commit `feat(linux): validate native API bootstrap authority`; handoff flags/FD/CLOEXEC map và optional dependency resolve evidence.

### Task B-06: Integration harness dùng cùng runtime core

**Files:** Create `apps/desktop/src-tauri/examples/geoai-runtime-harness.rs`, `tests/support/__init__.py`, `tests/support/linux_runtime.py`; Extend test_linux_session.py; Create `tests/integration/test_linux_lifecycle.py`.

**Interfaces:** LinuxRuntimeHarness ở catalog. Rust example dùng cùng manager/control/runtime library như shell, creator PID là chính example; descriptor chuyển qua anonymous stdout pipe cho Python harness, không terminal/log. Example không được bundle/phát hành hoặc expose production route. B-06 chỉ metadata/lifecycle; fixture project/DB scenarios ở E-01 sẽ chạy trong API child bằng test-only build, không thêm quyền cho process unittest bên ngoài.

- [ ] **Step 1: Test đỏ isolation.** `test_harness_requires_private_stdio`, `test_harness_missing_manager_is_skip_with_reason`, `test_harness_does_not_replace_existing_owner`, `test_harness_tracks_only_its_invocation`. Test probe thiếu systemd mô phỏng trả lý do; skip phải phân biệt với implementation fail ở môi trường đủ primitive.
- [ ] **Step 2: Build/red native.** Build example với Cargo rồi `python -m unittest discover -s tests/integration -p test_linux_session.py -v`. CWD/root config lấy từ executable fixture pack tin cậy do test tạo, không argv tùy ý do UI. Chạy native chỉ dưới OS test account/session riêng, xác nhận không có GeoAI session đang dùng; unit production cố định không tự suffix test để vượt lock.
- [ ] **Step 3: Implement harness.** Probe OS/FS/user manager/pidfd trước setUp, create test-owned runtime fixture pack, pin example/API identities, đọc descriptor private bằng SessionDescriptor Pydantic, dùng actual kernel/cgroup/unit query. kill_component chỉ nhận shell/supervisor/api/worker nằm trong invocation đã pin; pidfd signal, không PID/unit-name fallback. Cleanup chạy cả khi assertion fail, không xóa project ngoài temp root.
- [ ] **Step 4: Chạy positive/negative thật.** `test_creator_handshake_and_private_descriptor`, `test_second_instance_is_busy_without_stopping_first`, `test_shell_eof_cleans_unit`, `test_kill_supervisor_cleans_api`, `test_api_crash_ends_session`. Assert invocations/FD/proc/cgroup và log redaction, không chỉ HTTP200. Tests disconnect không được để fake process có shell socket clone khiến EOF không đến.
- [ ] **Step 5: Green/checkpoint B-06.** Record Ubuntu OS/boot/session/FS/manager identities đã lọc, result riêng từng LTS. Commit `test(linux): exercise real user-service session lifecycle`; nếu chỉ container thiếu manager thì partial, không ghi các native cases pass.

### Task B-07: Tauri Linux wrapper, retry và close không treo UI

**Files:** Create `apps/desktop/src-tauri/src/linux_native.rs`; Modify main.rs, frontend tests `apps/desktop/src/App.test.tsx`, `tests/integration/test_linux_session.py`, desktop README; build config/resources chỉ phần fixture runtime layout B-01, giữ bundle.active=false.

**Interfaces:** Linux `NativeSession::launch(app: &tauri::AppHandle, cancelled: Arc<AtomicBool>) -> Result<NativeSession,String>`, `.descriptor()`, `.is_alive()`, `.stop()` tương đương Windows interface. SessionState giữ Arc<Mutex<Option<ActiveSession>>> và atomic close flag; `bootstrap_session` async thực hiện blocking native work trong spawn_blocking. Cfg Linux/Windows/unsupported tách rõ, Windows không mất native behavior.

- [ ] **Step 1: Viết test đỏ retry/close.** `test_retry_after_ui_timeout_reuses_same_invocation`, `test_close_during_native_startup_cancels_same_session`, `test_untrusted_webview_cannot_supply_runtime_paths`. Rust fake clock startup20s và UI fake timer10s: late result bị bỏ, retry cùng shell nhận đúng active descriptor, không StartTransientUnit lần hai. Frontend giữ panel/projectName sau retry. Không đổi UI10_000ms thành30s để che race.
- [ ] **Step 2: Red.** `npm --prefix apps/desktop test` và Cargo lib tests; Linux real shell test chưa pass khi wrapper not(windows) vẫn windows_required. Test Tauri bằng launch thực sau fixture runtime/resources chuẩn bị.
- [ ] **Step 3: Implement wrapper/controller.** Native worker giữ connection/supervisor pidfd. Async invoke không giữ lock trên GUI thread; close callback chỉ set cancellation và schedule cleanup, không block mutex/DBus10–30s. Linux launch poll/calls kiểm cancel giữa các bước có deadline; cancel sau unit create dùng đúng retained proof, không app StopUnit. Windows launch cũ vẫn bounded; nếu close flag đến khi đang launch thì vừa trả session phải stop đúng phiên trước trả descriptor.
- [ ] **Step 4: Health/ready và retry.** Giữ validateSession/frontend health/capabilities flow và token header; native core kiểm health trong deadline30s, descriptor không tự ready. Pending bootstrap từ cùng shell chỉ có một native operation; queued retry tái dùng session còn sống hoặc cleanup session đã xác minh chết trước create mới. Không cho webview close/kill arbitrary PID/unit. Capability native/owner/writer/inference vẫn false dù native fixture pass.
- [ ] **Step 5: Green/dev smoke.** Npm tests/typecheck/build, Rust tests, `npm --prefix apps/desktop run tauri -- dev` trên WebKitGTK thật. Ghi actual origin/CSP/Host/Authorization policies; không wildcard để vượt WebKit lỗi. Test close/kill và unit không còn workload; release production smoke ở E-04.
- [ ] **Step 6: Checkpoint B-07.** Commit `feat(desktop): connect Ubuntu native sessions with bounded cleanup`. Handoff UI10s/native30s interaction, cancellation paths và results từng môi trường. B chưa đóng010.2 khi owner/journal C chưa xong.
