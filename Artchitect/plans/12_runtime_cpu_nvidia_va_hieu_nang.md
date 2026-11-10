# Runtime CPU/NVIDIA và hiệu năng

> Đồng bộ từ [bản tổng hợp v1.4](../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), ngày 08/11/2026. Đây là đề xuất thiết kế; chưa triển khai hoặc benchmark. Số mục được giữ theo tài liệu gốc.

[Mục lục bộ tài liệu](README.md) · [Danh mục nguồn](17_nguon_tham_khao_va_lich_su.md)

**Phạm vi:** ONNX/PyTorch, chọn thiết bị, compute pack và ngân sách CPU.

<a id="muc-13"></a>

## 13. CPU/NVIDIA và môi trường chạy

Người dùng nêu mục tiêu máy dự kiến ít nhất 20 GB RAM và 8 GB VRAM; chưa có CPU/GPU/hãng/OS/driver/SSD, dung lượng khả dụng, workload và SLO cụ thể. Đây chưa là support matrix hoặc bằng chứng inference/fine-tune đủ tài nguyên. Benchmark inference theo cửa sổ/tổng job và ngân sách training ở môi trường ngoài desktop phải được xác định riêng; không suy GPU NVIDIA chỉ từ dung lượng VRAM.

| Thành phần | Lựa chọn đầu | Điều kiện mở rộng |
| --- | --- | --- |
| CPU | NumPy/scikit-learn cho baseline; **ưu tiên ONNX Runtime CPU cho Prithvi + decoder**; PyTorch CPU nếu export chưa đạt | Cấu hình chính thức, có workload/thời gian/RAM riêng; không chỉ là fallback khi thiếu NVIDIA |
| NVIDIA | **Ưu tiên ONNX Runtime CUDA**; PyTorch CUDA là ngoại lệ có hồ sơ lý do | TensorRT/compile/INT8 khi có lợi đầu cuối và đạt quality gate |
| AMD/Intel | Render qua GPU đồ họa khi tương thích; AI dùng CPU | Runtime AI khác cần máy, model và support matrix riêng |
| Training | PyTorch/TerraTorch trong môi trường phát triển/server riêng để huấn luyện decoder/tinh chỉnh Prithvi | Không kèm notebook, optimizer hoặc môi trường training đầy đủ vào desktop |
| Toán–vật lý | CPU NumPy/SciPy cho đại số, chỉ số, tối ưu/LUT và uncertainty; solver chuyên ngành qua adapter khi mở feature | Kiểm đơn vị, cân bằng/hội tụ và ngân sách riêng; không mặc định mọi solver xuất ONNX, chạy GPU hoặc checkpoint theo tile |

Luồng chọn thiết bị: phát hiện → kiểm tra compatibility matrix → probe operator/model → so sánh kết quả → benchmark → lưu cấu hình theo máy/model. `auto`, `cpu`, `gpu:<id>` có fallback policy rõ. Yêu cầu GPU bắt buộc không âm thầm chạy CPU; không tự chuyển sang cloud.

Core CPU và compute pack CUDA có môi trường riêng để tránh xung đột DLL/package. Các model tương thích dùng chung runtime pack theo version; không tạo một môi trường PyTorch đầy đủ cho mỗi model. ONNX Runtime CUDA vẫn có dependency CUDA/cuDNN và phải đo tổng dung lượng bộ phân phối [T10]. Cache engine khóa theo model + decoder hash, input profile, precision, GPU và runtime cần thiết. Tách GPU render và compute trong trang tài nguyên khi có thể truy vấn.

G1 xây đường tham chiếu PyTorch cho **toàn bộ Prithvi + decoder + metadata theo profile TL/non-TL**, rồi thử ONNX với T=1, H=W=224 và các chiều còn lại theo [mục 8.2](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-2). Lựa chọn runtime ở G1 là kết luận kỹ thuật sơ bộ khi decoder chưa được huấn luyện; chỉ phân phối ONNX mặc định khi checkpoint nghiệp vụ vượt kiểm tra operator, output, quality gate và hiệu năng ở G2. Nếu chưa export đúng hoặc không có lợi, giữ PyTorch inference pack tối thiểu với hồ sơ gồm nguyên nhân, phiên bản, dung lượng và benchmark; đây là ngoại lệ được thiết kế sẵn, không bỏ Prithvi khỏi bản đầu để tránh đóng gói. Không mặc định hỗ trợ mọi dynamic shape hoặc mọi số frame.

