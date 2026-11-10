# Ubuntu Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Triển khai SPEC-010 thành luồng shell → supervisor → API → worker → publish → SQLite có bằng chứng trên Ubuntu 22.04/24.04 LTS, giữ regression Windows.

**Architecture:** Giữ contracts/coordinator/repository dùng chung; composition root chọn adapter OS. Shell nằm ngoài transient user service, supervisor Rust headless giữ ownership/liveness; API là child và worker không thoát khỏi cgroup. Linux dùng FD/openat2, generation journal và stop-then-copy publish.

**Tech Stack:** Python 3.12 riêng, unittest, Pydantic 2, FastAPI/Uvicorn, SQLAlchemy/Alembic/SQLite WAL; Rust 2021, Tauri 2/WebKitGTK, systemd user D-Bus/cgroup v2; React/TypeScript/Vitest.

**Spec:** [SPEC-010](../../specs/010-ubuntu-foundation.md), [native profile](../../platforms/ubuntu/ubuntu-native-profile.md), [adapter interfaces](../../platforms/ubuntu/ubuntu-adapter-interfaces.md). Đọc cả ba trước task đầu tiên.

## Global Constraints

- G-01: Đích foundation là `Ubuntu 22.04/24.04 LTS`, `x86_64`, local `ext4`, `cgroup v2` và user manager truy cập được; đây chưa là support matrix phát hành.
- G-02: Unit `geoai-execution.service`; runtime `/run/user/<uid>/geoai-execution-v1`; directory `0700`, lock/socket `0600`; không đổi namespace qua project/version/XDG override.
- G-03: Ledger lấy home từ user database OS, `.local/state/geoai/execution-v1/ledger.json`; project lock `.geoai-writer.lock`. Không reset epoch sau reboot hoặc restore/import.
- G-04: `StartTransientUnit(mode="fail")`, `Type=exec`, `KillMode=control-group`, `Restart=no`, `RemainAfterExit=no`, `TimeoutStopSec=5s`, `SendSIGKILL=yes`, `CollectMode=inactive-or-failed`; không Delegate/linger/system service, không app StopUnit/ResetFailed/replace theo tên.
- G-05: Control socket `AF_UNIX/SOCK_STREAM`, magic 8 byte `GEOAIU1` + NUL, challenge CSPRNG 32 byte; SessionDescriptor JSON + LF tối đa `8192` byte gồm LF; không SCM_RIGHTS, reject/close ancillary FD.
- G-06: Startup một deadline monotonic `30s`, challenge tối đa `5s`; cleanup tổng `10s`, grace tối đa `5s`. Đây là fixture/config kỹ thuật, không phải SLO/budget G0.
- G-07: Pin creator/supervisor/API/worker identity bằng pidfd + PID/start ticks/boot ID, kiểm invocation/cgroup. Signal retained pidfd; ESRCH không fallback PID/unit name.
- G-08: Owner FD chỉ supervisor và API giữ; API không `LOCK_UN` open file description chia sẻ; worker không có owner/writer/DB/publication writable FD. Giữ một owner/UID, một writer project, một workload nặng.
- G-09: Epoch mới `max(epoch_high_watermark, project_max_epoch)+1`; max project gồm Job/Attempt/DependencyLease. Journal giữ mọi generation; 1024 records/1,048,576 encoded bytes gồm LF; đầy thì chặn, không tự GC.
- G-10: OwnerStopEvidence do native observer tạo và kiểm OS lại, binding đúng project root/owner/epoch. Metadata, heartbeat hết hạn, lock lấy được hoặc bool không là proof.
- G-11: `openat2` dùng `RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS|RESOLVE_NO_MAGICLINKS|RESOLVE_NO_XDEV`; thiếu primitive thì fail closed. `linux-dev:<decimal>`/`linux-ino:<decimal>` là encoding FileIdentity hiện có.
- G-12: External input hợp lệ phải có snapshot/copy kiểm expected hash/size/identity; Linux không giả deny-write sharing. Publish chờ hết workload con, copy private, rehash/fsync, renameat2 NOREPLACE cùng FS, fsync dirs, rồi DB fencing commit; EXDEV từ chối.
- G-13: RPC/WorkerLaunchPacket dùng framing hiện có `1,048,576` byte gồm LF; giữ `registry_delivery="handle-snapshot"`. Schema `0.1.0`; Pydantic là nguồn, JSON Schema/client sinh ra; ledger mới thuộc private registry.
- G-14: CapabilitiesResponse native/owner/writer/inference vẫn Literal false. Không thêm production route job/import fixture. Không nhận executable/path/command tùy ý từ webview.
- G-15: G0 chưa hoàn tất; task chỉ dùng fixture tổng hợp/offline. Prithvi + decoder nghiệp vụ vẫn bắt buộc bản đầu nhưng không thuộc nghiệm thu foundation. Không tự đặt nhãn/AOI/ngưỡng/budget.
- G-16: Không sửa test để né lỗi, xóa Windows suite, thay SQLAlchemy bằng in-memory/sqlite3 repository hoặc ghi pass cho skip. Không lưu token/nonce/descriptor/argv/env dump trong evidence.

