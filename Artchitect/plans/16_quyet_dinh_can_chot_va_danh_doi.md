# Quyết định cần chốt và đánh đổi

**Addendum 10/11/2026:** mục tiêu Ubuntu 22.04/24.04 LTS đã được yêu cầu; [ADR-012](../docs/adr/ADR-012-ubuntu-desktop.md) tách yêu cầu này khỏi lựa chọn kỹ thuật WebKitGTK, supervisor/cgroup, UID owner, native I/O và `.deb` chưa Accepted. Bảng cấu hình Windows dưới là baseline Windows; CPU architecture, runtime/lock, session/graphics, offline và support matrix Linux cần bằng chứng riêng, không tự chốt từ tên distro.

[SPEC-010](../docs/specs/010-ubuntu-foundation.md) chọn profile/interface đề xuất cho foundation. Quyết định triển khai thiết kế được review riêng với nghiệm thu runtime/sản phẩm; không chờ đủ UB-01–20 trước viết fixture nền đủ dependency, cũng không đánh ADR Accepted vì spec đã hoàn tất.

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Mặc định đề xuất, người/thời điểm chốt, tác động và các đánh đổi.

<a id="muc-17"></a>

## 17. Các quyết định cần chủ dự án chốt và đề xuất mặc định

Những điểm dưới đây là đầu vào phải chốt trước khi triển khai hoặc nghiệm thu phần phụ thuộc. **Yêu cầu có Prithvi-EO-2.0 từ bản đầu đã được người dùng xác nhận**; biến thể, feature, dữ liệu, quality gate và ngân sách vẫn cần chốt theo bằng chứng. Các mặc định khác là lựa chọn của bản đề xuất, không phải thông số đã được đo.