Giảm tải trước hết bằng đọc ít hơn, prefetch có hạn, cửa sổ/batch đúng contract, giới hạn thread và giữ model resident. **Thử INT8 sớm ở G1 nếu profiling cho thấy inference CPU là nút thắt**: bắt đầu bằng dynamic quantization cho các toán tử tuyến tính/MatMul được runtime hỗ trợ trong transformer, giữ các phần khác FP32. Dynamic không cần calibration offline nhưng có overhead tính tham số activation lúc chạy. Chỉ thử static quantization cho Conv/decoder sau khi profiling cho thấy có lợi và có tập calibration đại diện, tách khỏi test độc lập. Cả hai chỉ được phân phối sau đánh giá checkpoint nghiệp vụ theo lớp/vùng, tolerance và hiệu năng toàn pipeline. ONNX Runtime khuyến nghị dynamic cho transformer, static cho CNN và lưu ý quantization có thể giảm độ chính xác hoặc chậm hơn [T8]. Không coi INT8 là tối ưu bắt buộc cho RF/boosting; FP32 là đường tham chiếu.

<a id="muc-13-1"></a>

### 13.1. Workload và ngân sách CPU bắt buộc

[Tiêu chí nghiệm thu](../docs/domain/acceptance-criteria.md) ghi yêu cầu mới GPU 16–24 GB/RAM 32 GB/SSD 500 GB, VRAM ≤85%, SLA GPU ≤15 phút/tile T=3, cap training 4 GPU-giờ và early stopping. Người dùng xác nhận máy này dùng riêng training/benchmark; giữ mục tiêu desktop ít nhất 20 GB RAM/8 GB VRAM. Máy thực/ranh giới đo, CPU SLO và campaign/chi phí còn chờ khóa; không coi đây là benchmark hoặc support matrix đã đạt. Các ví dụ GPU/chip/epoch không thay đo thực; shape/precision/profile đổi phải đánh giá lại.

G0 chốt trước khi đo nghiệm thu: model CPU cụ thể, số core/thread dùng, RAM khả dụng, loại đĩa, dữ liệu/hash, AOI/số pixel hợp lệ, T, window/overlap, chất lượng tối thiểu, **thời gian job tối đa**, peak RAM và đĩa tạm. Có hai mức: fixture nhỏ kiểm tra tính đúng và workload nghiệp vụ đại diện để quyết định khả năng sử dụng. G1 đo cold/warm time, thời gian riêng I/O/preprocess/inference/postprocess/report và phản hồi UI; không chỉ ghi tốc độ một patch rồi suy ra tốc độ toàn AOI.

Prithvi-300M-TL có thể nặng trên CPU; tài liệu chưa có số đo để cam kết phút/km². Nếu không đạt ngân sách, đánh giá ONNX/INT8, giới hạn workload được hỗ trợ hoặc biến thể nhỏ hơn **thuộc Prithvi-EO-2.0** với decoder đã kiểm định; ghi rõ quyết định và giữ cùng quality gate. Không âm thầm chuyển sang baseline hoặc server, và không gọi CPU “được hỗ trợ” nếu chỉ load được model nhưng không hoàn thành workload tối thiểu. Mixed precision/compile/TensorRT tiếp tục được kiểm tra theo backend; không gộp VRAM của các card thành một pool.

Ước lượng quy mô, không phải benchmark: AOI 10.000 km² ở 30 m có khoảng 11,1 triệu pixel, tương đương khoảng 221 cửa sổ 224 × 224 không overlap hoặc khoảng 886 cửa sổ theo stride 112 (overlap 50% mỗi chiều). Số cửa sổ thực còn phụ thuộc hình AOI, biên/padding, mask và cách ghép tile. Với cùng diện tích, 30 m có khoảng một phần chín số pixel của 10 m, nhưng RAM, cache và thời gian toàn pipeline không nhất thiết giảm chín lần. Chưa đo encoder + decoder và I/O trên CPU reference thì chưa kết luận hàng chục phút hay hàng giờ. 100M-TL/tiny-TL ở [mục 8.2](07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-2) là ứng viên cần đo, không phải cam kết tăng tốc hoặc giữ chất lượng.

<a id="muc-13-2"></a>

### 13.2. Spike kỹ thuật và kiểm chứng model nghiệp vụ

