# Rà soát source Ubuntu sau đồng bộ GitHub

Ngày: 10/11/2026. Source: `0abe24d8274d5dcf254fdcfd69fd429a19cbcb35`, nhánh `feat/ubuntu-installer`. Executor: Debian 13 x86_64, Python 3.12.14, Node 24.22.1/npm 11.9.0. Đây là kiểm code/backend/frontend trên Linux cloud; chưa là nghiệm thu Ubuntu Desktop, native Tauri hoặc installer.

> Phần khảo sát 10/11/2026 bên dưới giữ nguyên số liệu của `0abe24d`, không đại diện checkout mới. Xem [đối chiếu tại `d4e0060`](#đối-chiếu-lại-ngày-11112026-tại-d4e0060). Phương án khảo sát cũ đã bỏ; căn cứ triển khai hiện tại là [SPEC-010](../specs/010-ubuntu-foundation.md), [native profile](../platforms/ubuntu/ubuntu-native-profile.md) và [plan A–E](../superpowers/plans/2026-11-10-ubuntu-foundation.md).

## Kết luận theo mức ảnh hưởng (khảo sát 10/11/2026)

1. **Chặn bootstrap Ubuntu:** `apps/desktop/src-tauri/src/main.rs` có Win32 launcher thật, nhưng ngoài Windows trả `windows_required`. `backend/geoai/bootstrap.py` native mode cũng kiểm Job Object và gọi `ExecutionOwner` Windows. Cần adapter ở cả Rust và Python; không bỏ kiểm containment để chạy production.
2. **Chặn worker và đường dữ liệu:** `jobs/native_process.py`, `jobs/transport.py`, `workers/bootstrap.py` dùng Job Object/HANDLE/msvcrt; I/O resolver, extraction, GC, publisher và worker import `storage.windows_io` trực tiếp. Nhiều chỗ kiểm concrete `NativeRoot` bằng `isinstance`. Phải tách interface và factory được kiểm soát cùng backend Linux; đổi import một chỗ hoặc thêm launcher không đủ.
3. **Cần bảo toàn security semantics:** Linux không có Windows share-denial/Job Object/SID ACL tương đương một-một. Port phải chứng minh FD inheritance, directory/file identity, symlink/hardlink/race, atomic no-overwrite publication, owner epoch/stop evidence và thu hồi cả process tree. Không thay bằng `Path.resolve`, PID file hoặc kill parent đơn thuần.
4. **Đã có phần dùng lại:** coordinator/protocol, grant registry và repository/migration SQLAlchemy có source; phần logic thuần chạy được trên Debian với DB extra. Không cần viết lại thành backend Linux riêng. Native integration tiếp tục bị skip ở Linux.
5. **Packaging chưa có:** bundling còn tắt, chưa khóa Cargo/toolchain và chưa có workflow native. Giữ đề xuất `.deb` amd64 build trên Ubuntu 22.04, kiểm cùng artifact trên 22.04/24.04; Python >=3.12 cần runtime riêng. Source Windows đã có không đồng nghĩa Rust native đã compile/installer đã kiểm.

## Kiểm tra thực hiện

Cài `.venv` theo `PIP_CACHE_DIR=/workspace/.cache/geoai-pip .venv/bin/python -m pip install -e '.[api,test,db]'` (exit 0). Dependency DB resolve thực: SQLAlchemy 2.1.8, Alembic 1.20.1; FastAPI 0.141.1, Uvicorn 0.49.0, Pydantic 2.14.3. Không sửa manifest/lockfile hoặc tắt xác minh TLS/checksum.

Chạy từng suite bằng Python `.venv`, `PYTHONPATH=backend`, tương đương `python -m unittest discover -s tests/<suite> -v`. Runner lần này dùng `unittest.defaultTestLoader.discover` và `TextTestRunner`, lưu run/pass/skip/error riêng và trả exit 1 nếu có error/failure.

| Suite | Tổng số | Pass | Skip | Error | Failure |
| --- | ---: | ---: | ---: | ---: | ---: |
| contracts | 58 | 58 | 0 | 0 | 0 |
| integration | 56 | 14 | 42 | 0 | 0 |
| architecture | 2 | 2 | 0 | 0 | 0 |
| catalog | 9 | 9 | 0 | 0 | 0 |
| storage | 75 | 52 | 22 | 1 | 0 |
| jobs | 17 | 17 | 0 | 0 | 0 |
| Tổng | 217 | 152 | 64 | 1 | 0 |

Skip do Windows kernel/managed process/handle I/O, kể cả các bài tích hợp DB+Windows. DB extra đã được cài; không báo các skip này là pass hoặc thiếu dependency DB.

`npm test`: 7/7 UI tests pass; `npm run typecheck`, `npm run build`: exit 0, Vite build 33 modules. `tools/export_contract_schemas.py --check`, `tools/export_api_client.py --check`, `.venv/bin/python -m pip check`: exit 0/current/no broken requirements.

## Lỗi test được xác nhận, chưa sửa

`tests/storage/test_repository.py:288`, bài `test_attempt_state_tracks_publication_cancel_and_stop`:

```python
states = dict(conn.execute(text("SELECT job_id,state FROM attempts")))
```

Với dependency được phép bởi manifest hiện tại, dòng này báo `TypeError: 'CursorResult' object is not subscriptable`. Tái hiện bằng đúng test fixture, sau lỗi đọc query qua `.all()` và comprehension theo hai cột xác nhận dữ liệu là `{'job:1': 'succeeded', 'job:2': 'cancelled'}`. Đây là lỗi cách đọc result trong test được lộ ra khi bật DB extra; chưa có bằng chứng thao tác publish/cancel DB sai ở ca này. Cần sửa test theo API SQLAlchemy trong task code tiếp theo, giữ assertions và chạy lại suite DB. Không ghim lùi dependency chỉ để che lỗi; không coi kiểm chẩn đoán bổ sung là test gốc đã pass. Không suy lỗi này phụ thuộc Ubuntu hoặc khẳng định mọi version SQLAlchemy có cùng biểu hiện.

## Bàn giao

Trong đợt khảo sát 10/11/2026, đã sửa phương án Ubuntu cũ (đã bỏ ngày 11/11/2026) để thay các nhận định cũ về scaffold/production bootstrap/job/database, thêm bản đồ file cần port và tách U3a metadata khỏi U3b job/storage fixture. Đồng bộ roadmap/tracker. Chỉ sửa tài liệu, không sửa application code, test, schema, manifest hoặc lockfile. Native Ubuntu 22.04/24.04, Windows Rust, Wayland/X11, lifecycle xuyên session, package máy sạch và các gate vẫn chưa được nghiệm thu trong phiên này.

Log chi tiết trên máy hiện tại: `/workspace/geoai-onboarding/review-{contracts,integration,architecture,catalog,storage,jobs}.log`, tổng hợp `/workspace/geoai-onboarding/review-results.json`. Các file này không phải artifact Git và không bảo đảm tồn tại ở task khác. Bảng kết quả ở trên là bản ghi được giữ trong repository.

## Đối chiếu lại ngày 11/11/2026 tại d4e0060

Nhánh `feat/ubuntu-installer`, source `d4e0060` (`refactor(storage): begin shared native IO types`), đã đồng bộ remote khi cập nhật workspace. Đợt này chỉ bỏ phương án khảo sát cũ và đồng bộ báo cáo/roadmap/tracker, không sửa application code, test, schema hay dependency. Các số liệu 10/11 phía trên giữ giá trị lịch sử.

### Hiện trạng source và tài liệu

- A-01 **partial**: `backend/geoai/storage/native_io.py` mới chứa `NativeIdentity` và `StorageIOError(ValueError)`; `windows_io.py` re-export cùng object. `tests/storage/test_native_factory.py` có 1 test xác nhận tương thích; tên file không chứng minh đã có factory. Chưa có protocol, registration, WindowsIOFactory, deadline hoặc external reader. Theo [handoff A-01](ubuntu-foundation-2026-11-10/A-01/handoff.md), còn phải giải quyết khác biệt base exception với catalog trước khi hoàn tất adapter.
- A-02–E-05 chưa bắt đầu. 010.1 đang làm nhưng chưa hoàn tất; 010.2–010.3 chưa triển khai. Rust launcher ngoài Windows vẫn trả `windows_required`; bootstrap/owner/worker và concrete NativeRoot vẫn phụ thuộc Windows. Chưa có adapter/runtime Linux hoặc installer đã nghiệm thu; bundling vẫn tắt.
- Đã có [ADR-012](../adr/ADR-012-ubuntu-desktop.md), SPEC-010, native profile/interface và plan A–E. Không tạo ADR/plan song song từ phương án khảo sát cũ. Thiết kế kỹ thuật còn đề xuất, implementation phải theo spec/profile hiện tại: namespace `/run/user/<uid>/geoai-execution-v1`, ledger lấy home từ OS, systemd user manager/cgroup và pidfd; không tự dùng namespace từ HOME/XDG override hoặc fallback khác.
- Bước tiếp theo: tiếp tục A-01 theo [plan shared adapters](../superpowers/plans/2026-11-10-ubuntu-foundation/01-shared-adapters.md), kiểm factory/registry/purpose/root/deadline và Windows regression. Baseline Debian không thay baseline hai Ubuntu LTS hoặc acceptance native. G0–G4 giữ nguyên.

### Kiểm tra lại 6 suite Python

Dùng `.venv/bin/python`, `PYTHONPATH=backend` trên Debian Cloud với DB extra đã có. Không cài hoặc thay dependency trong đợt đối chiếu này. Chạy từng suite theo lệnh sau, thay `<suite>` bằng contracts, integration, architecture, catalog, storage, jobs:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s tests/<suite> -v
```

| Suite | Tổng số | Pass | Skip | Error | Failure | Exit code |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| contracts | 58 | 58 | 0 | 0 | 0 | 0 |
| integration | 56 | 14 | 42 | 0 | 0 | 0 |
| architecture | 2 | 2 | 0 | 0 | 0 | 0 |
| catalog | 9 | 9 | 0 | 0 | 0 | 0 |
| storage | 76 | 53 | 22 | 1 | 0 | 1 |
| jobs | 17 | 17 | 0 | 0 | 0 | 0 |
| Tổng | 218 | 153 | 64 | 1 | 0 | — |

So với khảo sát `0abe24d`, tăng 1 test shared types pass. Lỗi `test_attempt_state_tracks_publication_cancel_and_stop` vẫn tái hiện tại `tests/storage/test_repository.py:288`:

```text
states = dict(conn.execute(text("SELECT job_id,state FROM attempts")))
TypeError: 'CursorResult' object is not subscriptable
```

Không sửa test hoặc bỏ assertion để đạt pass. Các skip vẫn do yêu cầu Windows; không dùng chúng làm bằng chứng native thành công. Kết quả UI/typecheck/build/schema/client ghi ở phần 10/11 là lịch sử, không được chạy lại trong đợt chỉnh tài liệu này.

### Kiểm tài liệu sau chỉnh sửa

Ngày 11/11/2026: kiểm 163 liên kết nội bộ/anchor và code fence trong ba file báo cáo/roadmap/tracker đều hợp lệ; không còn tham chiếu tới file phương án đã bỏ. `git diff --check` không báo lỗi. Bảng kết quả và traceback ở trên lưu bằng chứng trong báo cáo; log chạy 6 suite của lần đối chiếu này ở `/workspace/work/ubuntu-doc-sync/<suite>.log` chỉ là log local, không bảo đảm tồn tại ở phiên khác. Chưa commit hoặc push.

## Tiếp tục A-01

Ngày 11/11/2026, baseline `d4e0060`, workspace đã có các thay đổi tài liệu chưa commit. Đã bổ sung `NativeReader`, `NativeRoot`, `NativeIOFactory` dạng Protocol và `ExternalRegistration` frozen trong `backend/geoai/storage/native_io.py`. Các protocol không runtime-checkable và không cấp quyền. `StorageIOError` tiếp tục kế thừa ValueError như implementation cũ; catalog ghi RuntimeError, cần quyết định tương thích khi hoàn thiện A-01. `io_resolver.ExternalRegistration` vẫn là kiểu cũ riêng: cần chuyển/re-export cùng object ở A-02 trước khi nối consumer; không dùng hai kiểu thay thế nhau lúc này.

TDD: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s tests/storage -p test_native_factory.py -v`: trước thay đổi 2 ImportError do thiếu interface, sau thay đổi 3 pass. Suite contracts: 58 pass. Suite storage: 78 tests, 55 pass, 22 skip, 1 error đã biết `test_attempt_state_tracks_publication_cancel_and_stop` tại `tests/storage/test_repository.py:288` (`CursorResult` not subscriptable); log local `/workspace/work/ubuntu-doc-sync/a01-storage.log`. Windows I/O: 7 skip trên Debian, không là native proof.

Chưa hoàn thành A-01: còn registry giữ strong references, purpose/closed-root checks, WindowsIOFactory và wrapper, deadline monotonic, external reader lifetime cùng tests và Windows regression thật. Tiếp tục từ Step 1 của [plan A-01](../superpowers/plans/2026-11-10-ubuntu-foundation/01-shared-adapters.md); chưa bắt đầu A-02–E-05. 010.1 chưa hoàn tất; không đóng gate.
