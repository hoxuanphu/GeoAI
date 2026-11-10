# Ubuntu Foundation Integration and Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chứng minh process/files/SQLite cùng hoạt động và fencing/cancel/recovery không bị phá trên hai LTS, giữ Windows regression.

**Architecture:** Test driver chạy **trong API child của unit**, dùng cùng production composition/coordinator/repository, không tạo production job route. Python unittest bên ngoài chỉ điều khiển harness/quan sát kết quả đã lọc, không giả làm native API để giữ owner hoặc spawn worker ngoài cgroup.

**Tech Stack:** unittest, Rust test-only harness, SQLAlchemy/Alembic thật, native FD/cgroup/pidfd, Tauri/WebKitGTK và existing frontend checks.

**Spec:** [SPEC-010](../../../specs/010-ubuntu-foundation.md), [validation matrix](../../../platforms/ubuntu/ubuntu-validation-matrix.md), [plan tổng](../2026-11-10-ubuntu-foundation.md), [catalog](interfaces-and-handoff.md).

## Global Constraints

G-01–G-16 áp dụng. Worker/candidate không ghi DB; publication chỉ transaction DB active token/state/uniqueness. Native stop observation không tự `confirm_stopped()` trước publish. `.deb`, model/GIS/business gates, live provider, broad support matrix ngoài scope; pass/skip/not_run tách đúng.

## Review Focus

RF-2 là E-01; E-02 kiểm cancel giữa rename và commit, worker còn writable FD; E-03 kiểm orphan/backup/recovery và WAL; E-04 kiểm actual WebKit dev/production, UI timeout/retry; E-05 kiểm native required tests không bị all-skip mà đóng mốc. Tests ở tasks tương ứng.

---

Các lệnh targeted dùng từ root, sau khi đã set PYTHONPATH theo plan tổng. Khi chạy ở executor đủ điều kiện, required native case phải chạy thật; exit0 với skip không là green acceptance.

| Task | Lệnh targeted đầy đủ | Expected green |
| --- | --- | --- |
| E-01/E-02 | `python -m unittest discover -s tests/integration -p test_ubuntu_foundation.py -v` và `python -m unittest discover -s tests/integration -p test_linux_publish.py -v` | Scenarios process/files/SQLAlchemy thật pass, counts >0 |
| E-03 | Hai lệnh E-01 và `python -m unittest discover -s tests/integration -p test_linux_owner.py -v`, `python -m unittest discover -s tests/integration -p test_linux_lifecycle.py -v` | Crash/reopen/pin/lease cases pass, unsupported fault cases ghi riêng |
| E-04 | `python -m unittest discover -s tests/integration -p test_linux_session.py -v`, `npm --prefix apps/desktop test`, `npm --prefix apps/desktop run typecheck`, `npm --prefix apps/desktop run build` | Unit/DOM checks pass; WebKit dev/production evidence bổ sung riêng |
| E-05 | `python -m unittest discover -s tests/architecture -p test_foundation_runner.py -v`, `python tools/ubuntu_foundation_check.py --layer all --output .cache/ubuntu-foundation-final` | Tooling pass và report từng required suite/env không thiếu |

Output dir cuối là ví dụ task-owned: trước chạy kiểm directory mới/chưa chứa evidence cũ; nếu đã tồn tại chọn tên run mới, không overwrite. Build test scenario sau E-01 bằng `cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --features runtime-test-harness --target-dir .cache/ubuntu-foundation-harness --bin geoai-supervisor --example geoai-runtime-harness`; harness dùng đúng executable trong target-dir này từ native config. Production build E-04 dùng target/build không feature để không lẫn artifact test.

### Task E-01: Foundation driver trong API và publisher stop proof

**Read:** D-05 composition, B-06 harness, toàn repository claim/publish/confirm_stopped, current test_job_recovery fixture. Giữ JobSpec/manifest fixture hiện có, chỉ thay trusted native root/owner/attempt/hash phù hợp.

