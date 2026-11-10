# Tiêu chí nghiệm thu lớp phủ HLS 30 m

**Ngày:** 08/11/2026. **Nguồn:** bộ Minimum Acceptance Criteria người dùng cung cấp; [hồ sơ tiếp nhận](../evidence/g0/decision-record.md), [đối chiếu kỹ thuật](../evidence/2026-11-08-acceptance-review.md). **Trạng thái:** đã ghi nhận các giá trị yêu cầu và xác nhận máy GPU dùng riêng cho training/benchmark; protocol, máy cụ thể và các lựa chọn còn mở chưa khóa, chưa có kết quả nghiệm thu. Không coi các ngưỡng này là chuẩn quốc tế hoặc bảo đảm chất lượng từ công bố Prithvi/JAXA.

Tài liệu cụ thể hóa [SPEC-002](../specs/002-g0-evidence.md), được dùng cho [SPEC-008](../specs/008-training-evaluation-model-pack.md) và [SPEC-006](../specs/006-landcover-workflow.md) sau khi khóa protocol phù hợp. G0 chốt đầu vào/ngưỡng/ngân sách; G1 kiểm kỹ thuật; G2 kiểm checkpoint nghiệp vụ. Ghi ngưỡng không làm bất kỳ gate nào đạt.

## Chất lượng phân loại

Giữ nguyên giá trị người dùng cung cấp; tất cả ngưỡng trong cùng hàng và giữa các hàng áp dụng **đồng thời**. PA là recall, UA là precision. Bảy lớp theo [taxonomy](landcover-taxonomy.md); -1 là ignore, không là lớp thứ tám.

| ID / lớp | F1 tối thiểu | IoU tối thiểu | PA tối thiểu | UA tối thiểu |
| --- | --- | --- | --- | --- |
| 0 / Mặt nước | 0,88 | 0,80 | 0,85 | 0,85 |
| 1 / Cây thân gỗ / Rừng | 0,85 | 0,75 | 0,85 | 0,85 |
| 2 / Đất canh tác hàng năm | 0,82 | 0,70 | 0,80 | 0,80 |
| 3 / Cây bụi & Trảng cỏ | 0,72 | 0,56 | 0,70 | 0,70 |
| 4 / Thực vật ngập nước / Rừng ngập mặn | 0,80 | 0,68 | 0,78 | 0,78 |
| 5 / Đất xây dựng / Mặt không thấm | 0,78 | 0,65 | 0,75 | 0,75 |
| 6 / Đất trống / Bãi bồi | 0,72 | 0,56 | 0,70 | 0,70 |
| Toàn cục | Macro F1 ≥ 0,80 | mIoU ≥ 0,68 | OA ≥ 0,85 | OA không thay ngưỡng theo lớp |

Với cùng confusion matrix và cách trọng số, `F1 = 2 × IoU / (1 + IoU)` cho từng lớp; hai cột không phải hai bằng chứng độc lập. Ví dụ IoU nước ≥0,80 kéo theo F1 ≥0,888889, chặt hơn riêng F1 ≥0,88. Không làm tròn số đo trước so ngưỡng. Macro F1/mIoU là trung bình không trọng số của bảy metric lớp; không loại lớp khó/thiếu mẫu khỏi mẫu số để pass. OA tính từ confusion matrix có protocol rõ, không lấy trung bình PA/UA thay OA.

