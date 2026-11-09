# Hợp đồng dữ liệu và versioning

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Schema, snapshot, model/run/revision/report và danh tính nội dung.

<a id="muc-6"></a>

## 6. Các hợp đồng dữ liệu cần chốt trước khi viết chức năng

Mọi hợp đồng lưu lâu dài có `schema_version`, ID ổn định và thời gian UTC; UI hiển thị theo múi giờ người dùng. ID nhà cung cấp luôn có namespace để không nhầm hai scene cùng tên. Không đưa credential, signed URL hay SDK object vào snapshot.

| Hợp đồng | Nội dung tối thiểu | Quy tắc chính |
| --- | --- | --- |
| `AssetRef` | Provider, collection, product profile/version, scene/asset ID, acquisition time/range, processing level, CRS, footprint, bands/units, QA, license reference, content identity | `asset_id` resolve ra địa chỉ tại thời điểm đọc; vị trí file không thay thế danh tính nội dung |
| `GridSpec` | CRS, affine transform, width/height, pixel interpretation, resampling rule, output dtype/NoData, vertical datum khi có | Extent/pixel size suy ra từ grid; trường lặp phải được kiểm tra nhất quán |
| `TransformSpec` | CRS nguồn/đích có version, trục/đơn vị, operation/pipeline, grid chuyển datum/hash, area of use, tolerance, PROJ database version | Backend quản lý; frontend chỉ dùng phép đã kiểm chứng tương đương, theo [mục 7.4](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md#muc-7-4) |
| `InputSnapshot` | AOI chuẩn, danh sách asset/version, band mapping, QA policy, temporal selection, mosaic recipe, retention profile và dependency inventory | Chạy lại không tìm lại catalog; phân biệt cố định danh tính với giữ dữ liệu offline |
| `ModelSpec` | ID/version/hash của backbone và decoder, upstream revision, task, sensor/product, band order, units/normalization, shape/GSD/time constraints, metadata policy, classes, runtime/precision, weight format/conversion provenance, license, evaluation IDs | Chặn input sai; pre/postprocess trỏ tới thành phần đã đăng ký và có version; phân biệt backbone, model kỹ thuật với decoder ngẫu nhiên và model nghiệp vụ đã kiểm định; hash đối chiếu manifest tin cậy |
| `PhysicalModelSpec` | Model/method ID và version, loại vật lý/bán thực nghiệm, nguồn phương trình, implementation/solver version/hash, biến/đơn vị, tham số và nguồn/miền hiệu lực, grid/time step/datum, điều kiện đầu/biên khi có, calibration/evaluation IDs, uncertainty policy | Tham chiếu phương pháp đã đăng ký; không chạy biểu thức/script tùy ý. Thiếu biến bắt buộc hoặc sai đơn vị thì chặn; không giả tạo backbone/decoder cho mô hình vật lý |
| `DatasetVersion` | Nguồn nhãn, geometry/CRS, ngày ảnh, class schema, người duyệt, split, license, hash | Tách train/validation/test trước chipping; lưu kiểm tra giao/chồng lấn |
| `JobSpec` | Project, workflow/version, snapshot, tham số, compute policy, resource budget, idempotency key | Dữ liệu gửi qua IPC là manifest/URI; không đẩy tensor lớn qua JSON |
| `RunManifest` | Input/model/pipeline/config hash, grid, attempt, backend/driver/precision thực dùng, coverage, output IDs/checksums, quality flags; với mô hình vật lý thêm PhysicalModelSpec, parameter/calibration snapshot, forcing/biên/solver hash, sai số cân bằng và uncertainty refs | Bất biến sau công bố; ghi cả quyết định fallback nếu có; thiếu đầu vào vật lý không tự điền bằng đầu ra AI chưa được kiểm định |
| `ResultRevision` | Base run, parent revision, edit artifact, class schema, tác giả, lý do, review state | Bản đầu dùng `unreviewed/reviewed`; revision mới khi sửa nhãn/hình học/ngưỡng và phải duyệt lại |
| `EvaluationRecord` | Dataset/split, model/run, loại kiểm chứng kỹ thuật/nghiệp vụ, matching/threshold policy, metrics theo lớp, vùng/thời gian, baseline đối chứng, quality gate/version và kết luận, hạn chế | Không gắn metrics của một khu vực như cam kết cho mọi khu vực; fixture decoder ngẫu nhiên không có giá trị nghiệm thu chất lượng nghiệp vụ |
| `ReportContext` | Result revision, AOI, metrics snapshot, coverage, evaluation refs, template/style/font version, thời gian lập | Chỉ render từ snapshot; đổi kết quả tạo báo cáo mới |

`PhysicalModelSpec` dùng chung `DatasetVersion`, `EvaluationRecord` và cơ chế artifact/job với model học máy. Domain Pack chỉ tham chiếu spec phù hợp từng bước; workflow lai lưu cả hai loại spec. `InputSnapshot` của job vật lý bao gồm forcing khí tượng/thủy văn, DEM/đất, bảng hệ số, điều kiện biên và thời gian tương ứng. Tham số sau hiệu chuẩn là snapshot bất biến có hash và liên kết dataset/split; cấu trúc chi tiết của từng profile được chốt khi thực hiện feature theo [mục 8.8](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-8).

Access context cấp cho worker là trạng thái runtime tạm, tách khỏi snapshot bền vững: coordinator khóa project/worker/attempt/ref hashes và quyền đọc/ghi theo [worker resolver](../docs/worker-resolver.md). `start` draft yêu cầu context ID/hash; SPEC-001/009 phải thêm kiểu Pydantic, fixture/test và artifact sinh cùng lúc khi triển khai. Không persist credential/provider URL trong context hoặc snapshot; location local private không là field API cho UI tự nhập.

**Versioning:** thay đổi không tương thích tăng major schema version; importer từ chối phiên bản không hiểu bằng lỗi rõ ràng. Trường mở rộng chỉ được bỏ qua nếu schema cho phép. Migration có backup, fixture dữ liệu cũ và kiểm tra restore. Phiên bản app, schema, feature, model và template là các giá trị khác nhau.

**Danh tính nội dung:** asset do hệ thống tạo có checksum. Nguồn remote ưu tiên checksum/version ID của provider; ETag chỉ là dấu hiệu thay đổi nếu provider không cam kết là content hash. File tham chiếu ngoài dự án được kiểm tra lại trước chạy; nếu nội dung đổi phải tạo asset version mới. Báo cáo vẫn xuất lại được từ snapshot/artifact đã lưu, còn chạy lại toàn bộ cần nguồn và runtime tương thích còn truy cập được.

---

**Tài liệu liên quan:**

- [Dữ liệu đa nguồn và chuẩn hóa địa lý](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md)
- [Model Prithvi, dữ liệu nhãn và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md)
- [Job, tài nguyên và phục hồi](08_job_tai_nguyen_va_phuc_hoi.md)
- [Lưu trữ, artifact và project di động](09_luu_tru_artifact_va_project.md)
- [Revision, Domain Pack và báo cáo](11_revision_domain_pack_va_bao_cao.md)