**Files:** Create `tests/support/ubuntu_foundation.py`, `tests/support/ubuntu_foundation_driver.py`, `tests/support/ubuntu_foundation_scenarios.py`, `tests/integration/test_ubuntu_foundation.py`; Modify publisher.py/transport.py/test_linux_publish.py, Rust supervisor/example **test-only** scenario wiring.

**Interfaces:** FoundationFixture trong catalog, chỉ khởi tạo **bên trong verified API process**. `LinuxRuntimeHarness.run_scenario(name: str) -> dict` nhận allowlisted scenario và trả assertion/result/environment không chứa descriptor/token. `WorkerTransport.stop_evidence()` trả bound native proof; Publisher thêm required keyword workload_evidence, giữ validator/io_factory.

- [ ] **Step 1: Viết test đỏ success/order.** Trong support scenarios, `test_stop_observation_does_not_revoke_publish_token` và `test_real_worker_candidate_commits_exact_bytes` thực hiện:

```python
fixture.run_worker_to_candidate()
fixture.stop_worker_observed()  # native proof; KHÔNG repo.confirm_stopped
self.assertEqual(fixture.repo.get(job_id).state, 'running')
result = fixture.publish('publication:fixture')
self.assertEqual(result.state, 'succeeded')
self.assertEqual(fixture.read_artifact(), FIXTURE_ARTIFACT_BYTES)
fixture.confirm_stopped()      # sau DB commit mới release compute allocation
self.assertTrue(fixture.repo.get(job_id).stop_confirmed)
```

Outer test_ubuntu_foundation gọi run_scenario, assert scenario đúng ID/invocation, assertions chạy >0/no skip/error và artifact hash từ **đọc actual bytes**. Không import fixture vào outer test rồi acquire native owner từ process ngoài unit.
- [ ] **Step 2: Red.** `python -m unittest discover -s tests/integration -p test_ubuntu_foundation.py -v`; expect missing native driver/proof integration, không native skip khi executor đủ điều kiện.
- [ ] **Step 3: Implement test-only driver.** Feature Cargo `runtime-test-harness`, build debug riêng; release build bật feature phải compile_error và E-05 kiểm release binary không có fixture flags. Trong feature này supervisor chọn **registry scenario cố định** và entry `tests.support.ubuntu_foundation_driver`, không arbitrary script/command; trusted debug config thêm repo root chứa tests vào PYTHONPATH bên cạnh backend, production không thêm tests path. API driver validate inherited owner rồi khởi Uvicorn/descriptor theo production bootstrap, cùng process ghép FoundationFixture và chạy scenario. Project temp ext4 do driver tạo, result/milestone dưới runtime test dir theo invocation; result chỉ assertion/count/hash/status. Production supervisor không parse --fixture-scenario, Tauri release không bundle example/tests. Không thêm HTTP fixture route hoặc FD từ shell socket.
- [ ] **Step 4: Implement fixture và publish proof.** Migrate temp DB qua real guard → ProjectRepository.open → enqueue/claim → fresh context/packet update owner/epoch/AttemptKey/hash → factory worker → capabilities/start → candidate. Retain input leases/grants cho coordinator đọc manifest sau worker exit; revoke worker dispatch/start quyền, không nhầm đóng coordinator read registry trước publish. Stop proof query native census trước finalize và trước commit; caller-created bool rejected. Sau publish succeeded mới confirm_stopped; failure/cancel path fail/revoke theo policy, native stop rồi confirm, retry tạo attempt mới.
- [ ] **Step 5: Green/Windows regression.** Target foundation/publish suites, existing test_job_recovery Windows cập nhật proof factory để cùng Publisher API. Không mock SQLAlchemy/finalize; kiểm DB rows/publication unique/inventory/hash. Commit `feat(jobs): publish only after native workload stop observation`; handoff driver feature isolation và exact transaction order.

### Task E-02: Cancel/retry/stale candidate và writer-FD races

