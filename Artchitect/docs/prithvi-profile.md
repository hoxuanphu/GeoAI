# Profile Prithvi bản đầu

Đọc khi làm model/preprocess. Nguồn: [mục 8.2](../plans/07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-2), [runtime/G1–G2](../plans/12_runtime_cpu_nvidia_va_hieu_nang.md), ADR-004/008.

[Quyết định G0 từng phần](evidence/g0/decision-record.md) xác nhận HLS 30 m trước và profile 10/5/1 m sau. HLS không có các mức quan trắc gốc 10/5/1 m; resample không tạo chi tiết mới. Sentinel-2 L2A có band khác GSD, gồm B8A/B11/B12 ở 20 m; không coi mọi band là gốc 10 m. Ảnh 5/1 m thiếu SWIR hoặc chỉ RGB cần profile/model phù hợp riêng, không lặp kênh để đưa vào profile HLS. Chưa có nguồn/model mở rộng nào được kiểm; mục tiêu 8 GB VRAM chưa chứng minh inference hay fine-tune 300M + UPerNet khả thi.

Bộ lớp nghiệp vụ 7 lớp và crosswalk WorldCover/JAXA được ghi tại [landcover taxonomy](domain/landcover-taxonomy.md). Profile kỹ thuật giữ T=1 cho spike; người dùng đã xác nhận profile nghiệp vụ T=3 cho bảy lớp. T=3 cần ba quan sát thật, cùng grid và metadata từng frame, fine-tune/evaluation/export riêng; không lặp một ảnh hoặc suy coverage dài hạn từ ba frame.

## Profile dữ liệu và tensor

| Thành phần | Quy tắc |
| --- | --- |
| Feature đề xuất | Phân đoạn lớp phủ, bộ lớp/nhãn địa phương chốt G0 |
| Backbone/decoder | Khởi đầu Prithvi-EO-2.0-300M-TL + UPerNet theo TerraTorch; revision tham chiếu `63adbd39c271da4c42f447e69b1a7c91a338cdc9` |
| Ứng viên | 100M-TL, tiny-TL 5M cho CPU; 300M non-TL để so metadata policy; tất cả phải kiểm định downstream |
| Nguồn đầu | HLS S30 v2 surface reflectance, 30 m; L30 chỉ thêm sau kiểm mapping/QA |
| Thứ tự phổ | Blue, Green, Red, Narrow NIR, SWIR1, SWIR2 |
| S30 | B02, B03, B04, B8A, B11, B12 |
| L30 | B02, B03, B04, B05, B06, B07 |
| Shape spike kỹ thuật | B × 6 × 1 × 224 × 224; patch 1 × 16 × 16; batch 1 ban đầu |
| Shape nghiệp vụ 7 lớp | B × 6 × 3 × 224 × 224; ba thời điểm thật, patch không gian 16 × 16; cần profile/export riêng |
| Thời gian | T=1 chỉ cho spike; T=3 cho model nghiệp vụ phải fine-tune/kiểm định; config pretrain 4 frame không được lặp một ảnh thành bốn quan sát giả |
| ONNX | C/T/H/W cố định; chỉ mở batch động sau benchmark và kiểm operator/output |

TL lấy acquisition date và tâm cửa sổ WGS84 từ metadata tin cậy theo encoding đúng version. Thiếu metadata thì chặn hoặc dùng profile thiếu metadata đã fine-tune/kiểm định; upstream metadata dropout không tự chứng minh downstream đạt. Non-TL vẫn giữ scene/ngày/CRS/QA trong provenance.

