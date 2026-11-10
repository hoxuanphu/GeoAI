# Kiểm tra và bằng chứng nghiệm thu

Đã bắt đầu triển khai code theo yêu cầu mới; contracts metadata đã kiểm, phần API/UI/native có trạng thái riêng ở [roadmap](../roadmap.md) và [spec](../specs/README.md). Bằng chứng phải chứng minh đúng loại yêu cầu, không suy từ số lượng test hoặc tài liệu.

## Ma trận yêu cầu – phép kiểm – đầu ra

| Nhóm | Phép kiểm bắt buộc khi triển khai | Bằng chứng và task |
| --- | --- | --- |
| Tài liệu | File/relative link/anchor, UTF-8, fence, JSON ví dụ, trạng thái và đồng bộ nguồn | Báo cáo Markdown; SPEC-000; không đóng gate runtime |
| Contracts | Round-trip, version/unknown field/UTC/finite, shape/units, invariant liên trường, RPC, schema stale | Lệnh unittest/exporter, log và schema hash; SPEC-001 |
| G0/data | Đọc band/QA có quyền, coverage ngày/tháng/composite 2–3 năm, split/nhãn, quyết định gate/hardware/budget | Hồ sơ G0 được xác nhận; SPEC-002 |
| Shell/security | Handoff session, Host/Origin/token đúng/sai/cũ, normal exit/crash, Job Object | Windows process/UI tests, log đã lọc; SPEC-003 |
| Ubuntu desktop | UB-01–20: hai LTS, WebKitGTK/session, UID owner/cgroup, FD/I/O, DB/publish, ABI/installer/offline | [Ma trận Ubuntu](../platforms/ubuntu/ubuntu-validation-matrix.md); SPEC-003/004/009 và gate tương ứng; toàn bộ runtime Ubuntu chưa chạy |
| Repository/job | DB constraint/migration/backup/restore, worker process thật, cancel/retry/fencing, crash từng điểm publish, lease/GC | SQLite/filesystem/process integration tests; SPEC-004 |
| Execution owner | Hai project/instance/session cùng tài khoản, khóa/ACL/namespace, abandoned owner còn worker sống, chuyển project và PID tái sử dụng | Process Windows thật; SPEC-003/004, ADR-011; chưa hứa điều phối nhiều tài khoản |
| Importer/resolver | IMP-01–11, NET-01–06, RES-01–08, ca dương external input và sentinel ngoài vùng ghi | Schema/native/process/network fixture có kiểm soát; SPEC-009 và phần tích hợp SPEC-004/007 |
| GIS | Điểm chuẩn độc lập, CRS/VN-2000/grid offline, ranh UTM, mask/resample/area/coverage | Fixture có nguồn/hash/tolerance được duyệt; SPEC-005/007 |
| Prithvi kỹ thuật | Band/unit/metadata/shape, backbone thật, decoder đúng kiến trúc, export/output tolerance, CPU/NVIDIA đã chọn | Manifest technical, benchmark và pack report; SPEC-005; chưa chứng minh F1 |
| Viewer/PDF/bundle | Codec/COG/COPC/WASM/font offline, Range/auth, state, p95/frame/memory, draft PDF tiếng Việt, native bundle | Fixture và máy/viewport cố định; SPEC-007 |
| Nghiệp vụ G2 | Checkpoint đã huấn luyện, test độc lập vùng/thời gian, per-class F1/IoU, coverage và CPU SLO; đối chứng RF cùng split | Evaluation/golden output/benchmark business, workflow tới reviewed report; SPEC-006 |
| Training/model pack | Dataset/split leakage, recipe/profile/seed/revision, checkpoint selection qua validation, test độc lập, conversion/runtime/gate/license và promotion | Checkout training có version + runtime pack tests/evaluation; SPEC-008 sản xuất đầu vào SPEC-006 |
| Phát hành G3 | Máy sạch tài khoản thường/offline, installer/pack, upgrade/restore, retention và diagnostics | Spec phát hành riêng sau G1/G2; chưa có bằng chứng |
| Vật lý G4 | Đơn vị/ví dụ chuẩn, miền hiệu lực, calibration/test, uncertainty; solver kiểm bảo toàn/hội tụ khi áp dụng | Spec riêng từng PHY theo ADR-010; chưa có bằng chứng |

G1 gồm cả nền tảng desktop/GIS/job/viewer/report/bundle và spike Prithvi; SPEC-005 pass riêng không đủ. G2 phải chạy lại export/tolerance/precision/benchmark với checkpoint nghiệp vụ. GPU tùy chọn chỉ được công bố hỗ trợ cho tổ hợp thực sự đã kiểm; CPU vẫn là cấu hình chính thức phải đạt gate.

Sau bổ sung review, G1 còn phải có phần execution owner/resolver/importer tương ứng SPEC-003/004/009; đây là ca acceptance cần chạy, không là bằng chứng đã có. Training có checkpoint/evaluation ở SPEC-008 không tự đóng G2: SPEC-006 vẫn kiểm integration/review/metrics/PDF. Nhãn/recipe có thể chuẩn bị trước khi toàn G1 xong theo dependency G0 tương ứng.

## Bằng chứng riêng cho Ubuntu

[SPEC-010](../specs/010-ubuntu-foundation.md) ánh xạ suite 010-T01–09 vào UB và yêu cầu process/file/SQLite thật, cùng Windows regression. Native profile bổ sung creator identity, pidfd stop không race theo tên unit, journal giữ generation cũ, writer-FD/copy finalize và schema-private ledger. Các suite/mốc này hiện chưa triển khai; kiểm Markdown không đánh pass runtime.