**Files:** Extend tests/support/ubuntu_foundation_scenarios.py, test_linux_publish.py/test_ubuntu_foundation.py; Modify publisher/transport/composition chỉ nếu test phát hiện behavior sai, không sửa repository state machine rộng ngoài invariant.

**Interfaces:** FoundationFixture + workload proof E-01. Scenario synchronization bằng events/barriers hoặc private test milestone files gắn invocation; không sleep để đoán timing. Hooks chỉ trusted unit/test injection, không production wire flag.

- [ ] **Step 1: Test đỏ các race quyết định.** `test_publish_is_blocked_while_worker_or_grandchild_has_writer_fd`, `test_cancel_after_rename_before_commit_leaves_unserved_orphan`, `test_retry_uses_new_attempt_token_and_context`, `test_cross_project_or_old_attempt_candidate_is_rejected`, `test_cancel_after_commit_keeps_succeeded_publication`, `test_second_compute_not_claimed_before_confirm_stopped`.

```python
with self.assertRaises(PublicationError):
    fixture.publish('publication:early')  # workload còn live
self.assertIsNone(fixture.repo.get_publication(job_id))
# Case cancel tại barrier sau rename:
self.assertIsNone(fixture.repo.get_publication(job_id))
self.assertTrue(fixture.orphan_files_exist())
self.assertFalse(fixture.artifact_is_available_from_repository())
```

Hai helper cuối là scenario-local read-only kiểm output dir và repository inventory, không thêm production API để liệt kê paths.
- [ ] **Step 2: Red.** Target Linux publish/foundation; nếu code đã đúng, chứng minh regression test bằng fault injection bypass duy nhất check liên quan trong test double của boundary, rồi restore; không commit code weakened. Không bắt buộc sửa source khi test đã green đúng.
- [ ] **Step 3: Hoàn thiện proof/ordering khi cần.** Child exit/EOF hoặc event completed không đủ; census gồm worker/grandchild → refuse. Stale key mismatch đủ job_id/attempt_id/generation_token + owner/epoch/project. Grant candidate gắn đúng context/staging; native observation không sửa DB token trước success path. Retry fail/revoke/stop-confirm → backoff → new claim/context/nonce; old context không resurrect.
- [ ] **Step 4: Chạy deterministic race regression.** Lặp mỗi schedule được kiểm soát ít nhất ba lần để phát hiện resource leak; không thay test bằng random stress không có seed. Ghi candidate/attempt **IDs tổng hợp**, không token trong log. Kiểm second compute bị block đến repo.confirm_stopped dù publish đã succeeded.
- [ ] **Step 5: Green/checkpoint E-02.** Repo/jobs/transport/publish suites, Windows same race regression. Commit `test(jobs): pin Linux cancel retry and publication races`; handoff những source fix thật, không claim safety từ test order mocks.

### Task E-03: Crash boundaries, recovery, backup/restore và GC

**Files:** Extend scenarios/foundation/publish/owner/lifecycle tests; Modify Linux byte adapter/recovery composition/backup fixture helper nếu cần. Reuse repository backup/restore/migration APIs hiện có, không thêm backend repository thứ hai.

**Interfaces:** Fault points là registry test-only: before_file_fsync, after_file_fsync, after_rename, after_directory_fsync, before_db_commit, after_db_commit; journal_after_append_before_reconcile. `FoundationFixture` helper backup bundle tạo DB backup + artifact inventory/hash bằng adapter, không export owner ledger/token/context.

- [ ] **Step 1: Test đỏ crash matrix.** `test_crash_before_commit_never_serves_orphans`, `test_crash_after_commit_reconciles_missing_artifact`, `test_append_b_then_crash_recovers_owner_a`, `test_backup_restore_quiescent_bundle_rebases_epoch`, `test_gc_respects_pins_and_old_owner_leases`, `test_corrupt_ledger_recovery_requires_trusted_provenance`.

