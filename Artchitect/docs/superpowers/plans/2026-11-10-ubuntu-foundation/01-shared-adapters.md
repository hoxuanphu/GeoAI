# Shared Adapters and Private Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shared code chạy qua interface có Windows implementation thật; ledger Linux có kiểu/fixture/exporter trước khi native writer dùng.

**Architecture:** Tách protocol/value/error khỏi concrete adapter, inject factory ở boundary. Registry nội bộ giữ danh tính root được cấp; Protocol hoặc isinstance Protocol không tự cấp quyền. Chưa cung cấp Linux execution bằng mock.

**Tech Stack:** Python 3.12, unittest/Pydantic/SQLAlchemy, Windows native regression, Python tooling.

**Spec:** [SPEC-010](../../../specs/010-ubuntu-foundation.md), [interface spec](../../../platforms/ubuntu/ubuntu-adapter-interfaces.md), [plan tổng](../2026-11-10-ubuntu-foundation.md), [catalog](interfaces-and-handoff.md).

## Global Constraints

Áp dụng toàn bộ G-01–G-16 trong plan tổng. Đặc biệt schema `0.1.0`, private model chưa là public RPC; CapabilitiesResponse giữ Literal false, RPC bound `1,048,576` byte gồm LF. Native method dùng một absolute monotonic deadline; không đổi semantics Windows deny-write/delete sharing.

## Review Focus

RF-4 ở A-03 kiểm close FD/deadline; RF-5 chuẩn bị URI test tại C-01. A-01 kiểm root giả đủ method vẫn bị từ chối; A-02 kiểm import thật không kéo Windows; A-04 kiểm private model không rò public registry; A-05 kiểm zero-test/all-skip không thành native pass. Các test tương ứng nằm trong steps dưới.

---

### Task A-01: Native I/O protocol và Windows registered factory

**Read:** `storage/windows_io.py` toàn file, `storage/io_resolver.py`, interface spec mục 2/4/5; prefix Python là `backend/geoai/`.

**Files:** Create `backend/geoai/storage/native_io.py`, `tests/storage/test_native_factory.py`; Modify `backend/geoai/storage/windows_io.py`.

**Interfaces:** Consumes NativeRoot hiện có. Produces NativeIdentity/StorageIOError/ExternalRegistration/NativeReader/NativeRoot/NativeIOFactory ở catalog; thêm `WindowsIOFactory` và registered root wrapper tại windows_io. Legacy `windows_io.NativeRoot` tiếp tục tồn tại cho native tests cũ; value/error re-export từ native_io để chỉ một định nghĩa.

- [ ] **Step 1: Viết test registry và deadline đỏ.** Trong `NativeFactoryTests.setUp`, dùng temp directory và WindowsIOFactory khi OS Windows; tests thuần dùng explicit unit fake registry tách lớp, không gọi fake là native proof. Viết assertions sau:

```python
def test_protocol_shape_does_not_register_a_root(self):
    with self.assertRaisesRegex(StorageIOError, 'unregistered_root'):
        self.factory.require_root(self.lookalike_root, purpose='publication')

def test_read_root_cannot_be_used_for_publication(self):
    root = self.factory.open_registered_root('root:read', self.directory, purpose='read')
    with self.assertRaisesRegex(StorageIOError, 'root_purpose_mismatch'):
        self.factory.require_root(root, purpose='publication')
```

Thêm `test_remaining_budget_is_not_reset_between_calls`: fake clock từ 100 → 104, absolute deadline 110; legacy calls nhận remaining 10 rồi 6, không đều 10. Root closed bị require_root từ chối; registry giữ strong refs, không chỉ cache `id()` có thể reuse.

- [ ] **Step 2: Chạy test đỏ.** `python -m unittest discover -s tests/storage -p test_native_factory.py -v`. Expected fail thiếu native_io/WindowsIOFactory hoặc behavior, không skip hết vì đặt nhầm decorator cả class.
- [ ] **Step 3: Tạo types/protocol và factory.** Copy method shape từ interface spec, không import OS adapter trong native_io. WindowsIOFactory tạo root wrapper có purpose/registry identity; read-purpose root tự refuse create/move/delete, không chỉ dựa caller đã gọi require_root; staging/publication có đúng quyền nội bộ cần thiết. Wrap legacy methods để chuyển absolute deadline sang remaining seconds, giữ Win32 open/share/fsync/rename behavior. `open_external(...)` mở đúng registration và trả reader giữ root đến close; ownership reader close idempotent. Lỗi chỉ reason code.
- [ ] **Step 4: Kiểm Windows thật.** Chạy test mới và `python -m unittest discover -s tests/storage -p test_windows_io.py -v`. Native cases phải chạy trên Windows; Linux chỉ pass các unit cases và ghi native chưa kiểm. Assertions thêm source thay đổi/deny-write/close-root-còn-reader không bị yếu đi.
- [ ] **Step 5: Checkpoint và handoff A-01.** Ghi class/module exports, nơi chuyển duration → absolute/remaining, test counts. Commit đề xuất `refactor(storage): introduce registered native IO factory` với đúng ba file task; không tick 010.1.

