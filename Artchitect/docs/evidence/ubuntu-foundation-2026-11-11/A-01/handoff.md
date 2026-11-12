# A-01 — registered Windows factory, 11/11/2026

Trạng thái: implementation và portable policy verified; native Windows chưa kiểm, task/mốc 010.1 chưa đóng. Baseline d4e0060 cùng thay đổi tài liệu/interface/Ubuntu builder có sẵn được giữ. Không commit/push/tạo nhánh.

Output: native_io có shared value/protocol/ExternalRegistration; windows_io có WindowsIOFactory, registered wrapper và reader adapter. Registry giữ strong refs, kiểm identity cùng factory, purpose, duplicate ID và root closed. Read purpose từ chối mutate trực tiếp. Duration legacy chuyển từ absolute deadline thành remaining tại mỗi call, callback vẫn kiểm deadline gốc sau khi đợi native lock. Move/delete legacy nhận cancellation/budget tương thích mặc định cũ. Reader external đóng verified reader rồi root, idempotent; OS errors map reason code không chứa path. Reader seek trả offset theo protocol.

Ruling: StorageIOError tiếp tục ValueError để bảo toàn class/catch cũ, sửa catalog RuntimeError thành ValueError; không tạo hai error class. Nếu consumer đòi RuntimeError phải điều chỉnh trước adoption. Chỉ giữ legacy concrete NativeRoot cho callers/tests cũ; A-02 mới thay shared consumers.

TDD: lúc đỏ 9 cases thiếu WindowsIOFactory; sau bổ sung policy có một test PermissionError/path exposure đỏ, đã map OSError thành native_io_failed. Lượt cuối: `tools/ubuntu-build/run.sh python -m unittest discover -s tests/storage -p test_native_factory.py -v`, 17 tests, 14 pass/3 Windows skip, exit 0; [log](portable.log). Unit tests chỉ patch OS-dependent legacy adapter, chạy production factory; không là Win32 proof. Test Win32 thật đã thêm cho sharing/lifetime/external expected version/expiry; còn chạy trên Windows cùng suite test_windows_io.py trước nghiệm thu.

A-02 có thể dùng factory/protocol đã tạo. Cần chuyển ExternalRegistration trong io_resolver sang re-export cùng type, inject factory và chuyển wrapper duration một lần tại operation boundary. Chưa mở capability/native Linux, chưa tick 010.1 hoặc gate. Baseline DB CursorResult error vẫn cần xử lý giữ nguyên assertion khi chạy full regression.
