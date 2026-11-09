# ADR-005: Backend quản lý CRS và TransformSpec

**Trạng thái:** Đề xuất thiết kế; cần điểm khống chế/tolerance G0–G1. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../domain-rules.md).

## Bối cảnh

Frontend proj4 và backend PROJ có thể dùng khác trục, operation/grid và tham số VN-2000 mà vẫn chạy.

## Lựa chọn

Registry backend có version và TransformSpec; frontend chỉ phép đã kiểm tương đương, còn lại backend reprojection. Phép đo dùng dữ liệu nguồn.

## Phương án đã cân nhắc

Hai bên tự nhập proj4; gán một VN-2000 chung; chỉ round-trip để kết luận đúng đều không đủ.

## Hệ quả

Cần grid offline/hash, area of use, tolerance, datum đứng và fixture cắt UTM 48N/49N; thiếu tài nguyên thì chặn phù hợp.

## Bằng chứng và người chốt

G0 có danh sách CRS/nguồn tham số; G1 đối chiếu điểm độc lập và raster overlay, không chỉ round-trip. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Khi có CRS/độ chính xác/miền sử dụng mới hoặc frontend hỗ trợ operation mới. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

