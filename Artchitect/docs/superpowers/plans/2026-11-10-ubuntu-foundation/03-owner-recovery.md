# Ubuntu Ownership and Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Một owner/UID, một writer project với epoch bền vững và recovery chỉ sau native stop evidence đúng generation.

**Architecture:** Supervisor giữ flock suốt phiên; API giữ duplicate đã xác minh và project writer. API đọc project epochs trước migration, append generation journal bền vững trước tạo guard/ghi DB; observer không coi journal state là quyền.

**Tech Stack:** Python 3.12, fcntl/proc/pidfd, SQLAlchemy read-only observation, Pydantic private ledger, existing WriterGuard/OwnerStopEvidence.

**Spec:** [SPEC-010](../../../specs/010-ubuntu-foundation.md), [native profile mục 4/5](../../../platforms/ubuntu/ubuntu-native-profile.md), [plan tổng](../2026-11-10-ubuntu-foundation.md), [catalog](interfaces-and-handoff.md).

## Global Constraints

Toàn bộ G-01–G-16. Home lấy `pwd.getpwuid(os.getuid()).pw_dir`; journal không theo HOME/XDG. `max(ledger, Job/Attempt/DependencyLease)+1`, journal1024records/1_048_576bytes gồm LF, không tự GC/reset. Không API LOCK_UN owner FD; project lock theo directory identity, không theo tên.

## Review Focus

RF-3/RF-5 thuộc C-01/C-02. C-03 kiểm crash sau appendB/trước reconcileA và đầy journal; C-04 kiểm boot/invocation/cgroup identity ambiguous và active dependency lease; không deserialize bool làm proof. Bốn task dưới có test cụ thể cho từng trường hợp.

---

### Task C-01: Quan sát epoch project read-only trước migration

**Read:** db_models Job/Attempt/DependencyLease/ProjectMeta, repository _engine/migrate/open/_validate_metadata, migrations current revision; không gọi _engine vì nó PRAGMA journal_mode=WAL và có thể ghi.

**Files:** Create `backend/geoai/storage/project_epochs.py`, `tests/storage/test_project_epochs.py`; Modify contracts/docs chỉ nếu source contract thật thay đổi (task này không yêu cầu).

**Interfaces:** PriorOwner/ProjectEpochState/read_project_epochs trong catalog. Input project root đã được native owner kiểm/lock và nguồn quiescent, database v1 tên `project.sqlite` theo fixture hiện có; source root/project identity do caller cấp, reader không tự cấp WriterGuard. Reader dùng private coherent snapshot gồm main DB và WAL để SQLite không tạo/sửa SHM tại project nguồn; không mở source qua writer engine hoặc backup connection có thể tạo sidecar.

- [ ] **Step 1: Viết SQLAlchemy fixture/tests đỏ.** Dùng schema/migration thật với FixtureGuard **chỉ cho fixture setup**, đóng writer rồi chụp bytes/hash/listdir/mtime trước reader. Tạo Job epoch3, Attempt epoch11, DependencyLease epoch17 (rows hợp lệ quan hệ project), expected max17; active generation tuples phân biệt với historical closed. Test `test_missing_database_is_fresh_without_creating_files`, `test_unknown_revision_or_project_is_rejected`, `test_epoch_reader_sees_committed_wal_without_writes`, `test_unicode_project_uri_and_alias_keep_identity`.

```python
state = read_project_epochs(project_root, 'project:one')
self.assertEqual(state.max_epoch, 17)
self.assertEqual(before_inventory, snapshot_inventory(project_root))
self.assertTrue(any(p.owner_epoch == 17 and p.needs_stop_evidence for p in state.prior_owners))
```

