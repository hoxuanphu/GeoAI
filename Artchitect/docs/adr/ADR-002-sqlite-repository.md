# ADR-002: SQLite WAL sau repository và migration

**Trạng thái:** Đề xuất thiết kế; chưa kiểm chứng migration/recovery. **Ngày:** 08/11/2026.
**Nguồn:** [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [đặc tả liên quan](../architecture.md).

## Bối cảnh

Desktop một writer/project cần metadata/job bền vững mà không cài database server.

## Lựa chọn

SQLite WAL trên ổ local, một coordinator ghi; SQLAlchemy repository, Alembic migration có khóa writer và backup. Worker không ghi DB.

## Phương án đã cân nhắc

PostgreSQL local thêm cài đặt/vận hành; truy vấn SQL rải trong domain làm khó migration; ORM object qua IPC phá contract.

## Hệ quả

Cần reconcile filesystem/DB và fixture constraint/index/upgrade/restore; không có transaction chung file/DB.

## Bằng chứng và người chốt

SPEC-004 phải kiểm publication/cancel/fencing và crash. Migration phải thử dữ liệu phiên bản cũ; PostgreSQL contract khi làm server G4. Chủ trì kỹ thuật/GIS/ML thực hiện phần tương ứng; chủ nghiệp vụ/chủ dự án chốt ngưỡng và thay đổi phạm vi. Hồ sơ này chưa có bằng chứng nghiệm thu runtime, model hoặc bộ cài.

## Điều kiện xem lại

Khi cần nhiều máy ghi đồng thời hoặc semantics SQLite không đáp ứng. Khi thay quyết định đã chấp thuận, tạo ADR mới và đánh dấu hồ sơ này bị thay thế, giữ nguyên nội dung/bằng chứng lịch sử. ADR đề xuất có thể được sửa cùng lịch sử review.