### Task A-02: Shared resolver/extraction/GC/publisher nhận factory

**Read:** toàn bộ `storage/io_resolver.py`, `extraction.py`, `gc.py`, `jobs/publisher.py` và tests tương ứng; A-01 handoff.

**Files:** Modify bốn source trên, `tests/storage/test_worker_io.py`, `test_extraction.py`, `test_publisher_io.py`, `tests/integration/test_job_recovery.py`; Create `tests/architecture/test_native_adapters.py`. Test fixture callsites khác chỉ sửa khi `rg` xác nhận đang dựng các class được thay.

**Interfaces:** Consumes NativeIOFactory A-01. Produces `WorkerIOResolver(registry, managed_roots, external_registrations, *, io_factory)`, `extract_zip(..., *, io_factory, <các keyword cũ>)`, `DisposableCollector(repository, disposable_root, *, policy_id, io_factory)`, `Publisher(..., *, validator, io_factory)`. Giữ ExternalRegistration import cũ qua re-export; mọi public `deadline_seconds` cũ chuyển một lần sang absolute deadline trước vòng lặp, không truyền duration xuống native protocol.

- [ ] **Step 1: Viết test đỏ import và authorization.** Architecture test chạy subprocess fresh Python import `geoai.storage.io_resolver`, `extraction`, `gc`, `geoai.jobs.publisher`, rồi kiểm sys.modules:

```python
self.assertNotIn('geoai.storage.windows_io', loaded_modules)
self.assertNotIn('geoai.storage.windows_owner', loaded_modules)
self.assertNotIn('geoai.jobs.native_process', loaded_modules)
```

Chạy trên Windows và Linux để bắt import vô điều kiện, không chỉ test os.name. Thêm `test_unregistered_root_is_rejected_even_with_protocol_methods`, `test_external_open_uses_factory_registration`, `test_zip_copy_uses_one_deadline`; factory spy phải là unit fake có đăng ký rõ.
- [ ] **Step 2: Chạy đỏ.** `python -m unittest discover -s tests/architecture -p test_native_adapters.py -v`; expected fail imported Windows module. Chạy targeted storage tests để ghi behavior trước sửa.
- [ ] **Step 3: Thay concrete import/check và cấp dependency.** Value/error từ native_io, `io_factory.require_root(..., purpose=...)` trước I/O; managed roots read, extraction staging, publisher output publication. External không tự `NativeRoot(path.parent)` trong shared resolver mà gọi factory.open_external. Không nhận root/factory từ JSON/RPC. GC chỉ root disposable đã đăng ký, không xóa source/project cả cây.
- [ ] **Step 4: Sửa deadline callsites và fixtures.** Bổ sung keyword-only `deadline_seconds=60`/`cancelled=lambda: False` ở operation boundary chưa có budget như Publisher.publish/Collector.collect, ghi rõ giá trị kỹ thuật kế thừa default I/O hiện tại; tạo một deadline cho toàn operation. Không đổi retry/business budget. Cập nhật Windows fixture composition tạo roots từ cùng WindowsIOFactory; không sửa assertions hoặc auto-register arbitrary object trong require_root. Fake unit tests khai báo registry của riêng test.
- [ ] **Step 5: Chạy green/regression.** `python -m unittest discover -s tests/architecture -v`, sau đó suite storage và integration hiện có. `rg -n 'windows_io|windows_owner|native_process|isinstance'` trên bốn shared source để tự kiểm còn concrete dependency nào. Publisher comment deny-write đổi thành mô tả adapter-specific; Linux test còn chưa có là not_run.
- [ ] **Step 6: Checkpoint A-02.** Handoff danh sách callsites đã đổi và default technical deadline. Commit `refactor(storage): inject native IO into shared services`; task này chưa yêu cầu Linux file adapter.

### Task A-03: Process/owner protocol và Windows transport adapter

**Read:** `storage/guards.py`, windows_owner acquire_writer/recovery_evidence, toàn native_process/transport, worker bootstrap; A-01/A-02.

**Files:** Create `backend/geoai/storage/native_owner.py`, `backend/geoai/jobs/process.py`, `tests/jobs/test_process_factory.py`; Modify `storage/windows_owner.py`, `jobs/native_process.py`, `jobs/transport.py`, existing Windows transport/native process tests và architecture test.

