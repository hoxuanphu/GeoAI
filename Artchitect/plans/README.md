# Bộ tài liệu chuyên biệt về kiến trúc GeoAI

Bộ tài liệu được tách ngày **08/11/2026**, cập nhật đồng bộ theo [đề xuất kiến trúc tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md).

Gồm **17 tài liệu chuyên biệt**, bao phủ đầy đủ **20 mục** của bản tổng hợp v1.4. Giữ cùng nội dung thiết kế, bảng, sơ đồ và số mục; bổ sung điều hướng và chuyển các dẫn chiếu giữa mục thành liên kết. Bản tổng hợp là nguồn nội dung chuẩn: cập nhật thiết kế ở đó trước, rồi đồng bộ toàn bộ tài liệu đã tách trong cùng phiên bản; không sửa riêng hai bản thành hai thiết kế khác nhau.

## Trạng thái và cơ sở của bản gốc

Ngày lập/cập nhật và tra cứu nguồn: **08/11/2026**. Phiên bản tài liệu: **1.4**.

Trạng thái: **đề xuất thiết kế để xem xét; chưa triển khai, build bộ cài hoặc benchmark GeoAI**. Những mục được gọi là “quyết định” là lựa chọn của bản đề xuất này, không phải tính năng đã có. Các ngưỡng chất lượng, phần cứng và lịch phát hành cần được xác nhận bằng dữ liệu nghiệp vụ và thử nghiệm.

Cơ sở nội bộ: [bản chính v1.2][A], [bản Copilot][B], [Cẩm nang kiến trúc][C1] và [Hướng dẫn xây dựng ứng dụng][C2]. Phạm vi kế thừa từ bản chính: **ưu tiên Windows desktop, xử lý cục bộ, Giro3D, AI CPU/NVIDIA; giữ khả năng đưa cùng lõi nghiệp vụ lên Linux/server**.

Yêu cầu sản phẩm đã được người dùng xác nhận: **Prithvi-EO-2.0 phải được tích hợp và sử dụng cho phân tích ngay trong bản phát hành đầu**. Biến thể, decoder và profile dữ liệu bên dưới là lựa chọn thiết kế khởi đầu cần kiểm chứng; việc tích hợp Prithvi không còn là hạng mục nghiên cứu tùy chọn.

## Mục lục và đối chiếu

| Tài liệu | Mục gốc | Nội dung |
| --- | --- | --- |
| [01_dinh_huong_san_pham.md](01_dinh_huong_san_pham.md) | 1 | Mục tiêu, nguyên tắc, nhóm người dùng và các cấu hình local/server. |
| [02_co_so_de_xuat_va_tham_chieu_thi_truong.md](02_co_so_de_xuat_va_tham_chieu_thi_truong.md) | 2, 3 | Chắt lọc tài liệu nội bộ, đối chiếu sản phẩm và yêu cầu R01–R09. |
| [03_pham_vi_ban_dau_va_luong_su_dung.md](03_pham_vi_ban_dau_va_luong_su_dung.md) | 4 | Chọn nghiệp vụ G0, phạm vi phát hành đầu, phần hoãn và luồng giao diện. |
| [04_kien_truc_thuc_thi_va_module.md](04_kien_truc_thuc_thi_va_module.md) | 5 | Sơ đồ kiến trúc, API/coordinator/worker và trách nhiệm các module. |
| [05_hop_dong_du_lieu_va_versioning.md](05_hop_dong_du_lieu_va_versioning.md) | 6 | Schema, snapshot, model/run/revision/report và danh tính nội dung. |
| [06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md) | 7 | Provider/product profile, định dạng, QA, grid, CRS và VN-2000. |
| [07_model_prithvi_nhan_va_kiem_dinh.md](07_model_prithvi_nhan_va_kiem_dinh.md) | 8 | Prithvi, profile HLS, mô hình toán–vật lý, nhãn/hiệu chuẩn, độ bất định và quality gate. |
| [08_job_tai_nguyen_va_phuc_hoi.md](08_job_tai_nguyen_va_phuc_hoi.md) | 9 | Vòng đời job, attempt, hủy/retry, scheduler và giao thức worker. |
| [09_luu_tru_artifact_va_project.md](09_luu_tru_artifact_va_project.md) | 10 | SQLite/filesystem, publish, backup/export, pin/retention và tái lập offline. |
| [10_viewer_gis_3d_va_kiem_tra_ket_qua.md](10_viewer_gis_3d_va_kiem_tra_ket_qua.md) | 11 | Giro3D, asset streaming, state, review và fixture hiển thị. |
| [11_revision_domain_pack_va_bao_cao.md](11_revision_domain_pack_va_bao_cao.md) | 12 | Duyệt kết quả, phiên bản chỉnh sửa, gói nghiệp vụ và xuất PDF. |
| [12_runtime_cpu_nvidia_va_hieu_nang.md](12_runtime_cpu_nvidia_va_hieu_nang.md) | 13 | ONNX/PyTorch, chọn thiết bị, compute pack và ngân sách CPU. |
| [13_stack_va_bo_cai_windows.md](13_stack_va_bo_cai_windows.md) | 14 | Dependency, core/compute/model/data pack, offline, build và update. |
| [14_bao_mat_server_va_van_hanh.md](14_bao_mat_server_va_van_hanh.md) | 15 | Bảo mật local/server, adapter triển khai, quyền, log và chẩn đoán. |
| [15_lo_trinh_va_cong_nghiem_thu.md](15_lo_trinh_va_cong_nghiem_thu.md) | 16 | G0–G4, ma trận kiểm chứng bắt buộc và hồ sơ benchmark. |
| [16_quyet_dinh_can_chot_va_danh_doi.md](16_quyet_dinh_can_chot_va_danh_doi.md) | 17, 18 | Mặc định đề xuất, người/thời điểm chốt, tác động và các đánh đổi. |
| [17_nguon_tham_khao_va_lich_su.md](17_nguon_tham_khao_va_lich_su.md) | 19, 20 | Danh mục A/B/C/M/T/P/F, phạm vi bằng chứng và lịch sử phiên bản gốc. |

