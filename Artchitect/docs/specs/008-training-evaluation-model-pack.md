# SPEC-008 — Dataset, training, evaluation và model pack nghiệp vụ

**Trạng thái:** mới có đặc tả; chưa có dataset/recipe/checkpoint/evaluation nghiệp vụ. Chưa triển khai code.
**Mục tiêu:** tạo đầu vào model nghiệp vụ có thể kiểm toán cho SPEC-006; không để checkpoint đã huấn luyện xuất hiện như dependency không có task sản xuất.

## Dependency và phạm vi

Đọc [Prithvi profile](../prithvi-profile.md), [domain rules](../domain-rules.md), [contracts](../contracts.md), [vòng đời model](../../plans/07_model_prithvi_nhan_va_kiem_dinh.md#muc-8-3), ADR-004/008. SPEC-002 cung cấp feature/AOI/class schema, nhãn/split policy/license, gate tuyệt đối, hardware và ngân sách/điểm dừng được xác nhận; SPEC-001 cung cấp contracts và exporter đã kiểm. SPEC-005 cung cấp kết quả sàng lọc input/shape/runtime, không phải checkpoint business.

Trước G0 có thể viết recipe outline, kiểm nhãn và lập kế hoạch dữ liệu bằng nguồn được phép; chưa coi recipe/hyperparameter/ngưỡng là đã chốt, chưa đánh giá pass nghiệp vụ. Chuẩn bị nhãn/split chạy song song G1. Training không cần đợi toàn bộ UI/viewer/bundle, nhưng phải khóa profile ứng viên và có ngân sách chạy; promotion/pack cuối cần chạy lại các kiểm export/runtime G2 liên quan.

Training nằm trong môi trường phát triển riêng. Chưa quyết định repo riêng hay thư mục trong repo: ML phải ghi vị trí checkout/code revision và môi trường thực trong training manifest trước chạy. Không thêm notebook/optimizer/training runtime vào desktop, không dựng hệ annotation tổng quát.

## Trách nhiệm và đầu ra bàn giao

| Đầu ra | Vai trò thực hiện | Vai trò kiểm/chốt |
| --- | --- | --- |
| Nhãn, class definition, quyền sử dụng, DatasetVersion/split | GIS/data và người gán nhãn | Chủ nghiệp vụ/người duyệt nhãn; reviewer GIS kiểm leakage |
| Recipe, environment lock, training manifest/checkpoint | ML engineer | Reviewer ML kiểm nguồn/profile/reproducibility; chủ dự án chốt ngân sách |
| Evaluation độc lập và RF/boosting đối chứng | ML/evaluation reviewer | Người kiểm định độc lập với việc chọn checkpoint; chủ nghiệp vụ chốt gate |
| Conversion, runtime benchmark, model pack | ML + runtime/packaging engineer | QA kiểm pack; chủ nghiệp vụ/chủ dự án quyết định promotion |
| Tích hợp feature và báo cáo | Dev SPEC-006 | QA/người dùng theo acceptance G2 |

Một người có thể kiêm vai trò, nhưng việc chọn/tinh chỉnh model không được dùng test độc lập như validation. SPEC-002 phải ghi tên người hoặc vai trò tổ chức được giao thực và người có quyền chốt; bảng này chưa là phân công nhân sự đã xác nhận.

## Input và hồ sơ output

Input thực: HLS S30 v2 sáu band/QA/ngày/tọa độ/grid đã kiểm, label assets có class schema và ngày phù hợp, split trước chipping, backbone revision/license, decoder architecture, profile nghiệp vụ T=3/224 theo [Prithvi profile](../prithvi-profile.md), normalization/metadata policy và budget. T=1 chỉ là spike kỹ thuật, không thay profile nghiệp vụ khi bàn giao. Các con số trong fixture contracts không phải normalization hoặc tolerance để huấn luyện.

Bộ lớp theo [taxonomy](../landcover-taxonomy.md): IDs 0–6 là bảy lớp học; `ignore_index = -1` không tạo kênh thứ tám. Khóa crosswalk theo version WorldCover/JAXA, xử lý ao nuôi có điều kiện và bổ sung nhãn wetland có cây gỗ còn thiếu; không dùng weak labels sinh train làm test truth độc lập. Recipe/model pack phải ghi T=3, class mapping/ignore, ngày từng frame và policy frame thiếu; không lặp ảnh để đủ shape. [Bằng chứng ghi nhận yêu cầu](../evidence/2026-11-08-aoi-taxonomy-review.md) chỉ kiểm tài liệu.

Output dự kiến ở kho model/data được kiểm soát; Git chỉ giữ manifest đã lọc và fixture nhỏ được phép:

| Hồ sơ | Nội dung tối thiểu |
| --- | --- |
| Dataset/split manifest | IDs/hash ảnh/nhãn, label source/license/reviewer/date, class mapping/ignore, vùng/mùa, split IDs, group/buffer policy và kiểm overlap trước chipping |
| Recipe có version | Code/environment/backbone/decoder revisions, freeze/unfreeze strategy, optimizer/scheduler/loss, learning rate/epoch/batch/seed, augmentation, imbalance/ignore policy, model selection/early stop và ngân sách |
| Pre/postprocess profile | Band/order/scale/offset/unit/mean/std có nguồn; TL encoding/date/location, mask/fill/padding/window/overlap/blend/crop/GridSpec khớp train và inference |
| Training manifest | Recipe/hash, dataset/split hash, hardware/software và seed, lệnh thực, log/checkpoint history, best-checkpoint selection reason, chi phí/thời gian thực |
| Checkpoint | Prithvi encoder + decoder đã huấn luyện, weights/hash/format/license, class schema và inference config; optimizer state chỉ ở kho training, không trong desktop pack |
| EvaluationRecord + báo cáo | Dataset/test split/hash, preprocessing/checkpoint hash, per-class F1/IoU/support, coverage/vùng/mùa, RF baseline cùng split, gate/version/decision và limitations |
| ModelSpec + pack | Manifest tin cậy, weights/runtime/conversion hashes, pre/postprocess/profile, evaluation refs, licenses/notices, readiness theo kết quả, compatibility và golden output nghiệp vụ |

Recipe phải có giá trị cụ thể và người review trước lần chạy thật; spec này không tự đặt learning rate, epoch, buffer hay số vòng. Trường training/pack manifest cần schema có kiểu khi triển khai; không sửa tay JSON Schema hoặc coi dict tự do là hợp đồng ổn định.

Áp quy tắc [nguồn ảnh/nhãn X–Y tại SPEC-002](002-g0-evidence.md#nhóm-3--nguồn-ảnh-và-đóng-gói-input-x): manifest cặp mẫu có target date/period, ba frame dates, grid/hash, masks/ignore reasons và label lineage; nhãn 2D không tự đúng ở mọi frame khi có biến động. Weak labels chỉ warm-up train/gợi ý sửa theo policy tiếp nhận; nhãn giải đoán/thực địa cần QC độc lập, không mặc định là ground truth không sai số. Split/group/buffer được khóa trước chipping; kiểm leakage cả cửa sổ T=3 và nguồn sinh nhãn. Loss/metrics phải lọc ignore rõ và xử lý all-ignore batch, kiểm UInt8/255 ↔ -1 nếu dùng mapping đó. Số chip 300–500, cỡ chip 512 và độ chính xác >95% trong tài liệu cung cấp không là recipe/gate đã duyệt.

## Trình tự và acceptance

Người dùng đã cung cấp [bộ tiêu chí định lượng](../acceptance-criteria.md): per-class/macro/OA, coverage, diện tích/CI/CRS, cap 4 GPU-giờ/lần và early stopping min_delta 0,005/patience 15. Recipe/protocol phải khóa phạm vi/máy/cách đo, số vòng cụ thể trong khoảng 3–5 và chi phí/lịch trước chạy; không coi các khoảng còn mở là budget đã đầy đủ. Không lấy ví dụ chip 512/epoch để cam kết thời gian, không tự thêm DEM vào sáu band hoặc đổi họ Prithvi để đạt SLA. Chạm trần/ngưỡng không đạt thì trade-off report và quyết định có thẩm quyền, không hạ gate hồi tố.

1. Khóa dataset/class mapping/split, kiểm nhãn và leakage theo vùng/thời gian/scene trước chipping. Kiểm đủ IDs 0–6, ignore -1, mask QA không loại nước hợp lệ, crosswalk/nhãn độc lập và ba frame cùng grid theo taxonomy/profile. Không dùng prediction hoặc mọi edit review như ground truth chưa duyệt.
2. Khóa recipe/profile và budget/điểm dừng; làm smoke train trên tập nhỏ thuộc train để kiểm loss/mask/decoder/shape, không báo chất lượng từ smoke hoặc decoder ngẫu nhiên.
3. Huấn luyện/fine-tune Prithvi + decoder bằng train; chọn checkpoint/threshold bằng validation. Nếu đổi split/profile sau xem test thì version lại và tạo test độc lập phù hợp, không tiếp tục gọi test cũ là chưa bị sử dụng.
4. Chạy đánh giá một model được chọn trên test độc lập theo protocol đã khóa. Ghi cả lớp hiếm/lớp không đủ mẫu; thiếu dữ liệu để đánh giá lớp bắt buộc là chưa đủ bằng chứng, không gộp overall accuracy để che.
5. Chạy RF/boosting đối chứng cùng split và ngữ nghĩa đầu vào. Prithvi đạt ngưỡng tuyệt đối/coverage/tài nguyên thì có thể pass dù RF tốt hơn; RF không thay Prithvi hoặc quyết định gate hồi tố.
6. Export/convert đúng checkpoint encoder+decoder; đối chiếu FP32 và chạy lại mọi runtime/precision định phân phối, CPU workload SLO và NVIDIA nếu chọn phát hành pack. Tolerance được khóa trước tối ưu, không dựa benchmark decoder ngẫu nhiên để pass model cuối.
7. Kiểm manifest/weights/license/nguồn tin cậy trên build cô lập; promotion chỉ khi đủ evaluation và kiểm runtime. Nếu chưa đạt, giữ technical/candidate hoặc đánh dấu fail và áp dụng điểm dừng G0; không gắn `business` chỉ vì có file EvaluationRecord.
8. Bàn giao cho SPEC-006 bằng IDs/hash/versions và báo cáo, chạy integration lại từ snapshot đến PDF. Việc pack đạt test riêng chưa đóng toàn bộ G2.

## Test và bằng chứng phải có khi triển khai

| File test dự kiến / nơi chạy | Ca kiểm và kết quả cần chứng minh |
| --- | --- |
| `tests/training/test_dataset_split.py` trong checkout training được ghi nhận | Scene/geometry/time group rò giữa split bị phát hiện; ignore/class mapping, nhãn sai ngày/nguồn và duplicated chips được xử lý trước train |
| `tests/training/test_recipe_profile.py` trong checkout training | Thiếu band/QA/TL metadata, scale hai lần, std sai đơn vị, class/ignore khác train-infer bị chặn; seed/config/code hashes được ghi |
| `tests/training/test_checkpoint_selection.py` trong checkout training | Selection chỉ đọc train/validation; provenance trỏ đúng checkpoint, không lấy last epoch ngầm hoặc thay weights sau evaluation |
| `tests/models/test_business_pack.py` trong runtime repo | Hash/license/evaluation/profile thiếu hoặc không khớp bị từ chối; random decoder/reconstruction không bật feature business; conversion pack load đúng architecture |
| Evaluation/benchmark CLI thực trong checkout tương ứng | Lệnh, environment, input/model hashes, per-class metrics, tolerance, RAM/time/coverage, kết quả pass/fail theo gate được xác nhận |

Chưa có các test/CLI này; tên file là deliverable, không phải lệnh đã chạy. Lưu báo cáo đã lọc tại `Artchitect/docs/evidence/g2/` cùng reference kho artifact có quyền; không đưa weights/dữ liệu khách hàng/credential vào Git hoặc log. Không cam kết bit-identical giữa runtime/phần cứng; ghi mức reproducibility và sai số đo được.
