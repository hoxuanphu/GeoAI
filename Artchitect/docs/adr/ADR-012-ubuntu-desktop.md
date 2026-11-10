# ADR-012: Mở rộng desktop local sang Ubuntu LTS

**Ngày:** 10/11/2026. **Trạng thái:** yêu cầu hỗ trợ Ubuntu 22.04 LTS và Ubuntu 24.04 LTS đã được người dùng xác nhận; các lựa chọn kỹ thuật dưới đây là **đề xuất chưa Accepted, chưa triển khai/kiểm chứng**.

**Quan hệ:** bổ sung phạm vi nền tảng của [ADR-001](ADR-001-desktop-first.md), phương án phân phối của [ADR-006](ADR-006-packaging.md) và ánh xạ execution owner của [ADR-011](ADR-011-local-execution-owner.md). Không thay yêu cầu Prithvi ở ADR-008, IPC/attempt ở ADR-009 hoặc bằng chứng Windows. Đây là hồ sơ mở rộng; chỉ thay thế phần giới hạn nền tảng khi quyết định kỹ thuật được chấp thuận sau kiểm chứng.

## Bối cảnh

[Hồ sơ yêu cầu](../evidence/2026-11-10-linux-support-assessment.md) mới ghi mục tiêu và khả năng kiểm Cloud. Checkout hiện có nhánh Tauri ngoài Windows trả `windows_required`, bootstrap/transport/owner/I/O phụ thuộc Windows và chưa bật bundle. Chạy contracts trên Linux không đủ chứng minh vòng đời desktop, resolver hay bộ cài.

Ubuntu là desktop xử lý cục bộ dùng cùng nghiệp vụ, không phải chuyển sang server G4. Cần giữ coordinator duy nhất ghi trạng thái, một project ghi/thực thi và một job nặng trong phạm vi owner; worker chỉ gửi event/candidate và không tự công bố kết quả.

## Các phương án

| Phương án | Lợi ích | Đánh đổi |
| --- | --- | --- |
| Tauri/WebKitGTK + lõi Python dùng chung + adapter Linux | Giữ UI, hợp đồng và pipeline; kiểm riêng các primitive OS | Phải triển khai containment, owner, FD/I/O và đóng gói native |
| Chạy backend Linux và mở trình duyệt | Có thể hữu ích để kiểm backend hoặc triển khai server sau | Không đáp ứng lifecycle/bộ cài desktop đang được yêu cầu; thêm bài toán phiên và vận hành |
| Viết shell/UI Linux riêng | Có thể tối ưu theo toolkit khác | Nhân đôi UI, luồng kiểm và chi phí bảo trì trước khi có bằng chứng cần thiết |

**Đề xuất của đợt tài liệu:** phương án đầu, dựa trên stack đang có. Người dùng đã yêu cầu Ubuntu; chưa có quyết định chấp thuận riêng cho primitive, kiến trúc CPU hoặc định dạng phân phối.

## Thiết kế đề xuất

1. Tauri 2/WebKitGTK thay lớp WebView2 trên Ubuntu; React/Giro3D, API loopback có token, JSON-RPC và các record dự thảo dùng chung. Không giả Origin production giống Windows/dev.
2. Profile đầu để kiểm là **amd64/x86_64**, CPU inference chính thức theo gate; NVIDIA là pack kiểm riêng. ARM64, distro khác, Flatpak/AppImage và multi-user compute chưa được đưa vào support matrix.
3. Supervisor là main process trong một transient service của `systemd --user`; API/worker được tạo bên trong cgroup của service từ đầu. Đề xuất `Type=exec`, `KillMode=control-group`, không tự restart, không daemon nền sau khi đóng shell. Mất kênh sống của shell thì drain/cancel có deadline rồi stop unit; supervisor chết thì manager dọn nhóm. Không dùng process group hoặc `PDEATHSIG` đơn lẻ thay bằng chứng containment.
4. Một namespace owner ổn định theo UID trên máy, dùng cùng user manager qua các login session/bản cài. Supervisor giữ `flock` trên inode local trong runtime directory tin cậy; tên unit/khóa không phụ thuộc project, đường cài, phiên bản app hoặc biến môi trường do project cung cấp. Khóa là advisory, không là sandbox. Chỉ cấp compute mới khi cả owner cũ và nhóm workload cũ đã được xác nhận dừng.
5. Project writer lock, owner epoch, attempt fencing và pin/lease giữ vai trò riêng. `flock` lấy được sau crash chưa cho phép chạy job mới nếu cgroup cũ vẫn có tiến trình hoặc trạng thái chưa xác định.
6. Adapter Linux dùng directory FD, mở tương đối và `openat2` với policy không follow link để giữ containment; kiểm file bằng FD. External input hợp lệ vẫn phải đọc được theo registration, identity/hash. File có nguy cơ thay đổi được materialize thành bản local đã kiểm trước compute; không cấm mọi input ngoài project để đạt ca âm.
7. Project/SQLite WAL/staging/publication ở filesystem local đã kiểm; đề xuất ext4 làm fixture đầu. Publish cùng filesystem, kiểm bytes/attempt và durability trước transaction DB. Không tự coi rename là transaction filesystem–DB.
8. Đề xuất build `.deb` từ Ubuntu 22.04, dùng runtime Python riêng đáp ứng `>=3.12` và dependency lock thực theo OS/architecture. Kiểm toàn bộ executable, sidecar, `.so`, data/font/WASM trên cả hai LTS; có thể cần hai gói nếu dependency khác nhau. Chưa chọn công cụ freeze Python từ tên công cụ.