Trước đánh giá phải khóa test độc lập, vùng/mùa/kỳ nhãn, sampling design, trọng số, mức support theo lớp và cách xử lý mẫu không chắc chắn theo [SPEC-002](../specs/002-g0-evidence.md#nhóm-4--nhãn-y-nguồn-tham-chiếu-và-split). Nếu lấy mẫu phân tầng không tỷ lệ, dùng trọng số theo thiết kế để ước lượng độ chính xác trên miền; báo sample metrics riêng, không gọi OA thô trên tập mẫu thiên lệch là OA toàn AOI. Báo số mẫu, ignore/abstention, confusion matrix và uncertainty phù hợp tương quan không gian; không chỉ báo một điểm số.

Chưa chốt support/cỡ mẫu, cách dùng point estimate hay cận tin cậy cho quyết định pass và ngưỡng theo vùng/mùa ngoài miền thí điểm. Lớp thiếu mẫu hoặc metric không xác định là **chưa đủ bằng chứng**, không mặc định 0 hay 1 để pass. Kết quả chỉ trên vùng quan sát hợp lệ phải công bố coverage; không suy chất lượng cho vùng bị mây hoặc chưa có nhãn. Bản đồ lớp 1 không tự là kiểm kê rừng pháp lý; lớp 4 gộp wetland/mangrove không tự chứng minh chất lượng riêng từng phân lớp.

## Coverage và số quan sát

Mẫu số là diện tích AOI đã xác nhận, theo phương pháp cắt biên/diện tích tại [domain rules](../domain-rules.md), giữ nguyên kể cả vùng ngoài footprint/không có dữ liệu. Policy Fmask/band validity, khoảng thời gian và mùa địa phương có version/hash trước đo. Phân biệt mask ảnh, mask nhãn và mask đầu ra.

| Chỉ tiêu người dùng cung cấp | Giá trị ghi nhận | Điều kiện sử dụng |
| --- | --- | --- |
| Ảnh đơn ngày | Mây + bóng mây ≤10% diện tích AOI | Là điều kiện cần, chưa bảo đảm valid coverage ≥90% nếu còn vùng ngoài footprint/fill/snow/band invalid. Không dùng % mây toàn scene thay AOI; frame một ngày không cho phép hạ model nghiệp vụ từ T=3 xuống T=1 |
| Composite mùa khô | Valid coverage ≥97%, thiếu quan sát ≤3% | Đo sau recipe/QA trên toàn AOI và báo mỗi frame lẫn input/output cuối; tên mùa và lịch vùng phải được khóa |
| Composite mùa mưa | Valid coverage ≥90%, thiếu quan sát ≤10% | Không bỏ qua tiêu chí vì vùng núi/mây nhiều; giữ -1 khi thiếu và báo fail/chưa đủ dữ liệu nếu không đạt |
| Chuỗi tháng | Ít nhất 2 quan sát sạch/pixel/tháng | Nhánh yêu cầu chuỗi năm: phải chỉ rõ các tháng bắt buộc và diện tích đáp ứng trên toàn AOI; không chỉ đếm trên tập pixel đã lọc cho đủ điều kiện |
| Ba mốc T=3 | Ít nhất 1 quan sát sạch ở mỗi frame cho pixel được suy luận hợp lệ | Nhánh ba mốc không tự chứng minh đạt yêu cầu 2 quan sát/tháng. Lựa chọn nhánh được khóa trước khảo sát/đánh giá; không đổi sang điều kiện dễ hơn sau xem kết quả |

Coverage dùng cho input T=3 phải đo trên **giao mask hợp lệ của cả ba frame** theo policy đã khóa; coverage union theo mùa/năm hoặc trung bình coverage ba frame không thay được chỉ tiêu này. Với composite phải có số quan sát thực/ngày nguồn theo pixel phù hợp recipe; median theo band có thể dùng nguồn khác nhau, phải kiểm ngữ nghĩa phổ/thời gian đối với model/TL. Chưa chốt ngưỡng giao-mask T=3 riêng với các ngưỡng theo mùa; phải ghi phạm vi áp dụng chính xác trước nghiệm thu.

Median 60–90 ngày và ghép S30+L30 là **recipe ứng viên người dùng nêu**, chưa được mặc định thay profile S30. Chốt độ dài cửa sổ cụ thể, mùa, nguồn/license, harmonization/band/QA, normalization và TL date policy; fine-tune/evaluation theo cùng recipe trước dùng nghiệp vụ. S30, L30 và tổ hợp báo riêng; không dùng revisit danh nghĩa hoặc tỷ lệ mây trong bài báo để hứa coverage địa phương.

Nội suy/lấp mây nếu nghiên cứu phải có mask/provenance/kiểm định riêng. Pixel được dự đoán/lấp từ model không được tính thêm thành quan sát sạch thật, không được dùng để nâng valid-observation coverage hoặc nhãn test. Chưa duyệt một profile imputation trong bản đầu.

## Diện tích và độ chính xác địa lý

Phân biệt diện tích bản đồ, ước lượng điều chỉnh sai số và số liệu tham chiếu. Không lấy số pixel của một test set lấy mẫu nhân 900 m² làm diện tích thật toàn tỉnh; ô biên AOI, biến dạng phép chiếu và phần không quan sát được xử lý theo domain rules.

| Chỉ tiêu người dùng cung cấp | Giá trị ghi nhận | Điều cần khóa trong protocol |
| --- | --- | --- |
| Chênh lệch diện tích bản đồ với tham chiếu, lớp 0/1/2 | Trị tuyệt đối sai lệch tương đối ≤8% | Định nghĩa `100 × abs(A_map − A_ref) / A_ref` với A_ref >0, cùng AOI/kỳ/ontology và miền quan sát; báo cả sai lệch có dấu. A_ref có nguồn/phương pháp/uncertainty, không tự lấy số liệu rừng hành chính làm tham chiếu tree cover |
| Biên CI 95% diện tích hiệu chỉnh, lớp 0/1/2 | ±5% | Diễn giải đề xuất là half-width CI chia cho diện tích ước lượng của lớp, không phải 5 điểm % AOI; cần người duyệt khóa mẫu số và cách dựng CI |
| Biên CI 95% cho nhóm xây dựng/đất trống/rừng ngập mặn | ±10–15% | Cần chọn một ngưỡng cụ thể cho từng lớp/nhóm trước đo. Lớp 4 gồm cả wetland; phải chỉ rõ áp cho cả lớp 4 hay riêng mangrove có nhãn đánh giá bổ sung |
| Cây bụi/trảng cỏ (lớp 3) | Chưa có ngưỡng diện tích trong nội dung cung cấp | Không tự gán ngưỡng 10% hay 15%; còn chờ xác nhận |
| RMSE ngang chuyển sang VN-2000 | ≤15 m | `sqrt(mean(dx² + dy²))` trên điểm kiểm độc lập, phân bố phù hợp, có độ chính xác nguồn; khóa CRS/operation/grid/miền dùng và protocol điểm kiểm |
| Chênh lệch diện tích AOI sau reprojection | ≤0,1% | Đo cùng ranh vật lý bằng cùng phương pháp diện tích ellipsoid/CRS phù hợp và mẫu số diện tích tham chiếu dương; không so diện tích phẳng hai phép chiếu khác biến dạng rồi quy mọi chênh lệch thành lỗi chuyển hệ |

Chênh lệch bản đồ so tham chiếu là một số đo trên miền cụ thể; chưa phải ước lượng bias thống kê nếu thiếu thiết kế suy luận thích hợp. CI hẹp không tự chứng minh estimator không lệch hoặc đạt sai số so chân lý. Ngưỡng ≤8% và CI 95% là hai tiêu chí khác nhau, phải báo riêng.

Ước lượng diện tích theo lấy mẫu phân tầng cần probability sample và trọng số. Trong trường hợp mẫu ngẫu nhiên đơn trong từng tầng bản đồ i, với toàn miền đã được phân tầng và lấy mẫu, có thể dùng `A_hat_j = A_domain × sum_i(W_i × n_ij / n_i)`; W_i là tỷ trọng diện tích tầng i. Variance/CI phải theo thiết kế lấy mẫu thực, có xử lý cụm/tương quan và finite population khi phù hợp; không áp máy móc công thức này cho các chip thuận tiện. Nếu có tầng NoData phải lấy mẫu tham chiếu phù hợp hoặc giới hạn suy luận và báo vùng chưa ước lượng; không ngoại suy tự động ra toàn AOI.

CI tương đối khi diện tích ước lượng bằng 0/rất nhỏ cần quy tắc riêng và thiết kế mẫu đủ lớp hiếm; không chia cho 0 hoặc báo đạt nhờ thiếu mẫu. Chưa khóa cỡ mẫu/phân tầng, tiêu chí precision cho lớp 3/4 và các khoảng 10–15%, nên phần diện tích chưa đủ để nghiệm thu tự động.

Mức 15 m là tolerance dự án được cung cấp, không bảo đảm pháp lý từ một bộ 7 tham số. Cần đối chiếu nguồn tham số/quyết định có hiệu lực, thứ tự/trục/đơn vị/convention phép chuyển, area of use và điểm chuẩn; không hard-code một phép VN-2000 chung hoặc fallback ballpark. Kiểm chuyển datum và đồng đăng ký ảnh/nhãn là hai kiểm khác nhau; nửa pixel HLS không tự chứng minh sai số chuyển hệ.

## Tài nguyên, thời gian và điểm dừng

| Hạng mục người dùng cung cấp | Giá trị ghi nhận | Phạm vi và việc còn mở |
| --- | --- | --- |
| Máy GPU tham chiếu | 1 GPU 16–24 GB VRAM, RAM 32 GB, SSD 500 GB | Người dùng xác nhận dùng riêng cho training/benchmark; giữ mục tiêu desktop ít nhất 20 GB RAM/8 GB VRAM. Chưa chọn GPU/CPU/driver/OS/SSD cụ thể hoặc dung lượng khả dụng; chưa phải máy thực/support matrix đã kiểm |
| VRAM inference | Peak ≤85% dung lượng GPU | Khóa phương pháp đo NVML/process/device, allocated/reserved, tải UI/OS và cold/warm; không suy chạy được từ VRAM danh nghĩa hoặc gộp nhiều GPU |
| SLA GPU | ≤15 phút/tile 3660 × 3660, 6 band, T=3, một GPU | Tile 30 m này có footprint phẳng danh nghĩa khoảng 12.056 km²; phải khóa asset/grid/coverage, model/runtime/precision, window/overlap và ranh giới thời gian đo. Đo inference và tổng job/I/O/preprocess/postprocess/report riêng, không suy SLA CPU |
| Training cap | ≤4 GPU-giờ/lần fine-tune | Đo GPU-hours thực theo tài nguyên cấp phát và log; khóa có tính setup/validation/checkpoint hay không. Không suy tương đương 50–100 epoch, 500–1.000 chip hoặc model cụ thể |
| Early stopping | min_delta = 0,005 mIoU, patience = 15 epoch | 0,005 là 0,5 điểm phần trăm tuyệt đối; theo validation cùng protocol, không test. Recipe khóa cách cập nhật best, cadence, checkpoint/stop reason; dừng khi chạm cap kể cả chưa đủ patience |
| Campaign thử nghiệm | 3–5 vòng, tối đa 2 tuần làm việc hoặc trần chi phí thuê GPU đã duyệt | Cần chọn số vòng cụ thể trong khoảng trước chạy, định nghĩa một vòng/tính retry và ngày bắt đầu/kết thúc, trần tiền cụ thể. Không vượt giới hạn nào đã khóa; chưa có lịch/chi phí cam kết từ bảng này |

T4/V100/L4/RTX 3090/4090 là các ví dụ, không phải các máy có hiệu năng hoán đổi được. CPU vẫn là cấu hình phát hành trong thiết kế hiện tại và cần SLA/RAM/workload riêng; một SLA GPU không chứng minh đạt CPU. Người dùng đã trả lời: “Máy training/benchmark GPU riêng; giữ mục tiêu desktop trước đó”. Phạm vi máy đã rõ, còn cấu hình thực và SLO từng môi trường cần khóa.

G0 chốt ngân sách/điểm dừng; không coi yêu cầu “vòng thử ở G0” là cho phép tự chạy fine-tune khi thiếu dependency G0 của SPEC-008. Hiện chỉ làm tài liệu.

Không bắt buộc chuyển cửa sổ 224 sang 512, FP16 hoặc Prithvi-EO-1.0 để chữa SLA. Ưu tiên profiling và ứng viên Prithvi-EO-2.0 đã được thiết kế cho phép; thay shape/precision/checkpoint/decoder phải kiểm lại output tolerance, metrics, coverage và benchmark. FP16 chỉ dùng trên backend đã kiểm. Không thêm DEM thành kênh thứ bảy vào checkpoint sáu band; nhánh DEM phụ trợ là thiết kế/model/evaluation riêng cần quyết định trước làm.

Khi không đạt hoặc hết ngân sách đã khóa: dừng, giữ checkpoint/log/metrics fail, lập trade-off report với confusion matrix theo lớp, coverage, mẫu lỗi, tài nguyên và chi phí; trình chủ dự án quyết định. Gộp lớp cần ontology/DatasetVersion/model/evaluation mới; bổ sung 200–300 mẫu là phương án người dùng nêu, chưa phải số mẫu đã cấp ngân sách; thay nhánh DEM/profile/model phải theo ADR nếu thay quyết định đã chấp thuận. Không hạ gate hồi tố, thay test, chọn bỏ lớp khó hoặc coi test thành validation để báo đạt.

## Hồ sơ phải khóa trước đo nghiệm thu

Ghi gate/version/người duyệt và thời điểm trước tối ưu/evaluation; khóa AOI/kỳ/mùa, test/sampling/support/metric/CI protocol, grid/transform, QA/composite/T=3 coverage policy, phạm vi ngưỡng diện tích còn mở; máy/runtime/precision/workload/clock boundaries, CPU SLO, training/campaign budget và stop accounting. Cùng IDs/hash dataset/model/profile/checkpoint và lệnh đo phải đi vào báo cáo.

Mỗi tiêu chí kết luận riêng **đạt / không đạt / chưa đủ bằng chứng**; chỉ kết luận gate khi đủ cả chất lượng, coverage, diện tích/CRS, tài nguyên và dependency tương ứng. Không dùng macro/OA hay kết quả một GPU thay các phần còn thiếu. Chưa triển khai schema/gate evaluator/test runtime trong đợt này.
