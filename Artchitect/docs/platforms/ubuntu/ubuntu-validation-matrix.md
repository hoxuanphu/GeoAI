# Ma trận phát triển và nghiệm thu Ubuntu

**Ngày:** 10/11/2026. **Trạng thái chung:** các ca `UB-01`–`UB-20` dưới đây **chưa chạy** trên Ubuntu 22.04 LTS hoặc Ubuntu 24.04 LTS. Đây là acceptance bổ sung cho [SPEC-003](../../specs/003-desktop-shell.md), [SPEC-004](../../specs/004-jobs-and-publish.md), [SPEC-009](../../specs/009-importer-worker-resolver.md) và các gate liên quan; không phải bảng kết quả.

Cơ sở: [ADR-012](../../adr/ADR-012-ubuntu-desktop.md), [kiến trúc Ubuntu](ubuntu-desktop-architecture.md), [đóng gói](ubuntu-development-and-packaging.md), [security IMP/NET/RES](../../importer-resolver-security.md), [testing strategy](../../guides/testing-strategy.md). Dữ liệu fixture nhỏ/tổng hợp được phép dùng trước G0; dữ liệu thực/model/benchmark chỉ thực hiện khi đủ dependency và quyền. Không đặt AOI, quality threshold, quota, thời hạn hoặc hardware thành quyết định đã duyệt.

[SPEC-010](../../specs/010-ubuntu-foundation.md) là spec triển khai foundation, với profile native/interface và suite 010-T01–09. UB vẫn là ma trận acceptance theo lớp; spec được hoàn thiện không đánh dấu bất kỳ ca runtime nào pass.

## 1. Lớp bằng chứng

| Lớp | Có thể chứng minh | Không đủ để kết luận |
| --- | --- | --- |
| Tài liệu trên Windows | File/link/anchor/fence, ngữ nghĩa thiết kế, phạm vi thay đổi | Bất kỳ test Linux/native/GIS/model/installer nào |
| Container userland từng LTS | Contracts/backend/DB/frontend hoặc build khi đủ dependency | Kernel LTS thật, login session/cgroup desktop, Wayland, driver và máy sạch |
| Desktop automation thật | Tauri/WebKitGTK, session/token, lifecycle trong OS/session đã ghi | GPU/hardware khác, power-loss durability hoặc chất lượng nghiệp vụ |
| VM/máy đích từng LTS | Cài/upgrade/uninstall, session và native integration trong profile đã thử | NVIDIA nếu chưa passthrough/driver thật, distro/architecture khác |
| GIS/AI/hardware | Chỉ số/quality/coverage/runtime/CPU/GPU trên workload và protocol đã khóa | Support matrix rộng hơn mẫu được kiểm hoặc gate khác |

Mỗi ID cần record riêng cho 22.04 và 24.04, result `chưa chạy/pass/fail/skip`, environment và log. `skip` vì thiếu dependency được giữ là chưa kiểm. X11 và Wayland tách subcase; profile nào thiếu bằng chứng thì không công bố hỗ trợ profile đó.

## 2. Ca bắt buộc

