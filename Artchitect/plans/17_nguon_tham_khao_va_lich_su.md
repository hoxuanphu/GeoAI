# Nguồn tham khảo và lịch sử tài liệu

**Addendum Ubuntu 10/11/2026:** [nguồn đã đối chiếu](../docs/platforms/ubuntu/ubuntu-development-and-packaging.md#nguồn-đã-đối-chiếu) bổ sung Tauri/Debian/prerequisites, package Ubuntu Jammy/Noble, systemd v249, XDG và Linux man-pages cho [ADR-012](../docs/adr/ADR-012-ubuntu-desktop.md). [Lịch sử nguồn tổng hợp](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md#20-lịch-sử-tài-liệu) ghi bổ sung trên baseline 1.4. Chỉ kiểm tài liệu; chưa chạy Linux, desktop/GPU/model hoặc bộ cài.

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** Danh mục A/B/C/M/T/P/F, phạm vi bằng chứng và lịch sử phiên bản gốc.

<a id="muc-19"></a>

## 19. Danh mục nguồn và phạm vi sử dụng

<a id="muc-19-1"></a>

### 19.1. Tài liệu nội bộ

| Mã | Tài liệu | Phần được sử dụng |
| --- | --- | --- |
| [A] | Đề xuất kiến trúc hệ thống GeoAI v1.2 | Quyết định desktop/Giro3D/CPU-NVIDIA, module, dữ liệu, report, packaging và hướng server |
| [B] | Đề xuất kiến trúc GeoAI — Copilot | Cấu hình triển khai, product profile, queue server, quyền truy cập và vận hành |
| [C1] | Cẩm nang kiến trúc và phát triển ứng dụng GeoAI | Năng lực, phương pháp, pipeline ảnh lớn, baseline, kiểm định không gian |
| [C2] | Hướng dẫn xây dựng ứng dụng GeoAI cho viễn thám | Đặc tả bài toán, dataset/nhãn, đánh giá, workflow, feedback và drift |

Bản 1.3 tiếp thu có chọn lọc tài liệu người dùng cung cấp **“Đề xuất kiến trúc hợp nhất hệ thống GeoAI (desktop-first)”**, tự ghi phiên bản 2.1, ngày 08/11/2026, tên file `Đề xuất kiến trúc hợp nhất hệ thống GeoAI (desktop-first) (1).md`: hướng phụ thuộc module, repository/migration, COG theo mục đích, bảo mật desktop, quản lý tiến trình Windows, cấu hình thảo luận và ADR. Đây là nguồn góp ý thiết kế, không phải bằng chứng triển khai. Không kế thừa các đoạn mâu thuẫn về Prithvi tùy chọn, bắt buộc thắng RF, lộ trình A–D, sửa snapshot khi bỏ pin hoặc báo cáo bỏ qua revision; bản tổng hợp và bộ plans tiếp tục dùng G0–G4 và các điều kiện của v1.2.

<a id="muc-19-2"></a>

### 19.2. Nguồn sản phẩm đã đọc trực tiếp ngày 08/11/2026

| Mã | Tài liệu chính thức | Nội dung làm bằng chứng |
| --- | --- | --- |
| [M1] | ArcGIS Pro — Deep learning in ArcGIS Pro | Preparing training data, model training, inference và review |
| [M2] | ArcGIS Pro — Deep learning models in ArcGIS | EMD/DLPK, sensor/band/model definitions và package contents |
| [M3] | ArcGIS Pro — Compute Accuracy For Object Detection | Metrics theo lớp, ground truth, IoU matching và PDF accuracy report |
| [M4] | ArcGIS Pro — Review results from deep learning | Rà soát đối tượng và sửa thuộc tính lớp |
| [M5] | ENVI — Introduction to ENVI Deep Learning | Module cài đặt/license riêng, mục đích phân tích đặc trưng không gian/phổ |
| [M6] | ENVI — Overview of the ENVI Deep Learning Process | Grid, object detection, pixel segmentation và chia sẻ model |
| [M7] | ENVI — Configure ONNX Model | Input/output, pre/postprocess, bands, shape, version, license và wavelength |
| [M8] | ENVI — View Training Metrics | Training/validation metrics, confusion matrices và metadata đánh giá |
| [M9] | Picterra — Annotations | Training areas, accuracy areas và annotation |
| [M10] | Picterra — Detector Insights | Cảnh báo dữ liệu nhãn và training/accuracy area overlap |
| [M11] | Picterra — Results | Detection area, thuộc tính, lớp và export; lưu ý simplification của detection area |
| [M12] | Picterra — Reports | Result/monitoring reports, timeline, count/area statistics và CSV |
| [M13] | UP42 — Create catalog orders | Access/EULA, search/preview, order/budget và delivery status |
| [M14] | UP42 — Access to data | STAC-retrievable storage, asset, metadata và download |
| [M15] | Earth Engine — Processing Environments | Interactive/batch, task lifecycle, retry và cancellation |
| [M16] | Earth Engine — Earth Engine quotas | Giới hạn request, batch, memory và storage |
| [M17] | Trimble — eCognition Remote Sensing Office Software | OBIA/AI/rulesets; thông báo không còn bán tích cực |

Đây là tài liệu sử dụng hoặc trang sản phẩm công khai, không phải thử nghiệm có tài khoản trả phí. ArcGIS `pro.arcgis.com` chuyển hướng sang `doc.esri.com` trong lần tra cứu; liên kết dưới dùng đích đã đọc. Picterra dùng miền `picterra.ai`/`docs.picterra.ai`. Những URL trả trang rỗng hoặc lỗi không được dùng làm bằng chứng.

<a id="muc-19-3"></a>

### 19.3. Chuẩn và nền tảng kỹ thuật đã đối chiếu

| Mã | Nguồn | Phạm vi xác nhận |
| --- | --- | --- |
| [T1] | STAC — SpatioTemporal Asset Catalogs | Mô tả, lập chỉ mục và khám phá asset địa lý |
| [T2] | OGC Cloud Optimized GeoTIFF Standard 1.0, 21-026 | COG, tile/overview và HTTP range; đây là đặc tả chuẩn |
| [T3] | Giro3D — API documentation | Khái niệm và API công khai; không phải benchmark GeoAI |
| [T4] | Tauri 2 — Windows Installer | NSIS/WiX, điều kiện build và phân phối WebView2 |
| [T5] | SQLite — Write-Ahead Logging | WAL, concurrency/checkpoint và giới hạn cùng host/network filesystem |
| [T6] | Giro3D — Examples | Ví dụ COPC và GeoTIFF elevation/color trong danh mục ví dụ chính thức |
| [T7] | PROJ — Computation of coordinate operations between two CRS | Lựa chọn operation theo vùng, độ chính xác và grid; CRS giống nhau chưa đủ bảo đảm cùng phép chuyển |
| [T8] | ONNX Runtime — Quantize ONNX models | Dynamic cho transformer, static cho CNN, calibration, overhead và trường hợp quantization không tăng tốc; không phải benchmark Prithvi |
| [T9] | JSON-RPC 2.0 Specification | Request/response/notification; transport/framing là quyết định bổ sung của GeoAI |
| [T10] | ONNX Runtime — CUDA Execution Provider | Dependency CUDA/cuDNN và tương thích runtime; không suy dung lượng pack chỉ từ tên framework |
| [T11] | PyTorch — Serialization semantics, tài liệu nguồn chính thức | `weights_only=True` hạn chế unpickling nhưng không chống mọi DoS/lỗi bộ nhớ; không coi là sandbox |
| [T12] | Microsoft — GetStdHandle và SetStdHandle | Win32 standard handle, thay hướng output và giới hạn khi code đã cache handle; cần kiểm chứng với sidecar/native DLL thực |
| [T13] | SQLAlchemy — Overview | Core/ORM và lớp tích hợp database; không chứng minh SQLite/PostgreSQL có semantics giống nhau |
| [T14] | Alembic — Running Batch Migrations for SQLite and Other Databases | Migration batch/table rebuild và constraint của SQLite; script sinh tự động vẫn phải review và kiểm tra restore |
| [T15] | Microsoft — Job Objects | Nhóm tiến trình, kế thừa/breakaway và kill-on-close; không bảo đảm flush/checkpoint nghiệp vụ |

Phiên bản dependency phải được khóa ở G1. Các trang `latest` có thể thay đổi; release manifest và hồ sơ benchmark cần ghi phiên bản thực tế, không chỉ lưu link `latest`.

<a id="muc-19-4"></a>

### 19.4. Nguồn Prithvi và profile HLS đã đối chiếu

| Mã | Nguồn chính thức | Phạm vi xác nhận |
| --- | --- | --- |
| [P1] | IBM/NASA — Prithvi-EO-2.0-300M-TL model card, revision đã ghi ở [mục 8.2](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-2) | Backbone MAE/ViT, metadata TL, HLS v2 30 m, sáu band, Apache-2.0; demo là image reconstruction và task khác cần fine-tune |
| [P2] | Cùng model repository — config.json tại cùng revision | Sáu input channel, img_size 224, patch 1×16×16, num_frames 4, time/location và thống kê normalization |
| [P3] | NASA-IMPACT/Prithvi-EO-2.0 — cấu hình fine-tuning sen1floods11.yaml | EncoderDecoderFactory/UperNetDecoder và sáu band quang học; là cấu hình mẫu, không phải checkpoint downstream đã kiểm chứng cho GeoAI |
| [P4] | Earth Engine Data Catalog — NASA HLS HLSS30 v002 | Mô tả sản phẩm NASA và band mapping của HLS Sentinel-2; không bắt buộc dùng Earth Engine làm nguồn thực thi |
| [P5] | Earth Engine Data Catalog — NASA HLS HLSL30 v002 | Mô tả sản phẩm NASA và band mapping của HLS Landsat |
| [P6] | IBM/NASA — Prithvi-EO-2.0-tiny-TL, revision `335eadc2c45ad5abe7bd307223e1c48c5b60c41b` | Model card công bố 5M và họ model tiền huấn luyện HLS; danh sách file có `.pt`; chưa đo chất lượng/tốc độ GeoAI |
| [P7] | IBM/NASA — Prithvi-EO-2.0-100M-TL, revision `2c84e383194986040f883cc43d7869002c425e1b` | Repository chính thức của ứng viên 100M-TL, có checkpoint `.pt`; config/decoder/runtime phải kiểm chứng trước chọn |
| [P8] | IBM/NASA — Prithvi-EO-2.0-300M, revision `9eb1b1102806593963daa333bcc491b1c6f8562f` | Model card/config xác nhận bản không TL, `coords_encoding` rỗng; không chứng minh non-TL tốt hơn TL trên GeoAI |
| [P9] | NASA Earthdata — Harmonized Landsat and Sentinel-2 (HLS) | HLS S30/L30 ở 30 m, lưới UTM/MGRS; đường truy cập cụ thể còn phải chốt/thử tại G0 |

Đã đọc model card/config và tài liệu sản phẩm ngày 08/11/2026. Chưa tải/chạy trọng số; không có bằng chứng ONNX export, INT8, tốc độ CPU hoặc chất lượng nghiệp vụ của GeoAI. Bản thân link/checkpoint nền không phải bộ model pack phân tích hoàn chỉnh: decoder, dữ liệu tinh chỉnh, code, môi trường và giấy phép liên quan phải được khóa và kiểm chứng trước phát hành.

Bản 1.2 bổ sung đối chiếu nguồn chính thức về biến thể Prithvi, quantization, serialization và Windows handles trong cùng ngày. Đây là xác minh tài liệu, chưa phải chạy các fixture đề xuất. Thống kê coverage HLS, giới hạn thử nghiệm G0 và các số đo G1/G2 vẫn là công việc cần thực hiện; không ghi ước lượng pixel hoặc thông số upstream thành kết quả nghiệm thu.

Bản 1.3 bổ sung đối chiếu tài liệu SQLAlchemy, Alembic và Windows Job Objects trong ngày 08/11/2026. Cấu hình phần cứng, p95 viewer, codec COG và adapter xác thực là đề xuất/điều kiện thử nghiệm; chưa chạy benchmark, kiểm thử bảo mật hay migration của GeoAI.

<a id="muc-19-5"></a>

### 19.5. Nguồn mô hình toán–vật lý đã đối chiếu

| Mã | Nguồn | Phạm vi xác nhận |
| --- | --- | --- |
| [F1] | PROSAIL Python bindings; mô tả PROSPECT và 4SAIL | Forward leaf/canopy reflectance và tham số cần khóa; repository này không tự xác nhận độ phù hợp từng cảm biến hay giấy phép phân phối toàn app |
| [F2] | FAO-56 Penman–Monteith; công thức triển khai tham chiếu PyETo | ET0 theo khí tượng ngày, đơn vị/hằng số; ETc và stress cần Kc/dữ liệu kiểm định riêng |
| [F3] | Bastiaanssen et al., SEBAL, DOI 10.1016/S0022-1694(98)00253-4 | Tham chiếu phương pháp cân bằng năng lượng và suy ET; đã đối chiếu metadata bài báo, chưa đọc toàn văn trong lần cập nhật này |
| [F4] | USACE HEC-HMS — SCS Curve Number loss model | Phương trình Pe, Ia, S và CN; tài liệu yêu cầu calibration/validation thay vì dùng CN bảng như kết quả cuối |
| [F5] | Nobre et al., HAND, DOI 10.1016/j.jhydrol.2011.03.051 | Tham chiếu mô hình địa hình HAND; đã đối chiếu metadata bài báo, chưa đọc toàn văn trong lần cập nhật này |
| [F6] | USACE HEC-RAS technical reference — 2D shallow-water/diffusion-wave basis | Bảo toàn khối lượng/động lượng, giả định và lựa chọn solver; feature cần adapter/giấy phép/kiểm chứng riêng |
| [F7] | USDA-ARS — RUSLE1.06c description | Các hệ số R, K, LS, C, P và phạm vi xói mòn tấm/rãnh nhỏ; không phải sediment yield tổng quát |
| [F8] | Chave et al. 2014, DOI 10.1111/gcb.12629; package BIOMASS implementation | Đã đọc abstract qua Crossref và code computeAGB: phương trình có D/H/wood density, đổi kg sang Mg; miền hiệu lực rừng nhiệt đới cần kiểm định địa phương |

Bản 1.4 bổ sung danh mục mô hình toán–vật lý và phương trình profile cho chỉ số/diện tích, PROSAIL, FAO-56, SEBAL, SCS-CN, HAND, nước nông 2D, RUSLE và allometry carbon. Phạm vi đọc nguồn ghi riêng trong bảng: trang FAO-56 trả HTTP 403 nên đối chiếu công thức/đơn vị ET0 qua PyETo; F3/F5 mới xác nhận thư mục bài báo. Đây là đặc tả dự kiến; chưa triển khai solver, hiệu chuẩn hay kiểm định thực địa. Chỉ GEO-01 thuộc G0–G2, các feature PHY là mở rộng G4.

<a id="muc-20"></a>

## 20. Lịch sử tài liệu

| Phiên bản | Ngày | Thay đổi |
| --- | --- | --- |
| 1.0 | 08/11/2026 | Tổng hợp ưu điểm của hai đề xuất và hai cẩm nang; bổ sung đối chiếu sản phẩm chính thức, hợp đồng dữ liệu, review/revision, vòng đời job, backup, phạm vi MVP và cổng nghiệm thu |
| 1.1 | 08/11/2026 | Đưa Prithvi-EO-2.0 vào phạm vi bắt buộc từ bản đầu; bổ sung backbone/decoder, profile HLS và band/time/normalization contract. Cập nhật bảng chọn nghiệp vụ G0, CRS/VN-2000, IPC, CPU SLO, ưu tiên ONNX có ngoại lệ PyTorch, log/chẩn đoán/golden fixture, pin/retention, project local và review hai trạng thái; đồng bộ bộ cài và nghiệm thu. Đây là sửa thiết kế, chưa triển khai/benchmark |
| 1.2 | 08/11/2026 | Bổ sung ngưỡng tuyệt đối/quy tắc dừng, chuẩn bị nhãn từ G0 và tách spike G1 khỏi nghiệm thu checkpoint G2; khảo sát HLS/credential/UTM; ứng viên 100M-TL/tiny-TL/non-TL, profile ONNX cố định và dynamic INT8 có điều kiện; an toàn chuyển đổi trọng số và stdout Windows. Đồng bộ README và 17 tài liệu trong plans, giữ số mục/liên kết và trạng thái đề xuất; chưa chạy benchmark hoặc nghiệm thu nghiệp vụ |
| 1.3 | 08/11/2026 | Tiếp thu chọn lọc bản hợp nhất chuyên gia: hướng phụ thuộc module/CI, SQLAlchemy/Alembic và upgrade/restore, hai profile COG dùng chung khi phù hợp, token loader/Host/Origin, Windows Job Object với dừng có kiểm soát, cấu hình nghiệm thu mẫu và sổ ADR. Giữ các điều kiện v1.2 và đồng bộ README cùng 17 tài liệu; chỉ cập nhật thiết kế, chưa triển khai/benchmark |
| 1.4 | 08/11/2026 | Bổ sung PhysicalModelSpec, danh mục mô hình toán–vật lý và phương trình/đơn vị/giới hạn cho chỉ số phổ, PROSAIL, FAO-56, SEBAL, SCS-CN, HAND, nước nông 2D, RUSLE và allometry sinh khối/carbon; thêm hiệu chuẩn, độ bất định và cổng kiểm chứng. Các feature vật lý mở rộng ở G4; bản đầu vẫn GEO-01 + Prithvi và baseline, chưa triển khai/benchmark |

**Bổ sung đặc tả cho baseline v1.4, 08/11/2026:** liên kết SPEC-008 tạo model nghiệp vụ, SPEC-009/worker access context và security acceptance, ADR-011 giới hạn đồng thời liên project/instance; đồng bộ docs/kiến trúc/plans chịu ảnh hưởng. Đây là tài liệu dự thảo để triển khai, chưa làm code, chưa chốt dữ liệu/ngưỡng/nhân sự hoặc tạo bằng chứng runtime.

**Bổ sung yêu cầu G0 cho baseline v1.4, 08/11/2026:** người dùng xác nhận chia đợt, HLS 30 m + lớp phủ/NDVI/EVI/NDMI/MNDWI/thống kê/PDF trước, các nghiệp vụ rừng/ngập và profile 10/5/1 m sau; nguồn mở/miễn phí trước, thương mại khi có quyền/ngân sách, mục tiêu máy 20 GB RAM/8 GB VRAM còn chờ kiểm chứng. Bổ sung công thức EVI vào GEO-01 và đồng bộ tài liệu chịu ảnh hưởng; [hồ sơ quyết định từng phần](../docs/evidence/g0/decision-record.md), G0 chưa đạt, chưa code hoặc benchmark.

---

**Tài liệu liên quan:**

- [Cơ sở đề xuất và tham chiếu thị trường](02_co_so_de_xuat_va_tham_chieu_thi_truong.md)
- [Model Prithvi, dữ liệu nhãn và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md)

[A]: <../solution/de_xuat_kien_truc_he_thong_geoai.md>
[B]: <../solution/de_xuat_kien_truc_he_thong_geoai_copilot.md>
[C1]: <../solution/cam_nang_kien_truc_ung_dung_geoai_vien_tham.md>
[C2]: <../solution/Hướng dẫn xây dựng ứng dụng GeoAI cho viễn thám.md>
[M1]: https://doc.esri.com/en/arcgis-pro/latest/help/analysis/deep-learning/deep-learning-in-arcgis-pro.html
[M2]: https://doc.esri.com/en/arcgis-pro/latest/help/analysis/image-analyst/deep-learning-models-in-arcgis.html
[M3]: https://doc.esri.com/en/arcgis-pro/latest/tool-reference/image-analyst/compute-accuracy-for-object-detection.html
[M4]: https://doc.esri.com/en/arcgis-pro/latest/help/analysis/image-analyst/review-results-from-deep-learning.html
[M5]: https://www.nv5geospatialsoftware.com/docs/Introduction.html
[M6]: https://www.nv5geospatialsoftware.com/docs/OverviewENVIDeepLearning.html
[M7]: https://www.nv5geospatialsoftware.com/docs/ConfigureONNXModel.html
[M8]: https://www.nv5geospatialsoftware.com/docs/ViewTrainingMetrics.html
[M9]: https://docs.picterra.ai/detectors/annotations/
[M10]: https://docs.picterra.ai/detectors/detector-insights/
[M11]: https://docs.picterra.ai/detection_results/
[M12]: https://docs.picterra.ai/reports/
[M13]: https://docs.up42.com/data/catalog-process
[M14]: https://docs.up42.com/data-management/assets
[M15]: https://developers.google.com/earth-engine/guides/processing_environments
[M16]: https://developers.google.com/earth-engine/guides/usage
[M17]: https://geospatial.trimble.com/en/products/software/trimble-ecognition
[T1]: https://stacspec.org/en
[T2]: https://docs.ogc.org/is/21-026/21-026.html
[T3]: https://giro3d.org/latest/apidoc/index.html
[T4]: https://v2.tauri.app/distribute/windows-installer/
[T5]: https://sqlite.org/wal.html
[T6]: https://giro3d.org/latest/examples/index.html
[T7]: https://proj.org/en/stable/operations/operations_computation.html
[T8]: https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html
[T9]: https://www.jsonrpc.org/specification
[T10]: https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html
[T11]: https://github.com/pytorch/pytorch/blob/main/docs/source/notes/serialization.md
[T12]: https://learn.microsoft.com/en-us/windows/console/getstdhandle
[T13]: https://docs.sqlalchemy.org/en/20/intro.html
[T14]: https://alembic.sqlalchemy.org/en/latest/batch.html
[T15]: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
[P1]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL/raw/63adbd39c271da4c42f447e69b1a7c91a338cdc9/README.md
[P2]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL/raw/63adbd39c271da4c42f447e69b1a7c91a338cdc9/config.json
[P3]: https://raw.githubusercontent.com/NASA-IMPACT/Prithvi-EO-2.0/main/configs/sen1floods11.yaml
[P4]: https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSS30_v002
[P5]: https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSL30_v002
[P6]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-tiny-TL/tree/335eadc2c45ad5abe7bd307223e1c48c5b60c41b
[P7]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-100M-TL/tree/2c84e383194986040f883cc43d7869002c425e1b
[P8]: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M/tree/9eb1b1102806593963daa333bcc491b1c6f8562f
[P9]: https://www.earthdata.nasa.gov/data/projects/hls
[F1]: https://github.com/jgomezdans/prosail
[F2]: https://github.com/woodcrafty/PyETo/blob/master/pyeto/fao.py
[F3]: https://doi.org/10.1016/S0022-1694(98)00253-4
[F4]: https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/canopy-surface-infiltration-and-runoff-volume/infiltration/scs-curve-number-loss-model
[F5]: https://doi.org/10.1016/j.jhydrol.2011.03.051
[F6]: https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.6/theoretical-basis-for-one-dimensional-and-two-dimensional-hydrodynamic-calculations/2d-unsteady-flow-hydrodynamics
[F7]: https://www.ars.usda.gov/southeast-area/oxford-ms/national-sedimentation-laboratory/watershed-physical-processes-research/docs/revised-universal-soil-loss-equation-106-description-of-rusle106c/
[F8]: https://github.com/cran/BIOMASS/blob/master/R/computeAGB.R