## Cách đọc

- **Sản phẩm và phạm vi:** đọc [định hướng](01_dinh_huong_san_pham.md), [phạm vi bản đầu](03_pham_vi_ban_dau_va_luong_su_dung.md), [quyết định cần chốt](16_quyet_dinh_can_chot_va_danh_doi.md) và [cổng nghiệm thu](15_lo_trinh_va_cong_nghiem_thu.md).
- **Kiến trúc và triển khai:** bắt đầu từ [kiến trúc module](04_kien_truc_thuc_thi_va_module.md) và [hợp đồng dữ liệu](05_hop_dong_du_lieu_va_versioning.md), sau đó theo liên kết tới thành phần cần triển khai.
- **GIS và AI:** đọc [chuẩn hóa địa lý](06_du_lieu_da_nguon_va_chuan_hoa_dia_ly.md), [Prithvi và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md), [runtime](12_runtime_cpu_nvidia_va_hieu_nang.md) và [review/báo cáo](11_revision_domain_pack_va_bao_cao.md).
- **Căn cứ và truy nguyên:** xem [tham chiếu thị trường](02_co_so_de_xuat_va_tham_chieu_thi_truong.md) và [danh mục nguồn/lịch sử](17_nguon_tham_khao_va_lich_su.md).

## Quy ước sử dụng

- Số thứ tự trong tên tệp là thứ tự đọc; số mục trong nội dung là số của bản gốc. Ví dụ mục 8.2 nằm trong tài liệu `07_model_prithvi_nhan_va_kiem_dinh.md`.
- Các mã nguồn `[A]`, `[B]`, `[C1]`, `[C2]`, `[M…]`, `[T…]`, `[P…]`, `[F…]` giữ nguyên; mỗi tệp có định nghĩa liên kết cho các nguồn được trích dẫn trong tệp đó.
- Nguồn cũ kế thừa bản tổng hợp; bản 1.2 bổ sung đối chiếu nguồn chính thức về biến thể Prithvi, quantization, serialization và Windows handles. Đồng bộ tài liệu không phải chạy thử hệ thống; chưa có benchmark, khảo sát coverage HLS hoặc kết quả nghiệm thu GeoAI.
- Yêu cầu Prithvi-EO-2.0 từ bản đầu được giữ nguyên. Các mặc định, quality gate, ngân sách và quyết định còn mở vẫn có trạng thái như bản gốc.

## Cập nhật trong phiên bản 1.2

- G0: khảo sát HLS theo ngày/tháng trong 2–3 năm, chốt đường truy cập/credential, bắt đầu nhãn và đặt ngân sách/quy tắc dừng.
- Model: thêm ứng viên 100M-TL/tiny-TL/non-TL, giữ provenance ngày/scene/composite; profile T=1, cửa sổ 224 cố định và dynamic INT8 có điều kiện.
- G1/G2: tách fixture kỹ thuật với decoder ngẫu nhiên khỏi golden output và nghiệm thu checkpoint nghiệp vụ; ngưỡng tuyệt đối quyết định nghiệm thu, RF là đối chứng.
- Phân phối và kiểm chứng: chuyển đổi trọng số an toàn, manifest tin cậy, stdout Windows và fixture HLS cắt ranh UTM 48N/49N.
- Quyết định có đánh đổi đáng kể khi được chốt cần ADR liên kết từ mục 17 và bản tổng hợp; không ghi các lựa chọn còn mở thành quyết định đã phê duyệt.