| ID | Phạm vi / task | Ca kiểm và điều kiện đạt | Môi trường tối thiểu / gate |
| --- | --- | --- | --- |
| UB-01 | Preflight / SPEC-003 | OS/arch/kernel/glibc/interpreter/lock/FS được nhận diện; ghi dependency thiếu và giới hạn; user manager/cgroup/runtime path được probe, không đoán từ tên image | Mỗi LTS; chuẩn bị G1 |
| UB-02 | Contracts/core/DB / SPEC-001/004 | Suite và exporter thật, SQLite migration/constraint/backup/restore; tách lỗi import Windows khỏi lỗi nghiệp vụ, không đổi skip thành pass | Userland hai LTS; G1 tương ứng |
| UB-03 | Frontend / SPEC-003 | Restore theo lock, DOM/typecheck/Vite build; bootstrap/health/error giữ state và capability chưa có vẫn false | Userland hai LTS; chưa là native |
| UB-04 | Native launch / SPEC-003 | Tauri/WebKitGTK thật nhận descriptor qua IPC private, API/worker thuộc nhóm từ lúc tạo; không lộ argv/URL/log; normal exit dọn đủ | Desktop hai LTS; G1 |
| UB-05 | Session security / SPEC-003 | Đúng/sai/cũ/thiếu Host/Origin/token, dev/production; fetch/SSE/Range/loader worker, CORS/CSP theo origin thực. Thiếu Origin vẫn theo policy có token/Host; không allow wildcard để chạy được | WebKitGTK thật; G1 |
| UB-06 | Owner / SPEC-003/004 | Hai project, hai bản cài và hai login session cùng UID cùng tranh; khác `XDG_*`/đường cài không tạo owner thứ hai. Instance mới không stop owner hợp lệ để giành quyền. Một writer/job nặng; read-only không ghi WAL/SHM hoặc chạy import/tile/GC ngầm | Desktop/session thật hai LTS; G1 |
| UB-07 | Crash/containment / SPEC-003/004 | Kill shell, supervisor, API và worker ở từng giai đoạn; child/grandchild kể cả `setsid`, EOF bị giữ FD, TERM timeout, process kẹt. Thu hồi token và xác nhận nhóm cũ rỗng trước cấp compute; chưa rõ thì chặn | Process/cgroup thật hai LTS; G1 |
| UB-08 | Danh tính/recovery / SPEC-003/004 | PID tái sử dụng, metadata cũ, lock FD rò, unlink/recreate lock, manager không truy vấn được, logout/session khác. Không kill PID không thuộc app, không cấp lại từ heartbeat/lock lấy được đơn thuần | Process/session thật; G1 |
| UB-09 | Worker IPC / SPEC-004/009 | UTF-8/LF, partial/oversized/NaN, ID correlation, stdout nhiễm log native, stderr đầy, pipe đóng, cancel/heartbeat khi handler bận; FD allowlist không rò token/owner | Process và native output Linux; G1 |
| UB-10 | Managed/external read / SPEC-009 | Ca dương IMP-07/08, RES-01/02/03/08; hash/identity/nonce/context đúng, dependency sidecar đủ; source đổi sau grant bị từ chối hoặc materialize copy đúng snapshot | File/FD/process thật; G1 |
| UB-11 | Path/format/ZIP / SPEC-009 | IMP-01–06/09–11 trên Linux: traversal, symlink/magic-link/hardlink, ancestor swap, FIFO/device, case/Unicode/portable names, ZIP envelope và quota/cancel. Sentinel ngoài staging giữ hash | File/FD/process thật; G1 |
| UB-12 | Publish/fencing / SPEC-004/009 | RES-04/05/06/07, candidate khác attempt/project, còn writer FD, bytes đổi, cancel/retry cạnh tranh; transaction chỉ nhận active token và publication duy nhất | Process + file + SQLite thật; G1 |
| UB-13 | Crash consistency / SPEC-004 | Crash trước/sau file fsync, rename/directory fsync, DB commit/event; không overwrite, EXDEV không fallback, orphan không phục vụ. Phân biệt process kill với power-loss test | FS/mount hai LTS đã ghi; G1/G3 theo phép thử |
| UB-14 | Provider / SPEC-009 | NET-01–06 với DNS/redirect/server fixture kiểm soát; tổng deadline/quota và redaction. Worker không tự truy cập provider; live test chỉ khi được cấp quyền | Fixture offline/local; G1; live phụ thuộc G0 |
| UB-15 | GIS/viewer/PDF / SPEC-007 | CRS/TransformSpec/grid/area đúng fixture độc lập, PROJ grid offline; COG/COPC/Range/WASM/font/PDF tiếng Việt, X11/Wayland, graphics driver và loader auth | Desktop/native pack hai LTS; G1 |
| UB-16 | Prithvi / SPEC-005/006/008 | Backbone + decoder/profile thật, HLS band/QA/T=3 và ignore đúng; output tolerance/CPU SLO/quality/coverage theo protocol đã chốt. CPU và NVIDIA/driver kiểm riêng, không fallback âm thầm | Máy/tài nguyên và input đủ điều kiện; G1 kỹ thuật, G2 nghiệp vụ |
| UB-17 | ABI/build/package | Build provenance/lock/ELF/.so/sidecar/data; gói built-on-22.04 được dependency-resolve/install/launch trên cả hai LTS hoặc ghi rõ gói riêng | Build + VM sạch; G1 bundle/G3 phát hành |
| UB-18 | Install/offline | Cài/launch thiếu mạng, không dev tools/cache có sẵn; đủ OS dependency, CPU/model/runtime pack/font/WASM/grids; app tài khoản thường; không tự cài driver/linger/system service | VM/máy sạch từng LTS; G3 |
| UB-19 | Upgrade/uninstall | Drain/backup/migration/restore, gián đoạn/hết đĩa, tương thích DB; gỡ/purge giữ dữ liệu người dùng theo policy, không xóa input/model/project ngoài quyền | VM/máy sạch từng LTS; G3 |
| UB-20 | Chuyển project Windows–Ubuntu | Bundle/backup có inventory/hash, refs/case/Unicode/CRS/license đúng; tái đăng ký root/identity, không replay token/context/owner; không share DB đang mở | Hai OS + bundle fixture; G1 kỹ thuật/G3 workflow phát hành |