Giao nhận cặp ảnh/nhãn theo [nhóm 3/4 của SPEC-002](specs/002-g0-evidence.md#nhóm-3--nguồn-ảnh-và-đóng-gói-input-x): Y có ngày/kỳ tham chiếu riêng cho chuỗi T=3, giữ frame dates thực và cùng grid/masks. TL giữ ngày đầy đủ, kiểm năm nhuận/ngày thứ 366 khi hợp lệ rồi encode theo code revision; không tự ép day-of-year về 1–365. Fmask là QA phụ trợ, không là kênh phổ hoặc bộ phát hiện mọi sương mù.

## Normalization và ghép cửa sổ

Áp product scale/offset về đúng đơn vị rồi dùng mean/std cùng đơn vị với checkpoint/downstream. Nếu config thống kê theo DN mà dữ liệu đã reflectance ×0,0001 thì đổi mean/std tương ứng; không scale hai lần, không dùng display stretch. Các hằng số phải lấy từ config/checkpoint đã khóa; schema fixture dùng mean/std giả cho validation, không phải cấu hình inference thật.

Loại invalid khỏi loss/metrics/output; quy tắc fill/mask giống train. Padding, overlap, blend/upsample và crop về GridSpec phải được chọn bằng fixture. Không resize cả AOI về 224. Sentinel-2 L2A resample không tự thành HLS; không thay band bằng SAR/DEM/RGB lặp kênh.

`ignore_index = -1` phải được cấu hình trong loss và lọc tương ứng ở metrics; backbone không tự bỏ qua nhãn chỉ vì giá trị âm. Với loss không có ignore_index phải dùng mask tương đương; batch toàn ignore phải skip/xử lý hữu hạn và ghi nhận, không tính như batch phân loại hợp lệ. Label-valid mask và observation-valid mask có ý nghĩa riêng.

Ảnh một ngày được ưu tiên; composite phải có recipe và ngữ nghĩa thời gian được model chấp nhận, đủ scene/date lineage. Phương pháp ghép cụ thể/overlap chưa chốt bằng benchmark, dev không tự ghi 50% là yêu cầu đã duyệt.

## Hai bước kiểm chứng

- G1: backbone thật + decoder đúng kiến trúc có thể ngẫu nhiên, seed/hash rõ. Đo shape, export/load, sai khác FP32, thời gian/RAM sơ bộ; không dùng F1 ngẫu nhiên để nghiệm thu chất lượng.
- G2: checkpoint nghiệp vụ đã huấn luyện, test độc lập theo vùng/thời gian, golden output riêng; chạy lại mọi precision/runtime định phân phối. Ghi per-class F1/IoU, coverage, lớp hiếm và tổng thời gian job.

CPU chính thức; NVIDIA pack tùy chọn. Dynamic INT8 trên linear/MatMul transformer chỉ thử khi profiling có lợi; static Conv/decoder cần calibration đại diện tách test. Cả hai vẫn cần gate nghiệp vụ. PyTorch inference CPU/CUDA là ngoại lệ khi ONNX chưa đúng/không có lợi, có hồ sơ version/dung lượng/benchmark.

## Điểm dừng

Các giá trị người dùng cung cấp nằm trong [tiêu chí nghiệm thu](domain/acceptance-criteria.md); máy GPU mới đã được xác nhận dùng riêng training/benchmark, giữ mục tiêu desktop trước đó. Protocol/máy thực/CPU SLO còn mở. Giữ T=3/224 nghiệp vụ, T=1 spike, S30 trước; median 60–90 ngày/S30+L30, window 512 hoặc DEM là ứng viên phải kiểm riêng. Không tính pixel imputation thành quan sát sạch, không dùng SLA GPU thay CPU SLO; các cap/early stopping cần khóa trong recipe và kiểm bằng log thực.

G0 chốt AOI/lớp/nhãn, ngưỡng tuyệt đối, coverage, thời gian/RAM, số vòng tối đa, trần chi phí/thời gian và người quyết định. Không tự điền F1 hay deadline đã được duyệt. Prithvi đạt gate thì có thể phát hành dù RF tốt hơn; công bố đối chứng cùng split. Hết ngân sách chưa đạt thì hoãn/thu hẹp/đổi yêu cầu có quyết định; không hạ gate hồi tố hoặc thay RF rồi ghi đã nghiệm thu Prithvi.

Trọng số chuyển trên build cô lập sang ONNX/safetensors, manifest tin cậy và hash; `.pt` ngoại lệ dùng PyTorch đã vá + `weights_only=True`, không tự mở pickle không hạn chế. Chưa có checkpoint downstream, nhãn/test, benchmark hay ONNX nghiệp vụ của GeoAI.

## Hồ sơ dev phải bàn giao

| Hồ sơ | Tối thiểu phải có |
| --- | --- |
| Product/preprocessing | Provider/collection/version, sáu band đúng thứ tự, QA bit policy, scale/offset và đơn vị, mask/fill/padding/window/crop, metadata encoding theo revision |
| Model/decoder | ModelSpec và hash trọng số, kiến trúc/source revision, decoder đã huấn luyện hay seed kỹ thuật, class schema, normalization có nguồn, license và conversion record |
| Runtime | C/T/H/W/batch, backend/precision/operators, output tolerance với FP32 đặt trước tối ưu, device/driver/pack inventory; fallback policy và thực tế dùng |
| Evaluation | DatasetVersion/split/hash, technical hay business, per-class metrics/coverage, RF đối chứng cùng test, gate/version và phạm vi vùng/mùa |
| Benchmark | Workload/AOI hợp lệ, cold/warm, tổng job và từng phase, peak RAM/VRAM/temp, UI đồng thời và cấu hình máy thực |

Từ chối input sai band/unit/T/GSD hoặc TL metadata thiếu bằng lỗi rõ trước enqueue/start. Nếu profile cho phép thiếu metadata hoặc composite thì phải có checkpoint/evaluation cho đúng trường hợp, không bật chỉ vì code nhận tensor. Loại pixel invalid khỏi thống kê, lưu mask/coverage/source ngày vào artifact/manifest; không hiển thị background giả như quan sát.

Các hồ sơ G0 thuộc [SPEC-002](specs/002-g0-evidence.md), spike kỹ thuật thuộc [SPEC-005](specs/005-prithvi-spike.md). [SPEC-008](specs/008-training-evaluation-model-pack.md) tạo dataset/split/recipe/checkpoint/evaluation/model pack nghiệp vụ; [SPEC-006](specs/006-landcover-workflow.md) nhận pack và kiểm workflow tới PDF. Nhãn/training chuẩn bị song song G1 theo dependency, không đợi mọi UI hoàn tất. Có thể sàng lọc các biến thể trong ngân sách đã chốt; không cần chạy hết mọi thử nghiệm 300M trước khi đo ứng viên CPU nhỏ. Hiện mới có tài liệu và metadata fixture, chưa có tensor fixture thực hoặc model pack đã chạy.
