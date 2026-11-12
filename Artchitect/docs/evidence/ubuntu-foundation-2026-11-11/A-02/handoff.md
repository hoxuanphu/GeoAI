# A-02 — shared native I/O injection, 11/11/2026

Trạng thái: code và portable regression verified; Windows native regression chưa chạy. Không đóng 010.1. Baseline d4e0060 với thay đổi có sẵn được giữ; không commit/push/tạo nhánh.

Resolver/extraction/GC/publisher không import Windows adapter. Constructor nhận io_factory; NativeRoot được cấp qua identity registry/purpose (read/staging/publication), không duck typing. ExternalRegistration re-export từ native_io giữ cùng type. Worker composition Windows và fixtures đã được cập nhật theo callsites rg, managed input chỉ read; writer fixture legacy còn đến D-04/D-05. Protocol/factory không từ JSON/RPC.

Các boundary duration chuyển một lần thành absolute monotonic deadline. Publisher dùng resolver._open_read_until để giữ nguyên deadline trong snapshot read; mỗi I/O dưới loop nhận deadline gốc. Mặc định publish/collect/verify_inventory_record 60 giây là kỹ thuật kế thừa I/O cũ. Extraction dùng policy.max_seconds cho toàn inspect/copy; rollback có một deadline cleanup riêng 60 giây, không dùng cancellation chỉ khi xóa đúng các file mới đã ghi và kiểm bytes. Không reset copy deadline hoặc xóa nguồn/project ngoài registration.

TDD: architecture subprocess đỏ vì import windows_io và 5 service cases đỏ do thiếu dependency injection; đã xanh. DB test CursorResult đọc cặp bằng .all() comprehension, giữ nguyên succeeded/cancelled assertion; baseline error đỏ đã tái hiện trước sửa. Full verify trên Ubuntu 22.04 Docker exit0: 248 Python tests, 181 pass/67 Windows skip, không error/failure; frontend 7 pass/build, schema/client/pip, native library link, Cargo check đều pass. [Kết quả](results.json), [status](status.txt), [storage](storage.log), [integration](integration.log), [architecture](architecture.log). Native Windows chưa kiểm; không gọi mock thành native proof.

Review độc lập đã chỉ ra 4 Important issues, đều được tái hiện đỏ → xanh:

1. Lock wait vượt deadline (20ms request chờ 400ms): registry lock chỉ giữ metadata, per-root timed lock dùng deadline/cancellation; move lấy lock thứ tự cố định với cùng budget. ensure_directory không có deadline trong protocol nên fail busy thay vì chờ vô hạn. Test test_deadline_bounds_wait_for_busy_root.
2. Cancellation/invalid budget bị đổi thành False làm demote publication: verify_inventory_record chỉ trả False cho negative byte/policy verification; abort/configuration/native-facility failure propagate. Test SQLite thực hủy ở artifact thứ hai xác nhận transaction rollback cả demotion trước đó.
3. Chuyển deadline qua duration khiến 110 thành114 khi scheduling chậm: internal resolver path giữ absolute110. Test test_scheduling_between_services_never_extends_deadline.
4. require_root(None) AttributeError: membership check tường minh, từ chối unregistered_root. Test test_none_is_an_unregistered_root.

Rulings đầy đủ trong ledger local .superpowers/sdd/2026-11-10-ubuntu-foundation/progress.md; các quyết định compatibility/cleanup/composition được ghi ở trên và handoff A-01. Không đổi wire/schema/gate hoặc capabilities. Bước tiếp theo A-03: process/owner protocols, Windows process factory và transport injection; tiếp tục viết/test phần đủ dependency dù Windows acceptance chưa có.