Các ID UB bổ sung môi trường và fault case, không thay IMP/NET/RES hoặc ngưỡng [acceptance criteria](../../domain/acceptance-criteria.md). Không ghi pass cả UB-16 chỉ vì một model load được; technical/business và CPU/NVIDIA cần kết quả con riêng.

## 3. Thứ tự triển khai sau tài liệu

| Mốc | Deliverable cần làm | Dependency và điều kiện hoàn tất |
| --- | --- | --- |
| U-DOC | ADR, thiết kế, guide, acceptance và điều hướng | Đợt này: kiểm cấu trúc/nội dung rồi lưu bằng chứng SPEC-000; không đóng runtime |
| U-ENV | Executor hai LTS, dependency resolve/lock, contract/core/frontend baseline | SPEC-010/010.1, UB-01–03 với pass/fail/skip; chưa cần AOI/model thật |
| U-SHELL | Adapter owner/supervisor/session, private FD/bootstrap theo profile v1 | SPEC-010/010.2; review ADR-012, UB-04–08 và phần FD UB-09. Native fixture có thể làm trước G0, không nâng readiness từ scaffold |
| U-IO | Resolver/importer/transport/publisher Linux và SQLite integration | SPEC-010/010.3 tích hợp SPEC-003/009/004; UB-09–13, regression NET fixture UB-14; không tạo dependency vòng |
| U-G1/G2 | Pack GIS/viewer/PDF/Prithvi, tích hợp nghiệp vụ | UB-15/16 và G0/fixture/profile/hardware/budget tương ứng; G1/G2 nghiệm thu riêng |
| U-RELEASE | ABI, package, máy sạch, offline, upgrade và chuyển dữ liệu | UB-17–20; spec phát hành riêng khi đủ đầu vào G3, không tự đánh hoàn tất từ build |

Đây là trình tự đề xuất, chưa phân công người hoặc ấn định lịch. U-ENV/U-SHELL/U-IO không đòi đóng toàn G0 cho fixture thuần; phần cần dữ liệu/model/protocol vẫn giữ dependency. Windows tiếp tục được kiểm regression trong task implementation; không xóa test Windows để tổng suite xanh trên Linux.

## 4. Bằng chứng cần lưu khi chạy thật

Mỗi lần chạy ghi task/ID/subcase, ngày và múi giờ, revision + patch/inventory hash, policy/fixture hashes, LTS/point release/kernel/architecture/FS/mount, desktop/session type, user manager/cgroup và dependency/build hashes. Khi dùng GPU ghi model/driver/runtime; không dùng cấu hình giả.

Ghi lệnh đầy đủ, exit code, pass/fail/skip, expected/actual, duration quan sát được, log đã lọc và đường dẫn artifact có thật. Ca từ chối ghi cần sentinel hash trước/sau; ca owner ghi timeline process/group chứng minh không có hai job nặng. UB-13 phân biệt process crash, reboot và mô phỏng mất điện; không lấy một loại thay cả ba.

Kết quả tài liệu đợt này nằm tại [báo cáo kiểm](../../evidence/ubuntu-2026-11-10/review.md). Báo cáo đó chỉ được đánh dấu hoàn tất phạm vi tài liệu sau khi phép kiểm thực sự chạy; toàn bộ UB runtime ở bảng vẫn chưa chạy.