`snapshot_inventory` là local test helper ghi relative names/hash/size/mtime, bao gồm `-wal/-shm`; không dùng chụp DB read qua writer engine để tự thay fixture trong bước reader.
- [ ] **Step 2: Red.** `python -m unittest discover -s tests/storage -p test_project_epochs.py -v`. DB extra thiếu là skip rõ; target executor phải restore DB extra để chạy thật.
- [ ] **Step 3: Implement coherent observation snapshot.** Nếu DB chưa có và không có sidecar/hot journal lạ, trả max0/empty, không tạo DB. Nếu có: dưới precondition native writer lock/quiescent, pin/no-follow source DB và WAL, copy cùng tên sang private temp ngoài project; kiểm source identity/size/hash trước/sau copy và validate snapshot qua SQLite. Copy max64MiB/deadline30s là giới hạn kỹ thuật foundation của helper, không business budget; vượt thì recovery_required, không đọc thiếu WAL. Temp cleanup chỉ đúng directory helper tạo. Snapshot riêng được phép tạo SHM phục vụ SQLite; project nguồn không đổi.
- [ ] **Step 4: Query snapshot read-only.** SQLAlchemy URI read-only/query_only trên snapshot; verify revision `0001_initial`, schema_profile `0.1.0` và project, query max/prior tuples cả Job/Attempt/DependencyLease. Không dùng repository.open/migrate/_engine hoặc `immutable=1`, không copy chỉ main DB. URI escape đúng `#`, `%`, space, Unicode. Hot rollback journal/nguồn còn đổi/WAL lỗi → recovery_required, không checkpoint/xóa WAL/migrate source. Test WAL epoch cao hơn main và inventory nguồn gồm -wal/-shm giữ nguyên, kể cả source WAL có mà SHM chưa có; unknown DB không coi fresh0.
- [ ] **Step 5: Green/checkpoint C-01.** Chạy suite project_epochs và migrations/repository DB regression. Commit `feat(storage): observe project owner epochs without writes`; handoff supported revision/query mode và failure reasons cho C-02.

### Task C-02: Linux owner/project locks và guard lifetime

**Read:** LinuxOwnerBootstrap B-05, guards.py, Windows lifetime tests, native profile4. B-06 harness phải sẵn cho integration thật.

**Files:** Create `backend/geoai/storage/linux_owner.py`, `tests/integration/test_linux_owner.py`. Không gắn owner vào bootstrap ở C-02; D-05 compose usable owner sau khi C-03/C-04 xong.

**Interfaces:** Task này tạo low-level `LinuxOwnerSession.from_inherited(bootstrap)` và `LinuxProjectLock` tại linux_owner.py: `session.lock_project(project_id: str, project_root: Path) -> LinuxProjectLock`, lock có `assert_held()`, `retain()`, `close()` và internal FD/root identity. Đây chưa là guards.WriterGuard; LinuxExecutionOwner/WriterGuard usable được tạo ở C-03 sau durable journal, không stub acquire_project trả dummy epoch.

- [ ] **Step 1: Test đỏ kernel locks.** `test_second_project_or_session_cannot_claim_writer`, `test_unicode_project_uri_and_alias_keep_identity`, `test_owner_fd_not_unlocked_when_api_copy_closes`, `test_unlinked_or_replaced_lock_requires_recovery`, `test_project_lock_lease_prevents_early_close`. Alias test là cùng directory được truy cập qua đường hợp lệ/FD identity khác spelling; symlink path vẫn bị từ chối, không tạo ngoại lệ symlink để test alias.

```python
lease = project_lock.retain()
with self.assertRaises(OwnershipError):
    project_lock.close()
project_lock.assert_held()
lease.close()
project_lock.close()
```