## Review Focus

| ID | Điều kiện dễ sót và hành vi phải có | Task/test giữ điều kiện |
| --- | --- | --- |
| RF-1 | UI timeout 10s trong lúc native còn startup 30s: retry cùng shell không tạo owner thứ hai, kết quả trễ không thay state UI | B-07 `test_retry_after_ui_timeout_reuses_same_invocation`; giữ test App late-result |
| RF-2 | Worker đã chết nhưng repo vẫn running: phải publish trước khi `confirm_stopped()` thu hồi token, vẫn chặn compute khác bằng native observer | E-01 `test_stop_observation_does_not_revoke_publish_token` |
| RF-3 | WAL chứa epoch mới hơn main DB hoặc schema lạ: đọc đủ epoch mà không migrate/ghi/khởi tạo DB, không `immutable=1` bỏ qua WAL | C-01 `test_epoch_reader_sees_committed_wal_without_writes` |
| RF-4 | Pipe đóng một phần, stderr đầy hoặc FD number bị tái dùng: không đóng nhầm FD và không để reader/writer thread giữ phiên sống | B-03/B-04/D-04, test `test_partial_bootstrap_failure_closes_only_owned_fds` |
| RF-5 | Tên project Unicode/khoảng trắng/`#` và root alias: không đổi identity/epoch hoặc trỏ SQLAlchemy URI sang DB khác | C-01/C-02 `test_unicode_project_uri_and_alias_keep_identity` |

---

## 1. Cách dùng bộ plan

**Trạng thái:** plan triển khai, chưa thực hiện task code. Yêu cầu phiên này chỉ lập plan. Không tick bước triển khai từ việc đọc plan hoặc chạy checker tài liệu.

Đọc theo thứ tự: AGENTS → roadmap → SPEC-010/profile/interface → file này → [catalog interface và handoff](2026-11-10-ubuntu-foundation/interfaces-and-handoff.md) → đúng plan phần được giao. Không yêu cầu AI tầm thấp nạp cả repo hoặc tự thiết kế lại protocol.

| Phần | Task | Deliverable độc lập để review | Dependency | Mốc tracker |
| --- | --- | --- | --- | --- |
| [A — Shared adapters và contracts](2026-11-10-ubuntu-foundation/01-shared-adapters.md) | A-01–A-05 | Interface có Windows adapter dùng thật, private ledger DTO, baseline/checks | Source hiện tại | Đầu 010.1 |
| [B — Supervisor và session](2026-11-10-ubuntu-foundation/02-native-session.md) | B-01–B-07 | Runtime Rust headless, D-Bus/control/FD, session security/lifecycle fixture | A | Đầu 010.2 |
| [C — Ownership và recovery](2026-11-10-ubuntu-foundation/03-owner-recovery.md) | C-01–C-04 | Epoch reader read-only, kernel locks, journal/guard/stop evidence | A, B | Cuối 010.2 |
| [D — Linux I/O và worker](2026-11-10-ubuntu-foundation/04-linux-io-worker.md) | D-01–D-05 | openat2/snapshots/writes/publish bytes, worker transport thật | A, B, C | Đầu 010.3 |
| [E — Tích hợp và nghiệm thu foundation](2026-11-10-ubuntu-foundation/05-integration-validation.md) | E-01–E-05 | Process/files/SQLite, races/crash/restore và báo cáo hai LTS/Windows | A–D | Đóng các mốc theo evidence |