```python
self.assertEqual(repo.get(job_id).state, expected_state_after_recovery)
self.assertEqual(repo.get_publication(job_id) is not None, expected_committed)
self.assertEqual(hash_file(sentinel_outside_staging), sentinel_hash)
self.assertGreater(new_writer.owner_epoch, maximum_epoch_in_restored_db)
```

Test missing artifact **sau committed publication** phải đánh unavailable, không recreate bytes giả để giữ available. Precommit orphan không được promote. Backup có active foreign-machine attempt/lease bị refuse, không claim native stop máy nguồn.
- [ ] **Step 2: Red/native fault run.** Dùng harness pidfd kill **đúng** API/supervisor/testworker tại milestone, reopen fresh invocation/project guard. Result mất vì API killed không được coi driver test pass; outer test phải quan sát actual persistent DB/files/journal qua recovery scenario kế tiếp trong native API mới. Process kill chỉ crash-process proof.
- [ ] **Step 3: Fix recovery/availability.** Native observer old generation trước reconcile attempt/lease; preserve A records; directory/file fsync và DB transaction order đúng. Reopen chạy inventory verify, artifact missing/hash wrong → unavailable; không serve dựa tồn tại file. GC chỉ sau no compute + pin/lease policy và verified delete; không timeout-delete staging/caches tất cả để “sạch”.
- [ ] **Step 4: Backup/restore tích hợp.** Sau quiescent native stop, repo.backup dùng online SQLite backup gồm WAL committed; bundle fixture copy chỉ immutable publication inventory/hash. Restore sang root mới qua writer guard/migration API hiện có và verify inventory, re-register native roots/FileIdentity, epoch cao hơn DB. Journal của máy nguồn không mang vào bundle như quyền native. Nếu source project chưa quiescent thì từ chối, ghi waiting recovery; không sửa record active bằng tay.
- [ ] **Step 5: Green/checkpoint E-03.** Matrix real files/SQLite/process, cross-volume fixture đúng EXDEV, fault-result/logs từng boundary. Commit `test(storage): verify Linux crash recovery and quiescent restore`; VM reboot/power-loss cần environment riêng, không gắn pass từ kill process.

### Task E-04: WebKitGTK dev/production và native lifecycle desktop

**Files:** Extend test_linux_session/lifecycle/ubuntu_foundation và App.test.tsx nếu thiếu assertion; Modify desktop README, Ubuntu guide/validation matrix bằng link evidence thật. Tauri config/resources chỉ điều chỉnh cho trusted fixture pack, không bật installer release scope.

**Interfaces:** NativeSession B-07 và same SessionDescriptor/API Pydantic. Existing two metadata routes là scope HTTP hiện tại; SSE/Range/loader route chưa có → not_run/out_of_scope theo case, không tạo giả.

- [ ] **Step 1: Test đỏ WebKit boundary hiện có.** `test_webkit_dev_and_production_metadata_authorization`, `test_stale_token_and_wrong_origin_are_rejected`, `test_ui_timeout_retry_preserves_state_and_one_invocation`, `test_close_during_bootstrap_leaves_no_workload`. DOM fake tests bổ trợ timing/state; actual WebKit kiểm origin/CSP/fetch.
- [ ] **Step 2: Chuẩn bị và build thật.** Runtime Python3.12 riêng và resources layout B-01, package/lock thật; `npm --prefix apps/desktop ci`, test/typecheck/build; Cargo lib/supervisor tests. Test-only scenarios dùng build feature riêng; **production smoke build không feature**: `npm --prefix apps/desktop run tauri -- build --no-bundle`. Build resources thiếu là fail/not_run, không dùng test supervisor debug thay kết quả production.
- [ ] **Step 3: Kiểm session thực.** Tauri dev và production WebKit: health/capabilities token header/Host/Origin đúng, wrong/stale/null/duplicate header bị policy từ chối; CORS preflight không trả secret. CSP giữ allowlist hẹp; diagnostic chỉ Origin/Host/scheme/status đã lọc, không Authorization/url query/raw descriptor. Browser-only mode vẫn lỗi handoff rõ, không auto-start metadata API ngoài supervisor.
- [ ] **Step 4: Kiểm desktop lifecycle/session.** Close normal, kill shell, kill supervisor/API/worker, grandchild setsid, connection thứ hai, logout/cross-login cùng UID và hai bản cài trong fixture test account. Mỗi case ghi observed cgroup/FD/pidfd và manager state; queued retry không stop owner hợp lệ. X11/Wayland tách subcase; thiếu display/session type ghi not_run, không suy từ headless test.
- [ ] **Step 5: Green/checkpoint E-04.** Artifact hashes/build provenance/dev-production logs từng LTS và session type. Commit `test(desktop): validate Ubuntu WebKit session and cleanup`; UB-15/GIS/PDF/Prithvi/.deb vẫn ngoài nghiệm thu.

