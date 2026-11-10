# Tài liệu desktop theo nền tảng

Đọc [kiến trúc triển khai chung](../architecture.md) và [SPEC-003](../specs/003-desktop-shell.md) trước khi làm thay đổi xuyên nền tảng. Các sơ đồ mô tả thiết kế đích; trạng thái implementation được theo dõi ở [roadmap](../roadmap.md).

| Nền tảng | Tài liệu | Phạm vi |
| --- | --- | --- |
| Windows | [Sơ đồ kiến trúc desktop](windows/desktop-architecture-diagrams.md) | UI, tiến trình, owner, Prithvi, publish và provenance |
| Ubuntu 22.04/24.04 LTS | [Kiến trúc](ubuntu/ubuntu-desktop-architecture.md) | WebKitGTK, supervisor, owner, FD/I/O và recovery; kỹ thuật còn đề xuất |
| Ubuntu 22.04/24.04 LTS | [SPEC-010](../specs/010-ubuntu-foundation.md), [native profile](ubuntu/ubuntu-native-profile.md), [interface](ubuntu/ubuntu-adapter-interfaces.md) | Input gen code: namespace, handshake, FD/epoch, adapter và fixture; chưa triển khai |
| Ubuntu 22.04/24.04 LTS | [Plan triển khai chi tiết](../superpowers/plans/2026-11-10-ubuntu-foundation.md) | 5 phần/26 task, signatures, test đỏ/green, lệnh và handoff cho AI; chưa thực thi |
| Ubuntu 22.04/24.04 LTS | [Môi trường và đóng gói](ubuntu/ubuntu-development-and-packaging.md) | Preflight, dependency, `.deb`, ABI, offline và upgrade dự kiến |
| Ubuntu 22.04/24.04 LTS | [Ma trận UB-01–20](ubuntu/ubuntu-validation-matrix.md) | Ca kiểm từng LTS và phân biệt container, desktop, GPU, máy sạch |

Ubuntu desktop là mục tiêu đã được yêu cầu; adapter/runtime/bộ cài và các ca kiểm Ubuntu chưa được thực hiện. [ADR-012](../adr/ADR-012-ubuntu-desktop.md) nối với các quyết định Windows và ghi các lựa chọn còn mở. Linux server là phạm vi riêng ở G4.