Có **26 task**, không phải 26 mốc sản phẩm. Thứ tự mặc định tuần tự A → B → C → D → E. Không song song task cùng sửa bootstrap, transport, Cargo.toml, contracts registry hoặc fixture chung. Một AI nhận một task; task có nhiều syscall phải giữ đúng các substep/test rồi mới nhận task tiếp.

010.1 chỉ đóng khi A hoàn tất **và** baseline trên hai LTS/Windows đã có, không đóng từ baseline một máy. 010.2 cần B/C và acceptance tương ứng. 010.3 cần D/E. Nếu thiếu môi trường, bàn giao code đã kiểm ở tầng có thể chạy và giữ mốc phụ thuộc chưa hoàn tất.

## 2. Baseline source đã đối chiếu khi lập plan

| Source hiện tại | Hiện trạng ảnh hưởng cách làm |
| --- | --- |
| `backend/geoai/bootstrap.py` | Import windows_owner vô điều kiện; `_require_native_job()` Windows; dev anonymous-pipe mode có thật, không được xóa |
| `storage/io_resolver.py`, `extraction.py`, `gc.py`, `jobs/publisher.py` | Import/check concrete Windows NativeRoot; shared code cần injection, không chỉ đổi type annotation |
| `jobs/transport.py` | Launch hiện chỉ Windows, tự tạo pipe và msvcrt handle; framing/request/event đã có, giữ lại |
| `workers/bootstrap.py`, `workers/main.py` | Read launch handle Windows; worker tự tạo Windows roots; native stdout redirection đã có |
| `storage/guards.py` | WriterGuard/GuardLease/OwnerStopEvidence đã có; không tạo bản sao protocol |
| `storage/repository.py` | `confirm_stopped()` thu hồi token và có thể chuyển running → failed; `publish()` đòi active token/state. Native stop observation và DB state transition phải tách đúng thứ tự |
| `contracts/__init__.py`, exporter | Có durable/wire/private_runtime registry; chưa có PRIVATE_NATIVE_MODELS/native.py |
| `src-tauri/src/main.rs` | SessionDescriptor validator nằm trong binary; cfg not(windows) trả windows_required; cần library dùng chung cho headless binary |
| `src-tauri/Cargo.toml`, config | Chưa Cargo.lock; bundle active=false; không giả đã có release runtime pack |
| `src/App.tsx`, `App.test.tsx` | UI 10_000ms, abort fetch, bỏ late result và giữ panel/projectName; native 30s không tự đổi UI timeout |

Đây là kiểm source tại thời điểm lập plan, không phải baseline tests/runtime. Khi thực thi phải chụp revision/hash/trạng thái mới. Số pass lịch sử trong roadmap không dùng làm kết quả của checkout mới.

## 3. File map trước khi code

Các đường dẫn dưới **là output tương lai** nếu chưa tồn tại. A–E ghi chính xác task tạo file và task sau sửa nó. Không tạo toàn bộ skeleton trước.

| Nhóm | File/chức năng và task sở hữu |
| --- | --- |
| Contracts | A-04: `backend/geoai/contracts/native.py`, registry/exporter, `tests/contracts/test_native_ledger.py`, fixture `tests/fixtures/contracts/native-ledger.json`; schema chỉ sinh bằng tool |
| Shared I/O | A-01/A-02: `storage/native_io.py` chứa types/protocol/registry; `storage/windows_io.py` adapter; shared resolver/extraction/GC nhận factory |
| Shared owner/process | A-03: `storage/native_owner.py` protocol/OwnershipError, `jobs/process.py` process/proof/factory protocol; Windows wrappers tại `storage/windows_owner.py`, `jobs/native_process.py`; guards giữ nguyên nguồn |
| Rust core | B-01: `src-tauri/src/lib.rs`, `session.rs`, `linux_runtime/mod.rs`, `runtime.rs`; B-02 `identity.rs`, `manager.rs`; B-03 `control.rs`; B-04 `supervisor.rs`, `src/bin/geoai-supervisor.rs` |
| Linux bootstrap | B-05: `storage/linux_bootstrap.py`, sửa root bootstrap; chỉ chứa private inherited FD/native identity validation, không import jobs từ storage |
| Shell/test driver | B-06: `src-tauri/examples/geoai-runtime-harness.rs`, `tests/support/linux_runtime.py`, `tests/support/__init__.py`; B-07: `src/linux_native.rs`, main.rs và session tests |
| Owner/DB observation | C-01: `storage/project_epochs.py`; C-02–C-04: `storage/linux_owner.py`, owner/lifecycle tests |
| Linux files | D-01: `storage/linux_syscalls.py`, `linux_io.py`; D-02/D-03 bổ sung read/snapshot/write/finalize, I/O tests |
| Worker process | D-04: `jobs/linux_process.py`, worker bootstrap/entry và transport injection; D-05: platform composition trong root/worker entry |
| Integration | E-01–E-04: `tests/support/ubuntu_foundation.py`, `ubuntu_foundation_driver.py`, `ubuntu_foundation_scenarios.py`, `test_linux_publish.py`, `test_ubuntu_foundation.py`; driver chạy trong API child, outer unittest chỉ harness; mở rộng owner/session/lifecycle và backup/restore fixture |
| Tooling/provenance | A-05: `tools/ubuntu_foundation_preflight.py`, `tools/ubuntu_foundation_check.py`, `tests/architecture/test_foundation_runner.py`; E-05 mở rộng runner và docs/check matrix |