| Quyết định | Mặc định đề xuất | Ai chốt / thời điểm | Tác động nếu đổi |
| --- | --- | --- | --- |
| Nghiệp vụ đầu tiên | So sánh bảng [mục 4.1](03_pham_vi_ban_dau_va_luong_su_dung.md#muc-4-1); ưu tiên lớp phủ HLS S30 30 m dùng Prithvi | Chủ nghiệp vụ, trước G0 kết thúc | S1-only không thay yêu cầu Prithvi; chọn một feature có nhãn/QA phù hợp |
| Model bắt buộc / cấu hình | Prithvi-EO-2.0; khởi đầu 300M-TL + UPerNet, T=1 và 224 cố định; ứng viên CPU 100M-TL/tiny-TL, non-TL 300M theo [mục 8.2](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-2) | Nhóm ML lập danh sách G0, sàng lọc G1, xác nhận checkpoint nghiệp vụ G2 | Giữ model/decoder version riêng; runtime/biến thể chưa được nghiệm thu chỉ từ decoder ngẫu nhiên |
| Nguồn HLS và chiến lược ảnh | Một provider S30 v2, xác thực qua kho hệ điều hành; khảo sát 2–3 năm và coverage/ngày/composite theo [mục 7.5](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md#muc-7-5) | GIS/data + chủ nghiệp vụ, G0 | Chốt mùa/AOI/coverage tối thiểu; L30 hoặc composite đổi profile phải kiểm định lại |
| Ngân sách thử và điểm dừng | Ngưỡng tuyệt đối, số vòng tối đa, trần thời gian/chi phí và người quyết định theo [mục 8.5](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-5); RF là đối chứng | Chủ dự án + chủ nghiệp vụ + ML, G0 | Hết ngân sách chưa đạt thì hoãn/thu hẹp hoặc phê duyệt thay đổi; không hạ gate hồi tố hay tự bỏ yêu cầu Prithvi |
| AOI, volume và lịch sử | Một vùng đại diện có cả ca khó; một tập nhỏ và một tập stress | GIS/data + kỹ thuật, G0 | Quyết định chunk, cache, dung lượng và benchmark |
| Class schema và chất lượng | Chốt theo mục đích sử dụng, không dùng danh sách lớp toàn cầu mặc định | Chủ nghiệp vụ + chuyên gia, G0 | Model/review/report phải có version tương ứng |
| Phương pháp toán–vật lý | GEO-01 cho đo/thống kê bản đầu; chọn từng PHY theo [mục 8.6](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-6) khi mở domain | GIS/ML + chuyên gia ngành + chủ nghiệp vụ; GEO-01 tại G0, PHY trước feature G4 | Chốt đại lượng, dữ liệu/đơn vị, solver/hệ số, calibration/test, uncertainty và ngân sách; không coi ảnh HLS là đủ cho mọi tham số vật lý |
| Phần cứng và CPU SLO | Windows x64; CPU reference/RAM/đĩa, thời gian job tối đa cho workload; một NVIDIA reference | Kỹ thuật + chủ dự án, G0; kiểm chứng G1 | Quyết định profile Prithvi, batch, runtime và phạm vi AOI hỗ trợ |
| Repository và migration | SQLAlchemy/Alembic theo [mục 5.2](04_kien_truc_thuc_thi_va_module.md#muc-5-2); SQLite trước, PostgreSQL khi làm server | Kỹ thuật, G1 | Version/constraint/upgrade/restore phải có fixture; không mở rộng CI hai database chỉ để giữ chỗ |
| Ngân sách viewer | Đề xuất p95 ≤ 33 ms trên scene/viewport cố định theo [mục 11](10_viewer_gis_3d_va_kiem_tra_ket_qua.md#muc-11), đối chiếu cấu hình ứng viên [mục 13.3](12_runtime_cpu_nvidia_va_hieu_nang.md#muc-13-3) | GIS/UI + chủ dự án, G0/G1 | Chốt tải hiển thị và AI đồng thời; không suy hiệu năng từ tổng polygon hoặc dung lượng VRAM |
| CRS/VN-2000 | Registry backend, TransformSpec, danh sách CRS và điểm khống chế/tolerance | GIS + đơn vị dữ liệu, G0/G1 | Tài nguyên chuyển datum offline và đường reprojection viewer |
| Định dạng đầu vào bản đầu | COG/GeoTIFF, GeoPackage/GeoJSON, DEM và COPC fixture | GIS + kỹ thuật, G0–G1 | Kích thước core và dependency native |
| Mức chỉnh sửa kết quả | Sửa thuộc tính/feedback; hình học qua QGIS rồi nhập GeoPackage | Nhóm người dùng, G0 | Không xây editor tổng quát; phải kiểm tra revision/representation khi nhập |
| Quy trình báo cáo chính thức | Hai trạng thái unreviewed/reviewed; PDF chính thức yêu cầu reviewed | Chủ nghiệp vụ, trước G2 | Chưa có nhiều cấp phê duyệt; sửa thì duyệt lại |
| Lưu trữ và retention | Project/cache/staging local; pin theo job hoặc run giữ offline, quota và thời hạn resume | Chủ dự án + kỹ thuật, G0/G3 | Dung lượng, tái lập, GC và quy trình chuyển dữ liệu mạng vào local |
| Offline và phân phối | NSIS Standard trước, Offline sau khi có đủ pack; MSI khi có nhu cầu | Đơn vị triển khai, G1–G3 | WebView2, font, dữ liệu nền, ký và cập nhật |
| Định dạng trọng số và nguồn tin cậy | Chuyển `.pt` trên build cô lập sang ONNX/safetensors; manifest ký và provenance chuyển đổi theo [mục 14.3](13_stack_va_bo_cai_windows.md#muc-14-3) | Kỹ thuật/ML, G1; kiểm chứng lại checkpoint G2/G3 | Ngoại lệ `.pt` phải có lý do, `weights_only=True` và runtime đã vá; không nạp code/pickle tùy ý |
| Nhu cầu server | Kích hoạt khi có chia sẻ tài nguyên/dữ liệu hoặc nhiều người dùng | Chủ dự án, sau G2 hoặc khi yêu cầu đổi | Auth, queue, storage, vận hành và chi phí |
| Nhân sự/ngân sách/thời hạn | Ước lượng sau G0/G1 theo work package | Chủ dự án + nhóm triển khai | Quy mô đầy đủ còn lớn; chưa có cơ sở cam kết lịch |
| Chủ sở hữu model nghiệp vụ | SPEC-008 tạo dataset/split/recipe/checkpoint/evaluation/pack; SPEC-006 tiêu thụ và kiểm tích hợp | GIS/data + ML + reviewer độc lập + chủ nghiệp vụ; ghi tên/phân công khi nhận task | Không coi checkpoint tự xuất hiện; recipe/budget/gate phải được chốt trước thực thi phần phụ thuộc |
| Đồng thời nhiều project/instance | ADR-011 đề xuất một execution owner/tài khoản Windows trên máy và một job nặng; instance khác chỉ đọc/báo bận | Kỹ thuật kiểm khóa/recovery xuyên session G1; chủ dự án chốt phạm vi hỗ trợ | Khóa project không đủ; nhiều tài khoản hoặc broker toàn máy cần yêu cầu/ADR riêng |

<a id="muc-17-1"></a>

### 17.1. Sổ quyết định kiến trúc (ADR)

Sổ dưới định danh các quyết định cần quản lý, không tự nâng các đề xuất thành thiết kế đã đo hoặc đã nghiệm thu. Yêu cầu Prithvi từ bản đầu đã được xác nhận; các lựa chọn kỹ thuật vẫn phải qua cổng tương ứng. Mỗi hồ sơ ghi bối cảnh, lựa chọn, phương án đã cân nhắc, hệ quả, chủ trì/người chốt, ngày, bằng chứng và điều kiện xem lại. Theo yêu cầu tổ chức tài liệu cho AI/dev, hồ sơ chính thức đặt tại [Artchitect/docs/adr](../docs/adr/README.md), thay đường `Artchitect/plans/adr/` từng được đề xuất. ADR-001–008 giữ mã cũ; ADR-009/010 cụ thể hóa IPC/attempt và mô hình toán–vật lý đã có trong v1.4, không tự nâng trạng thái thành đã nghiệm thu.

| Mã | Chủ đề | Trạng thái hiện tại | Điều kiện chốt/xem lại |
| --- | --- | --- | --- |
| ADR-001 | Windows desktop trước; server khi có nhu cầu | Định hướng kế thừa; động lực/ràng buộc triển khai cụ thể cần chốt G0 | Xác định offline, dữ liệu ở local, số máy và nhu cầu chia sẻ theo [mục 1.2](01_dinh_huong_san_pham.md#muc-1-2); mở server theo nhu cầu G4 |
| ADR-002 | SQLite WAL, SQLAlchemy và Alembic | Lựa chọn thiết kế đề xuất | Một writer, migration/restore G1; khi có server kiểm chứng PostgreSQL, không đổi ngầm semantics |
| ADR-003 | Giro3D và adapter viewer phạm vi hẹp | Lựa chọn thiết kế có điều kiện | Fixture CRS, codec/COG/COPC, xác thực, offline và hiệu năng G1; chỉ đổi/thêm engine khi có bằng chứng |
| ADR-004 | CPU chính thức, NVIDIA tùy chọn, ưu tiên ONNX | Lựa chọn thiết kế có điều kiện | Workload G0, spike G1 và checkpoint nghiệp vụ G2; giữ ngoại lệ PyTorch cả CPU/CUDA theo [mục 13](12_runtime_cpu_nvidia_va_hieu_nang.md#muc-13) |
| ADR-005 | Backend quản lý CRS và TransformSpec | Lựa chọn thiết kế đề xuất | Điểm khống chế, phép chuyển/grid offline và frontend tương đương theo [mục 7.4](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md#muc-7-4); backend reprojection khi cần |
| ADR-006 | Pixi và cách đóng gói sidecar/pack | Lựa chọn thiết kế đề xuất | Khóa dependency, so phương án đóng gói bằng fixture máy sạch G1/G3; không suy đủ DLL/data từ công cụ quản lý gói |
| ADR-007 | PDF Typst từ revision/metrics snapshot | Lựa chọn thiết kế đề xuất | PDF tiếng Việt offline, provenance và representation đúng, revision đã duyệt theo [mục 12](11_revision_domain_pack_va_bao_cao.md#muc-12) |
| ADR-008 | Prithvi-EO-2.0 dùng cho phân tích từ bản đầu | Yêu cầu đã xác nhận; biến thể/decoder còn cần kiểm định | Chốt profile/nhãn/gate và điểm dừng G0; xác nhận checkpoint thật G2; không chuyển yêu cầu thành model tùy chọn |
| ADR-009 | JSON-RPC local và fencing theo attempt | Lựa chọn thiết kế đề xuất; wire draft 0.1.0 chưa có transport | Kiểm framing/native log, cancel/retry/crash và stale attempt ở G1; idempotency không thay fencing |
| ADR-010 | Mô hình toán–vật lý theo Domain Pack | Lựa chọn thiết kế đề xuất; GEO-01 bản đầu, PHY chọn từng feature G4 | Dữ liệu/đơn vị/hiệu chuẩn, solver/uncertainty và gate riêng trước phát hành feature |
| ADR-011 | Quyền thực thi local dùng chung giữa project/instance | Đề xuất có điều kiện; một phiên sở hữu cho mỗi tài khoản Windows trên máy | G1 kiểm khóa liên session/process, hai project tranh tài nguyên, crash/worker còn sống và recovery; chưa hỗ trợ nhiều tài khoản cùng compute |
| [ADR-012](../docs/adr/ADR-012-ubuntu-desktop.md) | Mở rộng desktop Ubuntu 22.04/24.04 LTS | Mục tiêu OS đã xác nhận; adapter/packaging còn đề xuất | UB-01–20, review kỹ thuật và bằng chứng hai LTS; không thay acceptance Windows hoặc server G4 |

ADR dự thảo được sửa có lịch sử. Khi quyết định đã được chấp thuận thay đổi, tạo ADR mới liên kết hồ sơ cũ và đánh dấu trạng thái bị thay thế; giữ nguyên nội dung quyết định/bằng chứng lịch sử. Cập nhật bản tổng hợp và toàn bộ tài liệu chuyên biệt chịu ảnh hưởng trong cùng phiên bản. Chưa tạo các file ADR chỉ có tiêu đề hoặc ghi quyết định chưa được chốt là đã chấp thuận.

<a id="muc-18"></a>

## 18. Những đánh đổi được chấp nhận

- SQLite giảm công việc cài đặt nhưng cần coordinator local được thiết kế và kiểm tra kỹ; giới hạn một máy/một writer là chủ ý.
- Giro3D có hướng đọc dữ liệu phù hợp nhưng bộ công cụ biên tập/nhãn phải qua fixture; việc đổi engine có chi phí và không được che bằng lớp abstraction quá lớn từ đầu.
- CPU/NVIDIA thu hẹp số tổ hợp phải kiểm chứng; máy AMD/Intel vẫn dùng CPU và GPU đồ họa, nhưng chưa có tăng tốc AI tương đương.
- Prithvi-EO-2.0 là yêu cầu từ bản đầu, làm tăng công việc dữ liệu, decoder, CPU benchmark và đóng gói. Giữ một feature và một profile model được kiểm chứng để kiểm soát phạm vi; không hứa model nền giải quyết mọi bài toán.
- ONNX Runtime là ưu tiên phân phối, nhưng PyTorch được giữ khi cần bảo toàn tính đúng. INT8 là thử nghiệm có điều kiện; dung lượng và tốc độ phải đo trên pack/model cụ thể.
- Model package và revision tăng lượng metadata, đổi lại giúp kiểm tra, phục hồi và lập báo cáo đúng nguồn. Chỉ lưu probability/checkpoint cần thiết theo retention và nhu cầu nghiệp vụ.
- Một feature hoàn chỉnh tạo nền dùng lại tốt hơn triển khai nông nhiều ngành; các domain mở rộng phải có người phụ trách dữ liệu và kiểm định.
- Tham khảo sản phẩm thị trường giúp làm rõ trải nghiệm và hợp đồng, không thay thế thử nghiệm trên dữ liệu Việt Nam hoặc dữ liệu của người dùng.

---

**Tài liệu liên quan:**

- [Định hướng sản phẩm và cấu hình triển khai](01_dinh_huong_san_pham.md)
- [Phạm vi bản đầu và luồng sử dụng](03_pham_vi_ban_dau_va_luong_su_dung.md)
- [Model Prithvi, dữ liệu nhãn và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md)
- [Lộ trình và cổng nghiệm thu](15_lo_trinh_va_cong_nghiem_thu.md)