| Bước | Dữ liệu/model | Kết quả và giới hạn |
| --- | --- | --- |
| G1 — khả thi kỹ thuật, song song gán nhãn | Backbone Prithvi thật đã khóa revision; UPerNet đúng kiến trúc/profile dự kiến nhưng có thể khởi tạo ngẫu nhiên với seed/hash cố định; fixture HLS thật, metadata/QA hợp lệ | Kiểm tra tensor/grid, export/load ONNX, operator, output FP32 giữa runtime, cold/warm time và peak RAM; thử dynamic INT8 nếu cần. Ghi rõ decoder chưa huấn luyện; sai khác INT8 chỉ là chẩn đoán kỹ thuật, chưa phải bằng chứng chất lượng |
| G2 — model nghiệp vụ trước nghiệm thu | Checkpoint encoder + decoder đã huấn luyện, profile đầu vào thực, bộ nhãn/test độc lập và workload đại diện | Chạy lại export, tolerance, benchmark CPU/NVIDIA và mọi precision định phân phối; đánh giá theo lớp/vùng, coverage và baseline. Thay checkpoint/decoder/profile làm mất hiệu lực những số đo cũ bị ảnh hưởng |

G1 khóa fixture/tolerance kỹ thuật trước tối ưu và chỉ chọn sơ bộ runtime/biến thể khi chưa có checkpoint nghiệp vụ. Fixture decoder ngẫu nhiên giữ namespace/version riêng; golden output nghiệp vụ được tạo và duyệt từ checkpoint thật trước nghiệm thu G2. Không dùng output ngẫu nhiên để tính F1/IoU nghiệp vụ hoặc bật model cho người dùng. Khả năng export và mức chi phí sơ bộ có thể khảo sát trước nhãn; ổn định số, quantization và chất lượng cuối vẫn phụ thuộc trọng số, input và runtime thực.

<a id="muc-13-3"></a>

### 13.3. Cấu hình khởi điểm để chốt workload

Các con số dưới là **ứng viên thảo luận tại G0**, không phải cấu hình tối thiểu đã xác nhận hoặc support matrix phát hành. Chỉ chốt workload khi có model CPU cụ thể, OS/build được hỗ trợ, RAM khả dụng, đĩa, ngân sách thời gian và profile dữ liệu theo [mục 13.1](12_runtime_cpu_nvidia_va_hieu_nang.md#muc-13-1).

| Mức | Ứng viên đề xuất | Điều cần kiểm chứng |
| --- | --- | --- |
| Máy văn phòng | Windows x64; CPU 8 nhân, RAM 16 GB, SSD, không GPU rời | Ghi model CPU/core/thread thực và RAM còn cho worker; đo Prithvi + decoder, peak RAM và phản hồi UI. Không suy mọi CPU 8 nhân có cùng throughput |
| Máy trạm | Windows x64; RAM 32 GB, NVIDIA khoảng 8 GB VRAM trở lên | Chốt model GPU/driver/runtime và VRAM dành cho viewer/OS; dung lượng VRAM đơn thuần không chứng minh tương thích hoặc đủ batch |
| AOI đại diện | HLS S30 30 m, T=3 nghiệp vụ/T=1 spike; thử một tỉnh khoảng 5.000–15.000 km² bên cạnh fixture nhỏ | Chốt footprint, mùa/coverage, số pixel thực xử lý, padding/overlap và I/O; giới hạn AOI hỗ trợ dựa trên đo G1 và xác nhận checkpoint nghiệp vụ G2 |

Ngân sách thời gian job chưa có giá trị mặc định; chủ nghiệp vụ chốt tại G0. Mục tiêu viewer theo [mục 11](10_viewer_gis_3d_va_kiem_tra_ket_qua.md#muc-11) là phép đo riêng trên scene cố định, kể cả khi AI đang chạy. Không dùng cấu hình ứng viên hoặc ước lượng số pixel để tuyên bố tốc độ hàng chục phút hay khả năng chạy trên mọi máy văn phòng.

---

**Tài liệu liên quan:**

- [Model Prithvi, dữ liệu nhãn và kiểm định](07_model_prithvi_nhan_va_kiem_dinh.md)
- [Job, tài nguyên và phục hồi](08_job_tai_nguyen_va_phuc_hoi.md)
- [Stack và bộ cài Windows](13_stack_va_bo_cai_windows.md)
- [Lộ trình và cổng nghiệm thu](15_lo_trinh_va_cong_nghiem_thu.md)

[T8]: https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html
[T10]: https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html