Thêm manager/cgroup identity mất trong assert_held → ownership error, không tiếp tục DB transaction. Test close API duplicate trong child nhưng supervisor còn sống: owner contender vẫn không lấy được flock.
- [ ] **Step 2: Red.** `python -m unittest discover -s tests/integration -p test_linux_owner.py -v`. Phải ghi native case thực chạy hay skip; fake guard unit không đủ.
- [ ] **Step 3: Implement root/lock acquisition.** Từ inherited proof, xác minh UID/canonical runtime/home ancestors owner/mode; root-owned system ancestors có policy riêng hợp lệ, không đòi mọi `/` ancestor owned UID. Project lock O_NOFOLLOW/O_CLOEXEC, flock EX|NB, stable inode/nlink; directory root FD pin/no symlink. Không unlink/recreate lock khi busy hoặc unlock API owner duplicate. Chặn project khác khi writer/retained lease/workload chưa sạch.
- [ ] **Step 4: Implement lock lifecycle.** Internal RLock/state/retains; assert_held kiểm live parent/unit/cgroup/root/project binding. Session/lock có logic độc lập chạy test hết; không thêm test đòi journal/WriterGuard chưa thuộc task. Không tạo usable WriterGuard trước C-03 và không trả dummy owner/epoch. Storage không import bootstrap/jobs.
- [ ] **Step 5: Green/checkpoint C-02.** Native lock/lifetime cases + Windows owner regression. Commit `feat(linux): hold native owner and project writer locks`; handoff state chưa cấp guard generation cho tới C-03, không bật execution capability.

### Task C-03: Durable generation journal và epoch trước mọi ghi project

**Files:** Modify linux_owner.py; Extend test_linux_owner.py; dùng A-04 codec/fixture và C-01 reader, không thêm handwritten JSON schema.

**Interfaces:** LinuxExecutionOwner.from_inherited(bootstrap, *, epoch_reader) bao low-level session C-02; acquire_project trả LinuxProjectWriter thực hiện guards.WriterGuard chỉ sau durable append. owner_id/owner_epoch trước claim lỗi project_not_claimed. Internal helper `_append_generation(project_id, root_identity, state: ProjectEpochState) -> LinuxOwnerGeneration` giữ dưới owner/project lock; code không cho worker/client gọi helper. Journal temp file unique/no link, atomic durable replace ledger là thao tác **riêng ledger**, không nhầm với artifact no-replace.

- [ ] **Step 1: Viết test đỏ quyết định epoch/crash.** `test_epoch_is_max_of_ledger_and_all_project_tables_plus_one` dùng ledger10/project17 →18; fresh project0 →1; import quiescent epoch31 →32 hoặc hơn. `test_generation_b_append_preserves_a_before_db_reconcile`, `test_corrupt_missing_required_record_and_full_journal_fail_closed`, `test_xdg_overrides_do_not_split_counter`, `test_failed_ledger_fsync_never_creates_usable_guard`, `test_writer_retained_by_repository_cannot_close_early`. WriterGuard retain/release lúc repo đang giữ lease phải refuse close và assert_held vẫn đúng.

```python
self.assertEqual(writer.owner_epoch, 18)
self.assertIn((owner_a, epoch_a), {(g.owner_id, g.owner_epoch) for g in ledger.generations})
self.assertIn((writer.owner_id, 18), {(g.owner_id, g.owner_epoch) for g in ledger.generations})
self.assertLess(events.index('ledger_dir_fsync'), events.index('writer_guard_ready'))
```

Events là fault-injection hook local trong tests, không production flag nhận arbitrary action.
- [ ] **Step 2: Red.** Target owner suite. Xác minh fail ở giữ records/epoch/fsync barrier, không vì packet fixture epoch cũ chưa cập nhật.
- [ ] **Step 3: Implement claim algorithm theo spec.** Giữ owner+writer FD → read ledger/state → validate required prior bindings → UUID owner ID → max+1 → append record root/boot/invocation/supervisor/cgroup identities → encode private model → temp write/flush/fsync → atomic rename ledger → fsync state dir → dựng guard → migration/reconcile. Fail bất kỳ bước nào trước barrier không cấp guard/context/attempt; close đúng owned temp FD/lock, không xóa ledger cũ hợp lệ.
- [ ] **Step 4: Giữ journal/recovery boundaries.** 1024 records/1_048_576bytes inclusive LF, full → resource_exhausted. Không auto-GC closed record, không reset counter khi reboot/HOME env/project đổi. Missing ledger chỉ fresh khi project không cần prior stop evidence và không workload cũ; corrupt luôn recovery_required. API owner FD chỉ close duplicate, không LOCK_UN. Chuyển project drain/repo/leases/writer trước generation mới; chưa đủ điều kiện thì refuse.
- [ ] **Step 5: Green/checkpoint C-03.** DTO schema checker + owner tests + real process kill tại append/fsync boundary trong temp test journal. Commit `feat(linux): persist project-bound owner generations before claims`; handoff crash points và journal recovery instructions, không đưa journal user thật vào fixture Git.

