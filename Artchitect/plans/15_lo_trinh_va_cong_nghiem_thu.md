# Lộ trình và cổng nghiệm thu

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** G0–G4, ma trận kiểm chứng bắt buộc và hồ sơ benchmark.

<a id="muc-16"></a>

## 16. Lộ trình và cổng nghiệm thu

Đã ghi bộ số ngưỡng do người dùng cung cấp tại [tiêu chí nghiệm thu](../docs/acceptance-criteria.md); SPEC-002 còn khóa protocol/máy/CI/budget và thu đầu vào thực. G0 chưa hoàn tất; training/benchmark chỉ chạy khi đủ dependency tương ứng, không tự coi “vòng thử ở G0” là cho phép fine-tune trước gate. G2 cần số đo thật theo version đã khóa, gồm CPU SLO riêng và các tiêu chí chất lượng/coverage/diện tích/CRS phù hợp.

Thứ tự đã xác nhận: HLS 30 m với lớp phủ, NDVI/EVI/NDMI/MNDWI, thống kê và PDF trước; rừng/mất rừng, đất ngập nước/ngập lụt và profile 10/5/1 m sau. Đây là phạm vi chia đợt, chưa có lịch/ngân sách đợt sau; G0 vẫn chờ AOI/thời gian, bộ lớp/nhãn, nguồn truy cập thực, CRS/gate/workload và người chịu trách nhiệm. Chọn chỉ số không tự nghiệm thu công thức/profile hoặc số đo nghiệp vụ.