### Task E-05: Runner đầy đủ, Windows regression và bàn giao bằng evidence

**Files:** Extend tools/ubuntu_foundation_preflight.py/check.py và runner tests; Update SPEC-010, roadmap/task-tracker, contracts/resolver/Ubuntu guides theo source thực; evidence mới riêng theo ngày thực thi. Không sửa spec/evidence lịch sử để biến not_run thành pass.

**Interfaces:** Runner layers `portable`, `native`, `desktop`, `all`; output result từng LTS/Windows/subcase. Bổ sung expected-suite registry 010-T01–09 với required/native/desktop tests và counts, không allow all-skip thành pass. Detect release fixture feature leakage qua build flags và binary smoke rejecting --fixture-scenario.

- [ ] **Step 1: Test đỏ closure guard.** `test_all_skip_native_suite_cannot_close_milestone`, `test_missing_lts_or_windows_regression_keeps_partial`, `test_zero_tests_is_failure`, `test_release_binary_rejects_test_scenario_flags`, `test_report_omits_tokens_and_paths_not_needed_for_provenance`.
- [ ] **Step 2: Chạy green tooling.** Runner unit tests + schema/API check, kiểm testcase IDs không bị rename khỏi expected manifest để làm report xanh. Báo cáo required case not_run/skip giữ partial, overall command failure vẫn fail đúng code khi implementation lỗi.
- [ ] **Step 3: Chạy đủ trên môi trường có thật.** Từng Ubuntu22.04/24.04 có ext4/user manager và desktop phù hợp: preflight rồi portable/native/desktop. Trên Windows chạy các đường shared/native đã chạm tới, schemas và frontend; không ép Windows cài D-Bus. Ca làm hỏng/đầy/xóa journal chạy trong test account/VM disposable riêng sau khi baseline lưu; không phá ledger tài khoản đang dùng hoặc auto reset/GC counter để tiếp tục suite. Reboot branch C-04 chỉ nghiệm thu bằng dedicated VM fixture đã lưu journal/project/identity trước reboot và kiểm lại sau reboot; không reboot host người dùng. Power-loss chưa có protocol/environment riêng thì ghi chưa kiểm, không suy từ reboot/process kill.
- [ ] **Step 4: Review toàn diff và traceability.** Đối chiếu SPEC-010 từng invariant/suite với evidence, native/runtime source và actual dependencies; không chỉ text coverage. Kiểm module imports, FD leak, single compute, old token refusal, output ownership, recovery không fabricate. Nếu dùng skill requesting-code-review khi implementation hoàn tất, reviewer đọc final diff/spec; ở đây chỉ ghi yêu cầu tương lai, không cần spawn agent trong phiên lập plan.
- [ ] **Step 5: Bàn giao và checkpoint E-05.** Summary nguồn/code đã làm, pass/fail/skip/not_run, environment limits, remaining UB/gates. Chỉ tick010.1/010.2/010.3 khi đúng điều kiện plan tổng; SPEC-003/004/009 partial và G0–G4 không tự đóng theo foundation. Commit `docs(ubuntu): record foundation verification and remaining gates`; không tự deploy/merge/publish installer.