Chi tiết ở [kiến trúc Ubuntu](../platforms/ubuntu/ubuntu-desktop-architecture.md), [môi trường và đóng gói](../platforms/ubuntu/ubuntu-development-and-packaging.md), [ma trận nghiệm thu](../platforms/ubuntu/ubuntu-validation-matrix.md).

**Cụ thể hóa để gen code, 10/11/2026:** [SPEC-010](../specs/010-ubuntu-foundation.md) cùng [native profile v1](../platforms/ubuntu/ubuntu-native-profile.md) và [interface adapter](../platforms/ubuntu/ubuntu-adapter-interfaces.md) định nghĩa namespace, supervisor/owner FD, bootstrap và cleanup. D-Bus chỉ quản lý unit; Unix stream socket giữ phiên shell, FD API/worker kế thừa có allowlist giữa cha–con. Foundation không cần SCM_RIGHTS qua shell socket. Epoch được hoàn thiện theo ledger/project trước grant; worker kết thúc trước Linux publisher finalize/copy private. Đây là thiết kế đề xuất đã cụ thể hóa, chưa là code hoặc quyết định Accepted.

## Hệ quả và điều kiện

- Runtime không cần root; cài gói hệ thống có thể cần quyền quản trị. Không thêm system service hoặc bật lingering tự động. Thiếu user manager/cgroup/primitive an toàn thì chặn execution và báo rõ, không fallback xuống containment yếu hơn.
- Không giả mọi container/WSL có session desktop, D-Bus hay GPU. Cloud chỉ cung cấp bằng chứng cho lớp thực sự đã chạy.
- UID/cgroup/file identity là chi tiết adapter, không thêm field wire bằng văn bản. Mọi thay đổi Pydantic cần task schema/fixture/exporter riêng cùng SPEC-001.
- Không hứa portable project bằng cách copy raw DB đang mở giữa Windows/Linux. Chỉ trao đổi bundle/backup đã kiểm inventory, đường dẫn, case, Unicode, CRS và dependency.
- Không có hỗ trợ tính toán đồng thời nhiều UID hoặc bảo vệ trước mã độc cùng UID. Quyền OS/containment ở đây không thay fencing hoặc policy importer/network.

## Bằng chứng, người chốt và điều kiện xem lại

Phụ trách native/backend/GIS/packaging và QA là các vai trò dự kiến, chưa gán người hoặc lịch. Review và chấp thuận lựa chọn thiết kế của ADR khác nghiệm thu runtime/sản phẩm: có thể triển khai phần foundation đủ dependency và làm spike để kiểm phương án, không đợi UB-01–20 mới viết code. ADR chỉ ghi Accepted khi có quyết định kỹ thuật có thẩm quyền và bằng chứng phù hợp phạm vi quyết định; không tự Accepted từ spec hoàn tất. Công bố hỗ trợ/đóng G1/G2/G3 vẫn cần các UB tương ứng, đầy đủ bằng chứng và quyết định gate riêng. Các phép kiểm tài liệu theo [SPEC-000](../specs/000-documentation-baseline.md); code foundation theo SPEC-010, hiện chưa bắt đầu.

Xem lại khi user manager không đáp ứng trên hai LTS, có yêu cầu chạy nền/multi-user, cần distro/ARM khác, hoặc ABI/runtime/installer không thể dùng hướng build đề xuất. Không hạ yêu cầu owner/recovery để làm test pass.

## Nguồn

Nguồn upstream được đối chiếu ngày 10/11/2026 trong [hướng dẫn môi trường](../platforms/ubuntu/ubuntu-development-and-packaging.md#nguồn-đã-đối-chiếu). Đây là căn cứ chọn phương án để kiểm, không là bằng chứng GeoAI tương thích.