**Interfaces:** Produces protocols/error/factory và WorkloadStopEvidence trong catalog. Windows wrapper `WindowsExecutionOwner` ánh xạ acquire_project → legacy acquire_writer và giữ writer hiện tại cho recovery_evidence. `WindowsProcessFactory.launch_worker(...)` chứa launch-pipe/handle logic tách từ transport, gọi legacy ManagedProcess.launch; adapter quản lý duration/absolute boundary. `WorkerTransport.launch(executable, packet, *, process_factory, owner, bootstrap_timeout=10)` giữ request/event framing hiện có.

- [ ] **Step 1: Viết test đỏ shape/behavior.** Dùng unittest fake clock/factory có kiểm soát, không mock OS proof trong native acceptance:

```python
self.assertEqual(factory.calls[0].packet.start.attempt, packet.start.attempt)
self.assertEqual(factory.calls[0].deadline, 110.0)  # clock=100, timeout=10
self.assertEqual(process.stdin_frames[0]['method'], 'capabilities')
```

Thêm `test_transport_import_does_not_load_windows_adapter`, `test_partial_bootstrap_failure_closes_only_owned_fds`, `test_expired_deadline_does_not_spawn`, `test_stop_evidence_rechecks_bound_process_and_attempt`. Fake pipe allocator ghi close từng owned FD, tạo reuse number sau close để chứng minh finally không close lại. Native Windows test vẫn phải chứng minh Job Object và handle allowlist thật.
- [ ] **Step 2: Chạy đỏ.** `python -m unittest discover -s tests/jobs -p test_process_factory.py -v`; expected missing factory/protocol hoặc concrete import assertion fail.
- [ ] **Step 3: Tạo wrappers, di chuyển launch logic.** NativeProcessError chuyển sang jobs/process.py rồi native_process import/re-export chính class đó; OwnershipError cũng chuyển/re-export từ native_owner, không tạo hai class cùng tên làm catch sai. Factory Windows encode bằng jobs.protocol.encode, explicit handle allowlist, wait cleanup bounded, không token/packet vào argv/env. `ProcessFactory.stop_evidence` trả object giữ native process + owner + project/AttemptKey snapshot; assert_stopped query native Job Object lại và đối chiếu binding, không snapshot bool. Chưa cho publisher consume proof trong task này.
- [ ] **Step 4: Inject factory vào transport và cập nhật callsites Windows.** Transport chỉ delegate launch và giữ process, correlation/queues/thread behavior cũ. `ManagedProcess` wrapper chuyển deadline tuyệt đối về duration cho legacy .wait/.group_stopped/.terminate_group. Không đổi các hàm Windows cũ nhận duration rồi truyền absolute value vào chúng. Worker bootstrap Linux còn ở D-04.
- [ ] **Step 5: Green/regression.** Suite jobs và architecture; trên Windows `python -m unittest discover -s tests/integration -p test_native_process.py -v`, `... -p test_worker_transport.py -v`, `... -p test_native_owner.py -v`. Test lỗi cleanup không được nuốt để báo stopped; test owner.close còn live group giữ quyền như cũ.
- [ ] **Step 6: Checkpoint A-03.** Handoff mapping names/signatures/timeout conventions. Commit `refactor(jobs): isolate native process and owner adapters`; giữ guards.py là nguồn protocol lifetime duy nhất.

### Task A-04: Private Pydantic ledger và generated schema

**Read:** contracts.md, contracts/common.py/access.py/__init__.py, exporters, native profile mục 4; source hiện tại chưa native.py.

**Files:** Create `backend/geoai/contracts/native.py`, `tests/contracts/test_native_ledger.py`, `tests/fixtures/contracts/native-ledger.json`; Modify contracts/__init__.py, `tools/export_contract_schemas.py`, contracts.md; Generate `schemas/contracts-v0.1.0.json`. API client/OpenAPI chỉ sửa bằng exporter nếu có delta hợp lệ; ledger không phải HTTP DTO.

**Interfaces:** `LinuxOwnerGeneration(ValueModel)`, `LinuxOwnerLedger(Contract)` với fields đúng native profile. `PRIVATE_NATIVE_MODELS` riêng; `encode_ledger(value: LinuxOwnerLedger) -> bytes`, `decode_ledger(data: bytes) -> LinuxOwnerLedger` chịu inclusive LF/byte limit và strict JSON. Không syscall/OS probe trong contracts.

- [ ] **Step 1: Viết fixture/test đỏ.** Fixture synthetic 1 generation, UUID/hex hợp lệ, epoch=7/high_watermark=7, project/root/cgroup identities Linux encoding, created_at UTC. Assertions:

```python
self.assertEqual(decode_ledger(encode_ledger(value)), value)
self.assertTrue(encode_ledger(value).endswith(b'\n'))
self.assertIn('LinuxOwnerLedger', PRIVATE_NATIVE_MODELS)
self.assertNotIn('LinuxOwnerLedger', CONTRACT_MODELS)
self.assertNotIn('LinuxOwnerLedger', WIRE_MODELS)
```

Thêm unknown field/version, naive time, bool epoch, epoch 0, duplicate owner/epoch, watermark thấp, record trống/1025 records, bytes >1_048_576 gồm LF, trailing JSON/NaN/duplicate keys. Test 1024 records có thể vượt bytes: dùng fixture ngắn đủ giới hạn, kiểm hai budget độc lập. SessionDescriptor/LaunchPacket/capabilities schemas giữ nguyên nội dung definitions tương ứng.
- [ ] **Step 2: Red.** `python -m unittest discover -s tests/contracts -p test_native_ledger.py -v`; missing native models là expected red.
- [ ] **Step 3: Implement types/codec/registry.** Tái dùng Identifier/PositiveInt/FileIdentity/UtcDateTime; generation chỉ value metadata, native observer sẽ kiểm cgroup/root actual sau. Codec kiểm encoded limit trước parse, strict JSON và một LF cuối; serializer không thêm thông tin secret. Schema exporter merge private native và thêm `x-geoai-registries.private_native`, không đưa vào durable/wire. Export cả root model và nested definition nhất quán registry tests.
- [ ] **Step 4: Generate/check thật.** `python tools/export_contract_schemas.py`; `python tools/export_contract_schemas.py --check`; `python tools/export_api_client.py --check`; `python -m unittest discover -s tests/contracts -v`. Expected exit0, schema current; API artifact không đổi nếu chỉ private ledger mới. Không sửa JSON/TS tay.
- [ ] **Step 5: Checkpoint A-04.** Cập nhật contracts.md từ “chưa có” thành source thực đã thêm, vẫn chưa native acceptance. Commit `feat(contracts): define private Linux owner ledger`; handoff fixture/schema hash cho C-03.

### Task A-05: Preflight, baseline runner và evidence từng tầng

**Read:** Ubuntu development/packaging, validation matrix, guide testing, pyproject/package scripts; plan tổng mục 5/6.

**Files:** Create `tools/ubuntu_foundation_preflight.py`, `tools/ubuntu_foundation_check.py`, `tests/architecture/test_foundation_runner.py`; Modify Ubuntu guide/testing strategy cho lệnh thật vừa tạo. Evidence mới nằm ngoài source tests tại ngày thực thi, không ghi đè lịch sử.

**Interfaces:** `probe_environment() -> dict` trong preflight chỉ allowlist OS/arch/kernel/glibc/FS/cgroup/user-manager/interpreter/toolchain/package versions, không dump env/credentials. Runner CLI `--layer portable --output <directory>` chạy unittest/existing exporter/frontend checks và ghi `results.json`; layer native/desktop thêm ở E-05 sau khi suite có thật. `--output` directory mới hoặc task-owned, từ chối overwrite hồ sơ lịch sử.

- [ ] **Step 1: Test đỏ kết quả runner.** Unit fake command result chứa `exit=0, testsRun=4, skipped=4`; expected status skip, không pass. Zero tests expected fail. exit1 expected fail; thiếu binary expected not_run; unknown layer fail input, không silently portable. Redaction test dùng synthetic token trong stderr và assert output không chứa token.
- [ ] **Step 2: Red.** `python -m unittest discover -s tests/architecture -p test_foundation_runner.py -v`.
- [ ] **Step 3: Implement runner/probe.** Dùng subprocess argv arrays/timeouts, allowlist command và output fields; unittest result ghi counts từ result object/custom runner thay parse chỉ chữ OK. Tách JSON status của suite với status gate; dependency probe không cài máy. Raw stdout descriptor không thuộc allowlisted commands, không bao giờ chạy bootstrap trực tiếp rồi log stdout.
- [ ] **Step 4: Baseline thật.** Trên Windows và từng LTS đã sẵn executor, chạy `python tools/ubuntu_foundation_preflight.py --output <task-owned-dir>` rồi `python tools/ubuntu_foundation_check.py --layer portable --output <task-owned-dir>`. `--output` phải thay bằng path mới cụ thể trước chạy. Restore dependency cô lập khi được yêu cầu triển khai, ghi resolve/lock thật. Thiếu LTS thì ghi not_run chứ không fabricate environment.
- [ ] **Step 5: Green/handoff A-05.** Tests runner + kiến trúc, xem results không secret, ghi baseline fail/skip có sẵn. Commit `test(tooling): record Ubuntu foundation baseline by layer`. Đóng 010.1 chỉ khi yêu cầu mốc ở plan tổng đủ bằng chứng; nếu chưa, giữ partial và B vẫn có thể viết/test phần đủ dependency.