Prefix Python rút gọn trong bảng là `backend/geoai/`. Prefix Rust là `apps/desktop/src-tauri/`. Dùng catalog để tra signature; file map không cấp quyền mở arbitrary path.

## 4. Quy trình cho mỗi task

1. Đọc input task và Interfaces của task trước; xác minh file có thật và API chưa drift. Nếu mâu thuẫn spec/source, ghi đúng đoạn và dừng **phần phụ thuộc**, không tự hạ invariant.
2. Chụp diff/status mới; chỉ sửa file allowlist của task và test/doc liên quan đã nêu. Không stash/reset/clean worktree đang dirty; khi cần isolation dùng skill using-git-worktrees ở thời điểm thực thi và chuyển đúng thay đổi chưa commit cần thiết.
3. Viết test theo tên/assertions đã chỉ; chạy riêng để chứng minh FAIL đúng lý do thiếu behavior, không do sai interpreter/import test harness.
4. Thực hiện từng code step; chạy test mục tiêu, rồi regression nêu trong task. Không lặp full suite sau mỗi edit nhỏ nếu chưa có lý do.
5. Self-review diff theo global constraints và Review Focus; đổi schema thì sinh/check artifact cùng task.
6. Ghi handoff theo mẫu catalog, link log có redaction; checkpoint commit riêng khi workflow Git hiện tại cho phép. Không `git add .`; chỉ stage file task, không kéo thay đổi có sẵn vào commit.

**Gói tối thiểu để giao AI:** prompt mẫu + SPEC-010/profile/interface + plan tổng + catalog + một task. Nếu không đủ context, giảm xuống một substep của chính task đó và giữ cùng Interfaces; không xóa acceptance để rút context.

**Đơn vị gen nhỏ nhất:** các Step là thứ tự trong task, không phải yêu cầu gen cả task một lần. Với Step liệt kê nhiều test/symbol, làm từng test theo thứ tự: thêm một ca đỏ → chạy đúng lệnh → implement một callable hoặc một branch cần cho ca đó → chạy green → mới sang ca tiếp. Test helper chỉ tạo khi ca đó cần, không tạo mọi class/method trống trước. Không chuyển task tiếp nếu còn test thuộc deliverable hiện tại đỏ; nếu môi trường thiếu, handoff partial với đúng phần chưa chạy.

## 5. Lệnh và cách đánh giá kết quả

Mọi lệnh dưới là **lệnh thực thi tương lai**, không chạy trong phiên lập plan. CWD mặc định root repo; Python là interpreter cô lập đã resolve thật. Trong PowerShell đặt `$env:PYTHONPATH = 'backend'` trước; Bash đặt `export PYTHONPATH=backend`. Test unit dùng unittest hiện có, không tự thêm pytest.

```bash
python -m pip install -e '.[api,test,db]'
python tools/export_contract_schemas.py --check
python tools/export_api_client.py --check
python -m unittest discover -s tests/contracts -v
python -m unittest discover -s tests/jobs -v
python -m unittest discover -s tests/storage -v
python -m unittest discover -s tests/catalog -v
python -m unittest discover -s tests/integration -v
python -m unittest discover -s tests/architecture -v
npm --prefix apps/desktop ci
npm --prefix apps/desktop test
npm --prefix apps/desktop run typecheck
npm --prefix apps/desktop run build
```

