# ADR-007: PDF Typst từ revision và metrics snapshot

**Trạng thái:** Đề xuất; cần fixture tiếng Việt/offline. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../contracts.md).

## Bối cảnh

Kết quả sau review có thể khác raster dự đoán; báo cáo phải cố định revision/representation và nguồn số liệu.

## Lựa chọn

ResultRevision → MetricsSnapshot → ReportContext → bản đồ backend/Typst PDF. Official yêu cầu reviewed; lưu PDF gốc/hash, font/template version.

## Phương án đã cân nhắc

Chụp viewer làm số đo; truy catalog lại lúc report; sửa PDF cũ theo run mới đều phá truy nguyên. HTML/PDF renderer thứ hai chưa cần.

## Hệ quả

Sửa sau duyệt tạo revision chưa duyệt; vector sửa không tự sửa raster; report snapshot có acquisition/run/report times và coverage.

## Bằng chứng và người chốt

G1 PDF tiếng Việt offline; G2 số liệu khớp revision/representation; G3 xuất lại nội dung từ snapshot/restore. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Nếu tổ chức yêu cầu DOCX hoặc renderer khác có bằng chứng nhu cầu. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

