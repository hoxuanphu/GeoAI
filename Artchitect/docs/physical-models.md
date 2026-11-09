# Mô hình toán–vật lý và điểm tích hợp

Đọc khi làm feature vật lý, solver hoặc hiệu chuẩn. Nguồn phương trình, đơn vị và phạm vi đối chiếu nằm tại [mục 8.6–8.9](../plans/07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-6). ADR-010 giữ quyết định tích hợp theo Domain Pack. Chưa có solver/hiệu chuẩn thực địa.

| ID | Phương pháp/đầu ra | Dữ liệu và giới hạn |
| --- | --- | --- |
| GEO-01 | NDVI/EVI/NDMI/MNDWI đã chọn cho đợt đầu, diện tích/coverage | HLS QA + grid/AOI/nhãn; dùng trong G0–G2, chỉ số không tự là đại lượng vật lý tuyệt đối |
| PHY-01 | PROSPECT-D + 4SAIL/PROSAIL, LAI/chlorophyll | SRF, góc, tán/đất/prior, đo thực địa; sáu band không nhận dạng mọi tham số |
| PHY-02 | FAO-56 Penman–Monteith ET0/ETc | Khí tượng/bức xạ/gió 2m/Kc; ETc chuẩn chưa là ET thực khi stress |
| PHY-03 | SEBAL/cân bằng năng lượng, ET thực | LST/nhiệt + khí tượng/albedo/emissivity/nhám; HLS S30 sáu band không có thermal |
| PHY-04 | SCS-CN, Q mm/thể tích m³ | Mưa, đất/sử dụng đất/ẩm/CN/lambda; chưa là hydrograph/mực ngập |
| PHY-05 | HAND/kịch bản địa hình ngập | Routing DEM/mạng thoát nước/datum/mực nước; không dùng sông gần nhất Euclid, chưa là động lực lũ |
| PHY-06 | Nước nông 2D, độ sâu/vận tốc theo thời gian | Bathymetry, lưới, biên/đầu/nhám/công trình; solver kiểm khối lượng, wetting–drying, lưới/CFL |
| PHY-07 | RUSLE A=R×K×LS×C×P | Nguồn hệ số/đơn vị tương thích; mất đất tấm/rãnh nhỏ dài hạn, chưa là sediment yield cửa ra |
| PHY-08 | Chave 2014 allometry và carbon | D cm/H m/gỗ g·cm⁻³, kiểm kê/ô mẫu/f_C; HLS không trực tiếp đo từng cây, carbon tồn trữ chưa là tín chỉ |

Các PHY ở G4, chọn từng feature theo dữ liệu/nhu cầu. SCS-CN, RUSLE/allometry bán thực nghiệm và HAND địa hình phải được gắn đúng loại; không gọi mọi công thức là mô hình bảo toàn vật lý đầy đủ.

[G0-D05](evidence/g0/decision-record.md) xác nhận bốn chỉ số đầu; chỉ tiêu định lượng chuyên sâu bổ sung sau. EVI ba band dùng `2.5 × (rho_NIR − rho_Red) / (rho_NIR + 6×rho_Red − 7.5×rho_Blue + 1)` với reflectance đã scale/offset về đơn vị không thứ nguyên; hằng số `1` không tương thích việc dùng DN chưa scale. Mapping HLS theo profile đã khóa, mẫu số gần 0 và band/QA không hợp lệ phải mask, không trả 0 hoặc tự chuyển sang EVI2. Chi tiết cùng giới hạn nằm trong GEO-01 của tài liệu nguồn; chưa có implementation/test thực thi.

Luồng: InputSnapshot → kiểm biến/đơn vị/grid/datum/kỳ tích lũy → PhysicalModelSpec + parameter snapshot → worker/solver → kiểm miền/cân bằng/hội tụ/uncertainty → publish/review/report. Analytics chứa phép tính/adapter, geoprocessing chuẩn hóa, domains chọn phương pháp, jobs/compute cấp ngân sách. Không đưa script/executable tùy ý từ project vào runtime.

Mỗi spec khóa implementation/solver hash/version, biến/đơn vị, range/miền, điều kiện đầu/biên, nguồn hệ số, calibration/evaluation và uncertainty policy. Phân biệt tham số đo, từ tài liệu và fit; không điền 0 cho forcing thiếu. Solver liên kết không gian/thời gian chỉ resume native checkpoint đã kiểm chứng; nếu không thì khai báo không hỗ trợ và chạy lại.

Split calibration/validation/test độc lập theo vùng/mùa/sự kiện/ô mẫu. Đánh giá đúng đại lượng: ET0 khác ET thực, lượng dòng chảy khác lưu lượng, HAND khác mực nước, AGB khác carbon. Monte Carlo có seed/số mẫu/phân phối/tương quan, hoặc Var(y)≈JΣJᵀ khi gần tuyến tính; không gọi dải kịch bản là khoảng tin cậy. Sai số AI đầu vào phải truyền xuống model vật lý; simulation không tự thành ground truth. PINN là nghiên cứu riêng, chưa là dependency.

Mã nháp PhysicalModelSpec mới mô tả kiểu và một số invariant; bộ contracts chưa hoàn tất/kiểm chứng. Schema không chứng minh solver bảo toàn, tham số nhận dạng được hoặc có validation địa phương. Feature phải qua gate riêng trước phát hành, kể cả khi người dùng đã reviewed kết quả.

## Kiểm tra tối thiểu trước khi lập spec từng PHY

| Nhóm | Ca kiểm cần giữ trong spec feature |
| --- | --- |
| GEO-01 | Chỉ số phổ mask mẫu số không hợp lệ; diện tích lớp + chưa quan sát khớp AOI, không đếm chồng mosaic; đơn vị m²/ha và phương pháp cắt biên |
| PHY-01 | Forward spectrum đối chiếu nguồn; inverse trên dữ liệu độc lập, prior/range và khả năng nhận dạng; tích phân SRF đúng sensor |
| PHY-02/03 | Ví dụ chuẩn đúng kỳ ngày/giờ, gió/áp suất/bức xạ/đơn vị; phân biệt ET0/ETc/ET thực; PHY-03 thiếu nhiệt thì chặn |
| PHY-04/05 | SCS-CN mưa dưới ngưỡng cho Q=0, Q không vượt mưa trong giả thiết; HAND nối theo routing đúng và mực nước cùng datum, không suy vận tốc lũ |
| PHY-06 | Lake-at-rest, bảo toàn khối lượng có biên/mưa/thấm, độ sâu không âm, wetting–drying, CFL/hội tụ lưới/thời gian; cancel/resume native và sai hash checkpoint |
| PHY-07/08 | Hệ số/đơn vị phương trình có nguồn, kiểm số học và phạm vi; validation mất đất/ô mẫu phù hợp, truyền sai số đầu vào; không đổi AGB thành carbon khi chưa có f_C |

Spec PHY cụ thể phải khóa đại lượng đầu ra, phương trình/profile, forcing/parameter/biên, implementation/solver tin cậy, kiểm số và kiểm thực địa, gate/ngân sách, uncertainty và license. [Nguồn phương trình](../plans/07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-7) giữ chi tiết toán học; không chép công thức rút gọn rồi bỏ giả thiết/đơn vị. Chưa chọn PHY nào để code, chưa có dữ liệu hoặc solver đủ điều kiện nghiệm thu G4.
