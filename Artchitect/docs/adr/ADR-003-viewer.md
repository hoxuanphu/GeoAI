# ADR-003: Giro3D và adapter viewer phạm vi hẹp

**Trạng thái:** Đề xuất có điều kiện fixture G1. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../architecture.md).

## Bối cảnh

Viewer cần GIS 2D/3D, DEM COG, COPC và CRS địa phương, giữ state ứng dụng qua panel.

## Lựa chọn

Giro3D phiên bản khóa, state ngoài engine, adapter chỉ bao thao tác thực dùng. Backend đo đạc và render báo cáo chính thức.

## Phương án đã cân nhắc

Cesium/MapLibre/iTowns hoặc OpenLayers riêng chỉ xét theo fixture; chưa đóng gói hai engine để dự phòng.

## Hệ quả

Phải thử codec/overview/NoData, CRS/picking, WASM offline, token qua loader/web worker và giải phóng tài nguyên.

## Bằng chứng và người chốt

G1/G3: COG/DEM/COPC/vector trên viewport/style/máy cố định, p95 và AI đồng thời; 33ms là mục tiêu đề xuất chưa nghiệm thu. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Nếu fixture chứng minh không đáp ứng và đã xác định nguyên nhân/chi phí chuyển. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

