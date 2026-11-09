# SPEC-007 — Kiểm chứng nền tảng GIS, viewer, PDF và bundle G1

**Trạng thái:** chỉ có đặc tả, chưa triển khai/chạy kiểm tra.
**Mục tiêu:** bổ sung bằng chứng G1 ngoài spike Prithvi: đúng địa lý, hiển thị/xác thực/offline, báo cáo kỹ thuật và native bundle. Không coi SPEC-005 hoặc test contracts là toàn bộ G1.

## Dependency và phạm vi

Đọc [architecture](../architecture.md), [domain rules](../domain-rules.md), [testing strategy](../testing-strategy.md), ADR-003/005/006/007. Cần SPEC-001/003/004 và fixture được phép dùng; khi kiểm cùng AI cần runtime kỹ thuật SPEC-005. CRS/VN-2000 và tolerance, máy/workload/viewer budget phải có quyết định G0 tương ứng; trước đó chỉ chạy ca cơ chế tổng hợp, chưa kết luận hỗ trợ sản phẩm.

Output dự kiến: adapter viewer và asset/Range/tile serving, fixture GIS có nguồn/license/hash, template Typst/font tiếng Việt, prototype sidecar/bundle có inventory native; báo cáo tại `Artchitect/docs/evidence/g1/`. Các package đích ở [hướng dẫn dev](../development-guide.md); không tạo bản sao pipeline trong UI hoặc renderer thứ hai.

Phần import/asset/native phải tích hợp [SPEC-009](009-importer-worker-resolver.md) với policy/ca kiểm ở [ma trận security](../importer-resolver-security.md), không chỉ kiểm token HTTP. Tổng hợp G1 cần cả execution-owner/recovery ở SPEC-003/004 và resolver/candidate isolation; chưa có các bằng chứng này thì không kết luận toàn G1 đạt.

## Acceptance và ca kiểm cụ thể

Tolerance người dùng cung cấp RMSE ngang VN-2000 ≤15 m và chênh lệch diện tích AOI ≤0,1% được diễn giải tại [tiêu chí nghiệm thu](../acceptance-criteria.md). Cần khóa CRS/operation/grid/điểm kiểm độc lập và cùng phương pháp diện tích trước nghiệm thu; không dùng round-trip, schema pass hoặc một bộ 7 tham số chưa kiểm để xác nhận đạt.

| Nhánh | Phải kiểm | Khi không đạt |
| --- | --- | --- |
| CRS/grid | Điểm độc lập ở CRS được chọn, VN-2000 đúng operation/grid/datum; ranh 48N/49N; overlay và area/coverage không đếm trùng | Chặn CRS chưa đủ tài nguyên/độ chính xác; không fallback ballpark |
| Asset/viewer | COG liên tục/nhãn/DEM, GeoPackage/GeoJSON và COPC theo fixture; codec/predictor/overview/NoData, Range, token header qua loader/web worker, WASM/font offline | Dùng asset/tile dẫn xuất backend khi fixture chứng minh cần; lưu recipe/source, không sửa grid phân tích |
| State/hiệu năng | Camera/layer/AOI/selection/timeline giữ qua panel; unload giải phóng tài nguyên; p95/frame và memory trên viewport/style/máy cố định, có/không AI | Ghi số đo và phạm vi hỗ trợ; mục tiêu 33 ms trong đề xuất chưa là ngưỡng được duyệt |
| Draft report | ReportContext kỹ thuật chỉ rõ synthetic/unreviewed; PDF tiếng Việt offline, đơn vị/coverage/ngày ảnh/ngày chạy/ngày lập đúng snapshot | Không dùng decoder ngẫu nhiên để phát hành official hoặc tuyên bố chất lượng |
| Native/bundle | GDAL/PROJ database/grid/codec/ORT, Typst/font, WASM/WebView2 có nguồn/version/hash; path tiếng Việt, thiếu DLL/grid có lỗi rõ; PATH/cache không che dependency | Sửa inventory/phương án bundle bằng ADR-006; không công bố installer G3 chỉ từ prototype |

## Bộ kiểm tra cần tạo trong task triển khai

- `tests/geoprocessing/test_crs_reference.py`: điểm chuẩn độc lập/tolerance, thiếu grid, sai trục, mosaic cắt UTM, diện tích AOI và categorical resampling.
- `tests/integration/test_asset_serving.py`: hợp lệ/không hợp lệ về session, chưa publish hoặc sai project bị từ chối, Range/partial content, asset/tile fallback và không lộ path/secret.
- Frontend viewer tests: state qua panel, loader/worker nhận header, fixture codec/NoData, unload/reload; chạy trong WebView2 thực cho các hành vi phụ thuộc môi trường.
- `tests/reports/test_draft_report.py`: render offline từ snapshot, tiếng Việt/font/units và không cho technical/unreviewed thành official.
- `tests/integration/test_native_bundle.py`: process thật từ prototype bundle trên môi trường Windows ghi rõ PATH/cache, tài nguyên native/log stdout và máy không có môi trường dev.

Lệnh frontend/native cụ thể là deliverable khi dựng package; báo cáo phải lưu lệnh thực, môi trường, exit code, lỗi/skip, hash fixture và artifact. Review hình ảnh/PDF và số đo hiệu năng cần artifact/số liệu, không chỉ pass unit test. Cùng SPEC-003/004/005, task này cung cấp đầu vào tổng hợp G1; nghiệm thu business G2 và ma trận máy sạch/installer G3 vẫn riêng.