### Task C-04: Native OwnerStopEvidence và DB recovery

**Read:** repository open/recovery_views/reconcile_stopped/reconcile_owner_leases; OwnerStopEvidence guards; native profile5. `reconcile_stopped` không tự nhận proof, caller composition phải kiểm trước call.

**Files:** Modify linux_owner.py/root composition; Extend test_linux_owner.py/test_linux_lifecycle.py; integration fixture driver mới ở E-01 sẽ consume helper, chưa tạo production job route.

**Interfaces:** `owner.recovery_evidence() -> OwnerStopEvidence`; evidence.assert_stopped(project_id, old_owner_id, old_epoch) quan sát OS lại mỗi lần. Private observer dùng B identities/manager query, current root journal binding; không nhận evidence object từ RPC/JSON.

- [ ] **Step 1: Test đỏ branches.** `test_old_boot_needs_exact_root_owner_binding`, `test_current_invocation_allows_only_pinned_api_and_supervisor`, `test_old_cgroup_identity_ambiguous_blocks_recovery`, `test_manager_stopping_or_unknown_blocks_recovery`, `test_missing_generation_record_does_not_become_true_after_reboot`, `test_active_old_leases_retained_until_native_stop`. Boot-ID branch unit fake ghi rõ scope; actual reboot evidence thu ở E-05 trong VM fixture riêng, không reboot host làm việc.

```python
with self.assertRaises(OwnershipError):
    evidence.assert_stopped(project_id, unrelated_owner, old_epoch)
self.assertTrue(repo.dependency_retained(dependency_id))
# Sau native observer chứng minh đúng generation đã dừng:
count = repo.reconcile_owner_leases(old_owner, old_epoch, evidence)
self.assertEqual(count, 1)
```

- [ ] **Step 2: Red.** Owner/lifecycle suites mục tiêu; actual observer chưa có thì raise/missing proof là đỏ, không thay bằng lambda True.
- [ ] **Step 3: Implement stop evidence.** Lookup exact project/root/owner/epoch record. Boot khác chứng minh old processes gone nhưng vẫn cần provenance binding. Cùng invocation: cgroup census chỉ supervisor/API đúng pinned identities, lặp kiểm khi assertion. Old invocation: old supervisor exited, manager không chạy/stopping old invocation, old cgroup disappeared hoặc identity thay chứng minh old group bị loại bỏ. Ambiguous reuse/read denied/new PID lạ → recovery_required; lock/heartbeat không bỏ qua.
- [ ] **Step 4: Nối recovery đúng thứ tự.** Sau current guard/migrate/open, với từng recovery view: observer.assert_stopped(old tuple) rồi repo.reconcile_stopped(job,key); old active leases qua reconcile_owner_leases với evidence. Chỉ xong transaction mới nhận job/GC. Crash A→appendB→chết trước reconcileA: recordA vẫn dùng được. Không sửa bool/token trong DB bằng tay hoặc state closed trong ledger để vượt proof. Recovery mất provenance: restore trusted journal+project hoặc quiescent backup theo quy trình, không tự fabricate record.
- [ ] **Step 5: Green/checkpoint C-04.** Kill API/supervisor/worker/grandchild fixture thật; identity mismatch/permission read tests phải block; Windows owner regression vẫn giữ. Commit `feat(linux): require native generation evidence for recovery`. 010.2 chỉ đóng khi B/C trên hai LTS và các subcase cần thiết có evidence; phần chưa kiểm ghi riêng.
