# SPEC-006 — Luồng nghiệp vụ lớp phủ tới PDF

**Trạng thái:** chưa triển khai; phụ thuộc G0 đóng, G1 phù hợp và model pack nghiệp vụ từ SPEC-008. **Mục tiêu:** một feature thực chạy đầu-cuối trên CPU reference và NVIDIA nếu chọn phân phối pack, kết quả/revision/PDF truy nguyên được.

Input: G0 decision/dataset/class schema, checkpoint Prithvi+decoder đã huấn luyện, evaluation/split/license, runtime/bundle G1, contracts/job/review foundation. Output dự kiến: workflow lớp phủ đăng ký tĩnh, baseline RF/boosting, UI workspace/review, GEO-01/metrics, report Typst/font và evaluation/model pack nghiệp vụ.

Phần G1 phụ thuộc gồm SPEC-003/004/005 và các ca GIS/viewer/report/bundle tương ứng của [SPEC-007](007-g1-platform-validation.md), không chỉ export thành công. Luồng cần service tạo snapshot/revision/metrics/report theo contracts và kiểm project/reference/readiness; không cho UI ghép payload tự khai reviewed/business để bỏ qua kiểm tra.

[SPEC-008](008-training-evaluation-model-pack.md) là task tạo dataset/split/recipe/checkpoint/evaluation/model pack đầu vào; SPEC-006 chỉ tích hợp và đánh giá lại trong workflow cuối, không coi training tự phát sinh. SPEC-009 phải đạt phần importer/resolver dùng trong feature; execution tuân ADR-011. Không cần đợi G1 UI hoàn chỉnh mới bắt đầu chuẩn bị nhãn/training đủ dependency, và chưa bắt buộc NVIDIA như điều kiện của bản CPU.

## Acceptance

- Phạm vi người dùng đã chốt trong [G0-D02/D05](../evidence/g0/decision-record.md): đợt đầu có lớp phủ HLS 30 m và NDVI/EVI/NDMI/MNDWI, thống kê/PDF; profile 10/5/1 m và các nghiệp vụ rừng/ngập bổ sung sau, không tự đưa vào task này.
- AOI chọn bằng vẽ/footprint ảnh import/Shapefile theo [AOI policy](../aoi-policy.md), xác nhận geometry/CRS và cố định snapshot trước chạy; valid mask không tự thu nhỏ AOI. Dùng [bảy lớp IDs 0–6](../landcover-taxonomy.md), `-1` là ignore; lớp 4 wetland/mangrove có trong bản đồ đầu, còn giám sát ngập chuyên biệt ở đợt sau. Pack nghiệp vụ T=3 phải được kiểm riêng, không dùng kết quả spike T=1 để nghiệm thu.
- Import local/STAC HLS → InputSnapshot → Prithvi nghiệp vụ → raster/QA/coverage → revision/review → metrics theo vùng → PDF tiếng Việt offline.
- G2 chạy lại export/tolerance/precision/benchmark với checkpoint thật; ngưỡng tuyệt đối theo lớp, coverage và CPU budget G0 đạt. So RF/boosting trên cùng test split, không bắt buộc thắng RF.
- Áp [tiêu chí nghiệm thu](../acceptance-criteria.md) theo protocol/version được khóa trước đo: đủ bảy lớp và macro/OA, coverage thực đủ ba frame, diện tích/CI/CRS và tài nguyên. Số đo thiếu mẫu/máy/protocol là chưa đủ bằng chứng; SLA GPU 15 phút/tile không thay CPU SLO. Report tách diện tích bản đồ/ước lượng hiệu chỉnh/vùng không quan sát và không dùng pixel imputation làm quan sát thật.
- Sửa tạo revision chưa duyệt; vector QGIS không âm thầm sửa raster; metrics/report chọn representation/revision có thẩm quyền. Official chỉ reviewed, snapshot PDF cũ không đổi khi rerun.
- GEO-01 có NDVI/EVI/NDMI/MNDWI đúng reflectance/mapping/mask; EVI giữ đúng scale và hằng số, output dimensionless. Diện tích/coverage đúng AOI/mask/đơn vị; vùng không quan sát ghi riêng; confidence chưa là khoảng tin cậy.
- Cancel/retry/restore không công bố output thiếu hoặc attempt cũ. Model pack có conversion/runtime/evaluation/license/hash, chỉ checkpoint business được bật cho feature nghiệp vụ.

## Test phải có

`tests/e2e/test_landcover_workflow.py`: dataset nhỏ có nhãn thật chạy tới PDF, artifact/provenance/reference checks. `tests/review/test_revisions.py`: parent/edit/review reset, vector/raster authority và report cũ. `tests/reports/test_offline_report.py`: tiếng Việt/units/acquisition vs run/report dates và số liệu khớp snapshot. Evaluation độc lập per-class và workload đại diện lưu manifest/báo cáo riêng, không biến synthetic schema fixture thành golden ML.

G2 chưa đạt sau budget thì áp dụng điểm dừng G0. Installer/máy sạch/support matrix G3 và model toán–vật lý/server G4 là task sau với spec riêng; không kéo vào feature đầu khi chưa có nhu cầu.