[ADR-012](../adr/ADR-012-ubuntu-desktop.md), [kiến trúc](../platforms/ubuntu/ubuntu-desktop-architecture.md) và [guide](../platforms/ubuntu/ubuntu-development-and-packaging.md) phân biệt kiểm userland/container, kernel/session desktop, WebKitGTK automation, máy sạch và GPU thật. Mỗi ca phải ghi kết quả riêng cho Ubuntu 22.04 LTS/24.04 LTS và X11/Wayland khi áp dụng; không suy Linux pass từ Windows, frontend/Chromium hoặc skip native. Chưa có test Linux/Cloud trong đợt tài liệu 10/11/2026; chuẩn bị fixture trước G0 không thay các dependency GIS/ML/nghiệp vụ hoặc nghiệm thu G3.

## Tổ chức kiểm tra

- **Nhẹ/offline:** contracts và logic thuần, fixture nhỏ không yêu cầu weights/GPU/credential. Khi có package thật, thêm kiểm hướng import/cycle theo architecture.
- **Tích hợp local:** SQLite/filesystem/process/pipe và session trên Windows; không chỉ mock các race quyết định. Mỗi test cô lập project/temp directory, không dùng dữ liệu của người dùng làm chỗ ghi thử.
- **GIS/model/solver:** chạy trong môi trường native/pack đã khóa, inventory/hash dữ liệu và model; tách fixture kỹ thuật khỏi kiểm định nghiệp vụ. Skip vì thiếu dependency phải được ghi là chưa kiểm, không chuyển thành pass gate.
- **Live provider:** opt-in sau khi có quyền truy cập; secret nằm ngoài Git/log. Lưu metadata phiên bản, ngày kiểm và phạm vi; lỗi auth/quota/provider khác lỗi thuật toán.
- **Máy sạch/UI/installer:** báo OS/WebView2/CPU/GPU/driver, quyền tài khoản, mạng và cache. Không dùng thành công trên máy build có PATH/cache để kết luận offline pack đạt.

Lệnh SPEC-001: `$env:PYTHONPATH = 'backend'; python -m unittest discover -s tests/contracts -v` và `python tools/export_contract_schemas.py --check`. Suite/exporter đã được kiểm trong [bằng chứng](../evidence/codegen-2026-11-08/task-1-report.md); bổ sung DTO phải chạy lại. Script frontend/API/native nằm trong task SPEC-003; chỉ lệnh thực sự đã chạy mới được ghi pass, không suy native Cargo/build từ Vite build.

## Hồ sơ bằng chứng

Bộ số ngưỡng mới và các điều kiện đo còn mở nằm tại [tiêu chí nghiệm thu](../domain/acceptance-criteria.md). Khi triển khai, evaluator phải kiểm đồng thời per-class/global trên confusion matrix cùng protocol, mask coverage T=3/quan sát thật, area estimator/CI đúng thiết kế, CRS/điểm độc lập và tài nguyên/clock boundaries đã khóa. Cần ca biên bằng ngưỡng/thiếu mẫu/mẫu số 0, F1–IoU nhất quán, pixel imputation không tăng observation coverage và thiếu protocol không được trả pass. Đây là yêu cầu test tương lai, chưa là test đã chạy.

Mỗi lần bàn giao lưu báo cáo có các trường sau; chỉ ghi giá trị quan sát được. Với dữ liệu nhạy cảm, báo cáo chứa ID/hash và vị trí kho được phép, không chứa dữ liệu khách hàng, signed URL hoặc token.

| Trường | Nội dung |
| --- | --- |
| Danh tính | Task/gate, ngày và múi giờ, người thực hiện/reviewer; commit nếu có Git, nếu chưa thì inventory/hash |
| Phạm vi | Phiên bản đề xuất/spec/schema; các yêu cầu đang kiểm và phần chưa kiểm |
| Môi trường | OS/architecture/CPU/RAM/đĩa; GPU/driver/runtime khi dùng; dependency/lock/build hash |
| Đầu vào | AOI/dataset/split/model/decoder/profile/grid/TransformSpec IDs/hash; synthetic hay thực |
| Thực thi | Lệnh đầy đủ, exit code, số ca pass/fail/skip, thời gian; đường dẫn log/artifact đã lọc |
| Tiêu chí | Gate/tolerance phiên bản nào, người xác nhận và thời điểm trước tối ưu/evaluation |
| Kết quả | Số đo và kết luận riêng từng tiêu chí; lỗi/hạn chế; không bỏ qua lớp hiếm/vùng không quan sát |
| Quyết định | Người chốt, pass/fail/chưa đủ bằng chứng, hành động tiếp theo và task liên quan |

Báo cáo chỉ trỏ tới artifact thực sự tồn tại hoặc kho đã kiểm quyền. Không tạo file bằng chứng rỗng, không sửa golden output để test đạt, không ghi mục tiêu throughput thành số đo. Báo cáo tài liệu của đợt này đặt tại [2026-11-08-documentation-review.md](../evidence/2026-11-08-documentation-review.md).

## Quy tắc đóng trạng thái

Task hoàn tất cần đủ acceptance, phép kiểm đã chạy và đường dẫn bằng chứng. Gate hoàn tất cần tập hợp đủ task/phép kiểm của gate cùng quyết định có thẩm quyền. `readiness=business`, review của người dùng và schema validation là các điều kiện khác nhau: tự gán một trường không thay evaluation, quyền duyệt hoặc fencing.

Ngưỡng nghiệp vụ, tolerance kỹ thuật, chu kỳ heartbeat/cancel và support matrix cần được chọn đúng chủ trì theo G0/G1, có nguồn và phạm vi. Số `0.1 m`, RAM, coverage `0.75` hoặc seed trong fixture JSON chỉ là ví dụ cấu trúc, không phải thông số đã được chủ nghiệp vụ chấp thuận.
