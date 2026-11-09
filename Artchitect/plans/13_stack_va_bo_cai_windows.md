# Stack và bộ cài Windows

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Dependency, core/compute/model/data pack, offline, build và update.

<a id="muc-14"></a>

## 14. Stack và bộ cài Windows

<a id="muc-14-1"></a>

### 14.1. Stack mặc định

| Nhóm | Lựa chọn |
| --- | --- |
| Desktop/frontend | Tauri 2, React, TypeScript, Vite, Giro3D, pnpm |
| API/schema | FastAPI, Pydantic, OpenAPI, SSE |
| GIS | GDAL/PROJ, Rasterio, Shapely, Pyogrio; PDAL cho pipeline điểm đã chọn |
| Catalog/cube | pystac-client; Xarray/odc-stac khi cần; Dask chỉ khi có lợi đo được |
| AI bản đầu | Prithvi-EO-2.0 + decoder phân đoạn đã kiểm định; RF/boosting đối chứng; ONNX Runtime ưu tiên và PyTorch inference pack theo điều kiện [mục 13](12_runtime_cpu_nvidia_va_hieu_nang.md#muc-13) |
| Toán–vật lý | NumPy/SciPy theo phương pháp đã chọn; PROSAIL/solver thủy lực và dependency chuyên ngành chỉ thêm cùng Domain Pack G4 sau kiểm định/giấy phép |
| Data/job local | SQLite WAL, repository SQLAlchemy, migration Alembic, filesystem, coordinator có phạm vi hẹp; điều kiện kiểm chứng tại [mục 5.2](04_kien_truc_thuc_thi_va_module.md#muc-5-2) |
| Report | Matplotlib, Typst; XlsxWriter khi có yêu cầu |
| Môi trường native/Python | Pixi và lockfile theo OS/architecture; cơ chế khóa dependency pip bên trong phải được xác định, không quản lý cùng package bằng hai nguồn cạnh tranh |
| Sidecar | Python/runtime được đóng gói; thử PyInstaller onedir hoặc environment đóng gói có thể di chuyển trước khi chốt |

Ưu tiên phiên bản tương thích với toàn bộ stack thay vì phiên bản mới nhất của từng thành phần. Công cụ quản lý dependency không tự bảo đảm thu đủ GDAL/PROJ data, codec, DLL, PDF renderer và tài nguyên tải động.

<a id="muc-14-2"></a>

### 14.2. Thành phần phân phối

- **Core:** UI, API/coordinator, GIS/CPU, SQLite, report engine và viewer assets.
- **Compute pack:** runtime NVIDIA đã kiểm chứng; runtime PyTorch CPU/CUDA bổ sung chỉ khi cần theo hồ sơ ngoại lệ, không kèm full training toolchain.
- **Model pack bắt buộc của bản đầu:** Prithvi-EO-2.0 và decoder/head nghiệp vụ có trọng số, ModelSpec, upstream revision/hash, định dạng và provenance chuyển đổi, preprocessing config, evaluation summary và license/notice. Phân phối ONNX hoặc safetensors theo [mục 14.3](13_stack_va_bo_cai_windows.md#muc-14-3); ngoại lệ `.pt` cần hồ sơ riêng. Runtime tương thích phải có trong cấu hình phân phối; backbone đơn lẻ hoặc decoder ngẫu nhiên chưa đủ.
- **Data pack:** dữ liệu mẫu/bản đồ nền được phép phân phối, phục vụ offline hoặc kiểm chứng.

NSIS EXE Standard là profile mặc định; Offline bổ sung đủ prerequisite và pack đã chọn. MSI/WiX dành cho triển khai tập trung. Định dạng EXE/MSI độc lập với Standard/Offline. Tauri có các cơ chế này [T4]; mỗi profile chỉ được công bố sau khi kiểm tra gói cuối.

Standard có thể tải model pack Prithvi trong bước thiết lập tính năng để giữ installer core nhỏ; trạng thái tải/chưa sẵn sàng phải rõ và có xác minh hash/chữ ký. Điều này không biến Prithvi thành phần mở rộng tùy chọn của lộ trình: bản phát hành đầu phải có đầy đủ pack, runtime và workflow thực thi. Profile Offline kèm sẵn model + decoder, runtime, metadata và dữ liệu kiểm chứng cần thiết; không tải trọng số ngầm khi mở model lần đầu.

Offline phải cài/chạy được khi ngắt mạng, không dựa vào CDN, cache máy build hoặc WebView2 bootstrapper cần Internet. Dùng offline installer/fixed runtime theo chính sách cập nhật đã chọn. Các chức năng tìm ảnh mới trên Internet vẫn cần mạng.

<a id="muc-14-3"></a>

### 14.3. Build và vòng đời

**Khóa dependency → build UI → đóng gói sidecar/pack → stage tài nguyên → build installer → ký → kiểm tra trên Windows sạch → phát hành.**

Ký Authenticode và chữ ký updater là hai cơ chế riêng. App, runtime và model pack có manifest tương thích và được xác minh trước kích hoạt. Chỉ pack từ nguồn được tin cậy mới được nạp; không chạy Python script tùy ý lấy từ một model tải ngoài. Process riêng không được xem là sandbox bảo mật đầy đủ.

**Chuỗi cung ứng trọng số:** các repository Prithvi đã đối chiếu có checkpoint `.pt` dùng cơ chế serialization của PyTorch [P6], [P7], [P8]. Khóa revision và tải trên môi trường build cô lập, không có credential sản xuất; kiểm hash từ nguồn/manifest tin cậy trước nạp. Dùng PyTorch đã vá với `weights_only=True` được đặt tường minh; không tự chuyển sang `weights_only=False` hoặc allowlist class lạ khi nạp lỗi. Chuyển checkpoint đã xác minh sang safetensors cho đường PyTorch hoặc ONNX cho ONNX Runtime, kiểm tra tương đương trước phân phối; code kiến trúc/preprocessing được khóa và review riêng.

Manifest phát hành ghi hash nguồn/đích, phiên bản công cụ chuyển đổi, cấu hình, kết quả kiểm chứng và chữ ký; kiểm manifest tin cậy và hash trước kích hoạt pack. Ngoại lệ giữ `.pt` phải ghi lý do và dùng `weights_only=True` trên runtime đã vá; không nhận pickle tùy ý từ người dùng. `weights_only=True` giảm bề mặt thực thi mã nhưng không chống mọi dạng DoS/lỗi bộ nhớ [T11]. Safetensors/ONNX không tự làm code/runtime an toàn, nên vẫn giới hạn kích thước/tài nguyên và chỉ nạp pack được tin cậy.

Trước update: xử lý job đang chạy, kiểm tra dung lượng, backup metadata, stage phiên bản mới và migration. Rollback app chỉ khi schema tương thích; còn lại dùng restore đã thử nghiệm. Gỡ ứng dụng mặc định giữ project/kết quả; không gỡ driver hoặc WebView2 dùng chung. Máy người dùng không cần Python/Node/Docker/toolchain phát triển.

---

**Tài liệu liên quan:**

- [Model Prithvi, dữ liệu nhãn và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md)
- [Runtime CPU/NVIDIA và hiệu năng](12_runtime_cpu_nvidia_va_hieu_nang.md)
- [Bảo mật, hướng lên server và vận hành](14_bao_mat_server_va_van_hanh.md)
- [Lộ trình và cổng nghiệm thu](15_lo_trinh_va_cong_nghiem_thu.md)

[T4]: https://v2.tauri.app/distribute/windows-installer/
[T11]: https://github.com/pytorch/pytorch/blob/main/docs/source/notes/serialization.md
[P6]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-tiny-TL/tree/335eadc2c45ad5abe7bd307223e1c48c5b60c41b
[P7]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-100M-TL/tree/2c84e383194986040f883cc43d7869002c425e1b
[P8]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M/tree/9eb1b1102806593963daa333bcc491b1c6f8562f