| Giai đoạn | Đầu ra | Điều kiện chuyển tiếp |
| --- | --- | --- |
| **G0 — Đặc tả một nghiệp vụ** | So sánh phương án [mục 4.1](03_pham_vi_ban_dau_va_luong_su_dung.md#muc-4-1); khảo sát HLS 2–3 năm theo [mục 7.5](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md#muc-7-5), thử truy cập/credential; bắt đầu nhãn/split; ứng viên Prithvi/decoder; CRS/VN-2000; CPU workload và quality gate | Chốt một feature, nguồn/profile/mùa/coverage tối thiểu, kế hoạch nhãn và fixture; có giá trị cụ thể cho ngưỡng chất lượng, thời gian/RAM và ngân sách/số vòng/quy tắc dừng theo [mục 8.5](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-5). Không yêu cầu đã hoàn tất gán nhãn để bắt đầu spike G1 |
| **G1 — Kiểm chứng rủi ro nền tảng** | Spike Prithvi + decoder đúng kiến trúc, có thể ngẫu nhiên, theo [mục 13.2](12_runtime_cpu_nvidia_va_hieu_nang.md#muc-13-2); ONNX/dynamic INT8 có điều kiện; Windows bundle/model conversion; CRS và AOI cắt 108°E; JSON-RPC/native logging; COG/DEM/COPC; PDF/offline | Có đường tham chiếu và fixture kỹ thuật có version; sàng lọc runtime/biến thể, tolerance và packaging từ số đo; ghi lý do nếu dùng PyTorch. Lựa chọn model/runtime còn sơ bộ khi thiếu checkpoint nghiệp vụ; gán nhãn tiếp tục song song |
| **G2 — Một luồng hoàn chỉnh** | Import/STAC → snapshot → Prithvi nghiệp vụ → review hai trạng thái → metrics → PDF; đối chứng baseline, hủy/khôi phục job; chạy lại export/precision/benchmark với checkpoint thật | Có nhãn/test độc lập và golden output nghiệp vụ; đạt ngưỡng tuyệt đối, coverage và ngân sách CPU đã chốt, không bắt buộc thắng RF; NVIDIA đạt tương đương nếu chọn phân phối pack NVIDIA. Provenance gồm backbone/decoder, conversion và phép chuyển CRS; không đạt thì áp dụng điểm dừng [mục 8.5](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-5) |
| **G3 — Hoàn thiện phát hành local** | Model/compute pack; log/chẩn đoán, retention/pin; backup/restore; upgrade/uninstall; profile Offline; support matrix | Vượt kiểm tra trên máy sạch, có Prithvi + decoder thực chạy offline, không mất nguồn đang bảo vệ hoặc artifact |
| **G4 — Mở rộng chọn lọc** | Feature/domain/nguồn/model mới theo nhu cầu; chọn từng model toán–vật lý [mục 8.6](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-6) với PhysicalModelSpec, dữ liệu hiệu chuẩn và uncertainty; hoặc server nếu nhu cầu chia sẻ ưu tiên hơn | Mỗi mở rộng có fixture, chất lượng, miền hiệu lực và ngân sách riêng; model vật lý qua [mục 8.9](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-9) trước phát hành, không nhân rộng giả định chưa kiểm chứng |

Khả năng import và chạy thư viện lõi trên Linux có thể được kiểm tra sớm để phát hiện phụ thuộc Windows. Nghiệm thu sản phẩm server/Linux là phạm vi riêng ở G4, không phải điều kiện bắt buộc hoàn thiện mọi chức năng server trước khi phát hành desktop.

Bổ sung ánh xạ task sau review: G1 cần bằng chứng execution owner theo ADR-011 và importer/resolver SPEC-009, bên cạnh shell/job/Prithvi/GIS/viewer/PDF/bundle. SPEC-008 chuẩn bị nhãn/recipe/training song song G1 khi đủ input/budget, cung cấp checkpoint/evaluation/model pack cho SPEC-006 kiểm workflow G2. CPU là cấu hình chính thức; kiểm NVIDIA để phân phối pack NVIDIA, không tự biến pack tùy chọn thành điều kiện bắt buộc của bản CPU. Các task contracts/shell/job/resolver dùng fixture được chỉ rõ có thể làm trước G0; chưa tự cho toàn nghiệp vụ được nghiệm thu.

<a id="muc-16-1"></a>

### 16.1. Ma trận kiểm chứng bắt buộc

| Nhóm | Bài kiểm tra | Kết quả cần chứng minh |
| --- | --- | --- |
| Execution owner local | Hai project/instance/session cùng tài khoản, namespace/ACL, owner crash nhưng worker còn sống, chuyển project/model resident | Một phiên sở hữu và một job nặng trong phạm vi hỗ trợ; thu hồi token không thay xác nhận giải phóng compute; chưa điều phối nhiều tài khoản |
| Importer/resolver | Ma trận IMP/NET/RES của SPEC-009: archive/reparse/limits/VRT, network/redirect, bootstrap/context và candidate khác project/attempt | Chặn truy cập vượt policy, input ngoài project đã đăng ký vẫn hợp lệ, không lộ secret hoặc publish file chưa kiểm; context và lease được kiểm trước dùng |
| Training/model nghiệp vụ | SPEC-008: dataset/split/recipe/checkpoint selection, test độc lập, RF đối chứng, conversion/runtime/license/promotion | Có đầu ra thực cho SPEC-006, không dùng test để tinh chỉnh hoặc business readiness tự khai; đạt gate tuyệt đối và ngân sách đã chốt |
| Địa lý | CRS/axis/transform, VN-2000 mục tiêu, grid thiếu, frontend/backend và điểm khống chế độc lập; fixture HLS cắt UTM 48N/49N tại 108°E; band/scale, NoData/QA, reference grid, diện tích, datum đứng | Đạt tolerance đã chốt; mosaic về GridSpec đích không lệch đường nối hoặc đếm trùng; không fallback datum âm thầm; round-trip không thay điểm chuẩn |
| Module/repository | Hướng import theo package thực, phụ thuộc vòng; SQLite repository contract, Alembic migration trên dữ liệu cũ và restore khi gián đoạn | Không import ngược bootstrap hoặc rò session/ORM qua IPC; migration giữ constraint/index và dữ liệu, chỉ một writer; PostgreSQL kiểm chứng riêng khi làm server |
| HLS/access/coverage | Provider/collection đã chọn, đọc sáu band/QA, xác thực/hết hạn/làm mới; khảo sát theo ngày/tháng trong 2–3 năm và recipe composite | Phân biệt metadata công khai với quyền đọc asset, ngày tốt nhất với coverage hợp; không lộ credential; coverage thực đáp ứng chiến lược ảnh, lưu đủ scene/ngày |
| AI/Prithvi | HLS S30/L30 theo profile phát hành, sáu band/scale/QA, metadata TL/non-TL, shape/T, backbone + decoder; baseline và split độc lập | Model nghiệp vụ thực chạy và đạt quality gate tuyệt đối; phát hiện sai band/GSD/thời gian; không dùng reconstruction hoặc decoder ngẫu nhiên thay segmentation đã kiểm định |
| Toán–vật lý theo feature | GEO-01 ở G1/G2; các PHY ở G4: ví dụ công thức/đơn vị độc lập, calibration/test, mask/miền hiệu lực, cân bằng/hội tụ và độ bất định theo [mục 8.9](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-9) | Không nhầm đại lượng/đơn vị hay dùng input thiếu; PhysicalModelSpec/parameter/forcing/solver truy nguyên được; kiểm chứng số học không thay validation thực địa |
| CPU/NVIDIA | Cùng fixture nghiệp vụ; golden tensors/output; ONNX/PyTorch và precision được phân phối | CPU đạt ngân sách thời gian/RAM của workload; GPU đạt tolerance và quality gate; công bố cold/warm và giới hạn |
| Dữ liệu lớn | COG/COPC Range, chunk, overviews, mạng chậm/URL hết hạn | Đọc có giới hạn; RAM/đĩa tạm nằm trong ngân sách; không đổi input snapshot |
| Job | Crash ở từng giai đoạn, mất heartbeat, cancel, retry, coordinator restart; đóng bình thường, shell crash và force-kill nhóm Windows Job Object | Attempt cũ không publish; output thiếu không succeeded; không còn worker mồ côi; chỉ resume checkpoint hợp lệ, không coi kill là dừng đúng checkpoint |
| IPC | Worker đang infer vẫn nhận cancel; log Python/CRT/Win32 khi bootstrap/import và inference trong sidecar Windows; UTF-8/LF, stdout lạc dữ liệu, partial/oversized message, stderr đầy, timeout và pipe đóng | Protocol không nhiễm log native hoặc đổi framing; phát hiện vi phạm rõ; không treo vì log/progress; không truyền tensor JSON hoặc nhận kết quả từ attempt cũ |
| Revision/report | Hai trạng thái duyệt; sửa thuộc tính, nhập geometry từ QGIS, đổi threshold, rerun, report lại | Sửa tạo revision chưa duyệt; bản gốc giữ nguyên; metrics/bản đồ/PDF chọn đúng representation/revision |
| Viewer | DEM/COPC/vector lớn, COG phân tích/hiển thị và codec/overviews/QA, WASM local; đóng/mở layer, AI đồng thời | Ghi p95 frame time theo scene/viewport/máy đã chốt; không rò tài nguyên; dùng chung COG khi tương thích, display artifact không thay dữ liệu đo/phân tích |
| Bảo mật desktop | Host/Origin sai, token thiếu/sai/hết phiên; API, SSE, tile và Range qua loader/web worker; khởi động lại ứng dụng | Từ chối truy cập trái policy, không lộ token qua URL/log; đường loader hợp lệ vẫn chạy có xác thực trên bản đóng gói |
| Offline | Ngắt mạng, máy sạch, font/decoder viewer, Prithvi + decoder nghiệp vụ, runtime và input đầy đủ | Cài và chạy feature Prithvi đến PDF không yêu cầu CDN/PATH/cache bên ngoài |
| Installer | Tài khoản thường, đường dẫn tiếng Việt/khoảng trắng, thiếu đĩa, upgrade bị gián đoạn | Phục hồi được; không mất project; chỉ phát hành tổ hợp đã kiểm tra |
| Model pack | Revision/hash/chữ ký, checkpoint nguồn và artifact đã chuyển, `weights_only=True` với ngoại lệ `.pt`, giới hạn kích thước và runtime đã vá | Từ chối pack/manifest không tin cậy hoặc sai hash; không tự fallback pickle không hạn chế; output sau chuyển đổi đạt tolerance, chỉ phân phối model nghiệp vụ đạt gate |
| Backup | Restore metadata và project trên thư mục/máy khác | Mở được artifact/report; chỉ rõ nguồn ngoài chưa được kèm |
| Retention/storage | GC đồng thời nhận job, lease sau crash, hết quota, nguồn mạng mất/đổi; export/restore run được giữ offline | Không xóa dữ liệu đang pin; tái lập không cần nguồn ngoài khi đã công bố đủ offline; project ghi ở local |
| Hỗ trợ | Crash native, lỗi runtime/CRS, xuất gói chẩn đoán và log rotation | Tìm được lỗi theo job/attempt; không lộ secret/dữ liệu mặc định; không tự gửi ra ngoài |
| Server khi có | Quyền API/tile/asset/export, quota, concurrent claim, object storage | Không vượt quyền; không công bố trùng; kết quả tương đương trong tolerance |

Benchmark lưu cấu hình máy/driver, app/backbone/decoder/runtime version, dataset hash, cold/warm time, compile time, tổng thời gian job, peak RAM/VRAM, byte đọc, đĩa tạm và ảnh hưởng UI. G0 đặt ngân sách theo nhu cầu sử dụng; G1 xác nhận khả thi hoặc điều chỉnh có lý do trước G2. Không chỉ đo rồi ghi nhận mà thiếu điều kiện đạt/không đạt. Chưa cam kết FPS, phút/km² hoặc dung lượng bộ cài trước khi có dữ liệu và phép đo.

---

**Tài liệu liên quan:**

- [Phạm vi bản đầu và luồng sử dụng](03_pham_vi_ban_dau_va_luong_su_dung.md)
- [Model Prithvi, dữ liệu nhãn và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md)
- [Runtime CPU/NVIDIA và hiệu năng](12_runtime_cpu_nvidia_va_hieu_nang.md)
- [Stack và bộ cài Windows](13_stack_va_bo_cai_windows.md)
- [Quyết định cần chốt và đánh đổi](16_quyet_dinh_can_chot_va_danh_doi.md)