`pip install` chỉ trong môi trường task cô lập, không sửa Python hệ thống; không chạy lại khi dependency đã đủ. Lỗi mạng/dependency ghi nguyên nhân đã lọc; không thêm fallback package hoặc tắt TLS. Patch Python/Node/Rust/crates được khóa từ resolver/executor thật, không đặt số tưởng tượng.

Sau B-01 có target Rust, chạy từ root:

```bash
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --bin geoai-supervisor
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --example geoai-runtime-harness
npm --prefix apps/desktop run tauri -- dev
npm --prefix apps/desktop run tauri -- build --no-bundle
```

Hai lệnh Tauri cần desktop/runtime resources đã chuẩn bị trong B-07/E-04. Build release không bundle chưa là `.deb` hoặc G3. Trên Windows supervisor binary Linux không được chạy; cfg giữ regression Windows. Cargo lib tests không chứng minh WebKitGTK được khởi tạo đúng.

Runner A-05/E-05 tạo báo cáo từng suite với `pass/fail/skip/not_run`, test count, skips/reasons, exit code, environment/hash và log đã lọc. **Không** dựa mỗi exit code 0: unittest exit 0 khi mọi ca native bị skip cũng chưa là nghiệm thu native. Thiếu systemd/desktop chỉ chặn tầng đó, không chặn portable contracts/core.

## 6. Coverage và điều kiện bàn giao

| SPEC suite | Task thực hiện | Điều kiện bằng chứng |
| --- | --- | --- |
| 010-T01 | A-01/A-02/A-03, D-05, E-05 | Import isolation và factory selection; Windows native regression riêng |
| 010-T02 | A-04 | Pydantic/registry/fixture/export/check, không nới SessionDescriptor/LaunchPacket/capabilities |
| 010-T03 | B-03/B-05/B-06/B-07, E-04 | Rust/Python negative tests + WebKitGTK dev/production thật |
| 010-T04 | C-01/C-02/C-03/C-04, E-03 | Locks/journal/epoch/recovery trên project/process thật |
| 010-T05 | B-02/B-04/C-04/D-04, E-03 | Crash/descendants/EOF/pidfd và fail-closed khi không chứng minh dừng |
| 010-T06 | A-03, D-04 | Packet/FD framing/stdout/stderr/deadline và existing protocol regression |
| 010-T07 | D-01/D-02/D-03/D-05 | Files/FD/mount race/sentinel thực, external positive |
| 010-T08 | D-03/E-01/E-02/E-03 | Native stop + byte isolation + SQLite fencing/crash |
| 010-T09 | D-05/E-01/E-03/E-04/E-05 | End-to-end process/files/DB, retry/reopen/backup/restore |

UB-01–13 ghi subcase theo suite; UB-14 chỉ regression fixture có thật, UB-15–20 chưa được đóng bởi plan này. SSE/Range chỉ kiểm route có thật khi thực thi, hiện API chỉ metadata GET; không tạo route giả để đủ checkbox.

Khi kết thúc implementation: log hai LTS, filesystem/cgroup/user manager, Rust/Python/Node/dependency locks, fixture/source hashes, Windows checks và coverage table. X11/Wayland, dev/production tách record. `not_run/skip` còn ở acceptance bắt buộc → ghi partial và không đóng SPEC-010; source đã gen vẫn bàn giao được với giới hạn đó.

## 7. Trạng thái plan và bước tiếp theo

Kết quả self-review/kiểm tài liệu ở [hồ sơ lập plan](../../evidence/ubuntu-plan-2026-11-10/review.md). Trạng thái thực thi A-01–E-05 ban đầu đều chưa bắt đầu; checkbox trong các plan là checklist triển khai tương lai, không là checkbox đã kiểm tài liệu.

Khuyến nghị giao từng task tuần tự, dùng implementer có context nhỏ; review riêng các thay đổi native identity/FD/owner/publish trước bước tiếp theo. Người điều phối giữ catalog/handoff và chặn lệch signature. Nếu dùng Superpowers subagent-driven-development thì áp dụng skill đó **khi thực thi**, không spawn implementer trong phiên chỉ lập plan.