## Cập nhật trong phiên bản 1.3

Tiếp thu có chọn lọc bản hợp nhất chuyên gia, giữ phạm vi Prithvi/HLS và các điều kiện G0–G4, chất lượng, pin/lease và revision của v1.2.

- Kiến trúc: thêm hướng phụ thuộc module, kiểm tra import và repository SQLAlchemy/migration Alembic; CI SQLite trước, PostgreSQL khi thực hiện adapter server.
- Dữ liệu/viewer: hai profile sử dụng COG, dùng chung asset khi tương thích; kiểm chứng codec/overviews/WASM offline, token cho loader/web worker và p95 frame time theo scene cố định.
- Desktop: kiểm tra Host/Origin và token phiên; Windows Job Object thu hồi nhóm tiến trình, dừng/checkpoint vẫn có quy trình riêng.
- Nghiệm thu: cấu hình CPU/RAM/GPU và AOI là ứng viên để chốt tại G0, chưa phải support matrix hoặc benchmark.
- Quyết định: thêm [sổ ADR](16_quyet_dinh_can_chot_va_danh_doi.md#muc-17-1), phân biệt yêu cầu đã xác nhận với lựa chọn kỹ thuật còn cần kiểm chứng. Nguồn chuyên gia và phạm vi tiếp thu được ghi tại tài liệu nguồn/lịch sử.

## Cập nhật trong phiên bản 1.4

- Thêm [danh mục mô hình toán–vật lý](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-6): PROSAIL, FAO-56 Penman–Monteith, SEBAL, SCS-CN, HAND, nước nông 2D, RUSLE và allometry sinh khối/carbon.
- [Phương trình và đơn vị](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-7) nêu dữ liệu bắt buộc, giới hạn áp dụng và phép kiểm chứng; GEO-01 bổ sung chỉ số phổ/diện tích/coverage cho bản đầu.
- Thêm PhysicalModelSpec, snapshot tham số/forcing/điều kiện biên, hiệu chuẩn và độ bất định; đồng bộ job, pin/retention, Domain Pack, báo cáo và cổng nghiệm thu.
- Các feature PHY được chọn từng bước ở G4 theo dữ liệu kiểm định; nguồn tài liệu có ghi phạm vi đã đọc và phần chưa đọc toàn văn. Chưa triển khai solver, hiệu chuẩn hay kiểm định thực địa.

## Tài liệu để triển khai

[Bộ docs AI/dev](../docs/README.md) cụ thể hóa v1.4 thành contracts, domain/Prithvi/IPC/physical profile, [roadmap](../docs/roadmap.md) và [task specs](../docs/specs/README.md). Hồ sơ [ADR-001–010](../docs/adr/README.md) được đặt tại `Artchitect/docs/adr/` theo yêu cầu người dùng; [sổ quyết định](16_quyet_dinh_can_chot_va_danh_doi.md#muc-17-1) và bản tổng hợp đã đồng bộ vị trí này. Đây là bổ sung tổ chức tài liệu, không thay yêu cầu nghiệp vụ hoặc trạng thái nghiệm thu v1.4. Phạm vi hiện tại chỉ viết tài liệu; mã contracts có một phần bản nháp và chưa hoàn tất.

Bổ sung sau review ngày 08/11/2026 trong baseline v1.4: [SPEC-008](../docs/specs/008-training-evaluation-model-pack.md) tạo dataset/training/evaluation/model pack, [SPEC-009](../docs/specs/009-importer-worker-resolver.md) và [worker resolver](../docs/worker-resolver.md) cụ thể hóa cấp quyền/acceptance; [ADR-011](../docs/adr/ADR-011-local-execution-owner.md) đề xuất execution owner liên instance/project. Đồng bộ các mục liên quan ở plans 05/07/08/14/15/16 và kiến trúc; mới là đặc tả, chưa có code hoặc kết quả gate.

[A]: <../solution/de_xuat_kien_truc_he_thong_geoai.md>
[B]: <../solution/de_xuat_kien_truc_he_thong_geoai_copilot.md>
[C1]: <../solution/cam_nang_kien_truc_ung_dung_geoai_vien_tham.md>
[C2]: <../solution/Hướng dẫn xây dựng ứng dụng GeoAI cho viễn thám.md>
