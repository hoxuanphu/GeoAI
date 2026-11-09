# G0 — Ghi nhận yêu cầu và quyết định từng phần

**Ngày:** 08/11/2026 · **Nguồn xác nhận:** câu trả lời trực tiếp của người dùng trong phiên làm việc GeoAI. **Task:** [SPEC-002](../../specs/002-g0-evidence.md). **Trạng thái:** đã xác nhận mục tiêu, thứ tự triển khai, chính sách nguồn ảnh, bốn chỉ số đầu, cách tạo AOI và bộ bảy lớp; G0 chưa đạt.

Hồ sơ này là bằng chứng về yêu cầu người dùng, chưa phải bằng chứng truy cập ảnh, kiểm định model, benchmark phần cứng hoặc duyệt đầy đủ G0. Chưa có người/đơn vị thực hiện và người duyệt từng đầu ra được phân công.

## Phát biểu gốc

1. Phạm vi mong muốn: “Lớp phú HLS 30m 10m 5m 1m, thống kê, PDF, giám sát rừng/mất rừng, các chỉ số đất nông nghiệp, cây trồng, đất ngập nước, vùng ngập nước”. Diễn giải “lớp phú” là lớp phủ; phân biệt sản phẩm HLS 30 m với các nguồn/profile độ phân giải khác ở dưới.
2. AOI và thời gian/mùa phân tích: “chưa rõ”.
3. Nguồn ảnh và cấu hình: “tôi muôn là dữ liệu ảnh từ tất cả các nguồn ảnh vệ tinh trên thế giới, cấu hình máy dự kiến chưa có, nhưng sẽ ít nhất 20GB ram, 8GB vram”. Câu trả lời chưa xác định inventory ảnh/nhãn hiện có hoặc quyền sử dụng từng nguồn.
4. Xác nhận thứ tự triển khai: “Chia đợt: HLS 30 m + lớp phủ/chỉ số/thống kê/PDF trước; sau đó rừng/mất rừng, đất ngập nước/ngập lụt và profile 10/5/1 m”.
5. Xác nhận chính sách nguồn ảnh: “Nguồn mở/miễn phí trước; ảnh thương mại tích hợp sau khi có quyền và ngân sách”.
6. Xác nhận chỉ số đợt đầu: “Bắt đầu NDVI, EVI, NDMI, MNDWI; chỉ tiêu định lượng chuyên sâu bổ sung sau”.
7. Phát biểu AOI: “AOI do người dùng vẽ trên bản đồ hoặc dựa vào ảnh vệ tinh được import vào, linh hoạt có thể là shapefile import vào”. Diễn giải thao tác dựa vào ảnh là lấy footprint có georeference và cho người dùng xác nhận; geometry/CRS/hash được giữ trong snapshot theo thiết kế hiện có.
8. Người dùng cung cấp bảng bảy lớp IDs 0–6 và `-1` ignore, tiêu chí vật lý, dấu hiệu phổ/đa thời gian và crosswalk ESA WorldCover/JAXA; bảng nêu “T=3 mốc” cho cây trồng. Chi tiết ở [bộ lớp](../../landcover-taxonomy.md). T=1 là profile spike kỹ thuật trong baseline hiện có, không phải phát biểu mới trong bảng này.
9. Người dùng cung cấp nội dung kỹ thuật để cụ thể hóa nhóm 3 (nguồn ảnh) và nhóm 4 (nhãn/kiểm định) SPEC-002: cặp ảnh X–nhãn Y, sáu band/QA/metadata, ba loại nguồn nhãn và bốn kiểm soát thời gian/lưới/ignore/split không gian. Phần tiếp nhận cùng hiệu chỉnh kỹ thuật ở [SPEC-002](../../specs/002-g0-evidence.md#nhóm-3--nguồn-ảnh-và-đóng-gói-input-x) và [báo cáo đối chiếu](../2026-11-08-input-label-review.md); các tỷ lệ chất lượng, số chip và link nguồn trong nội dung chưa là kết quả dự án đã được xác minh.
10. Người dùng cung cấp bộ Minimum Acceptance Criteria theo lớp, coverage, diện tích/CI/VN-2000, cấu hình/SLA GPU và ngân sách/điểm dừng. Các giá trị được giữ tại [tiêu chí nghiệm thu](../../acceptance-criteria.md); [đối chiếu kỹ thuật](../2026-11-08-acceptance-review.md) phân biệt giá trị yêu cầu với protocol còn mở và các phương án đổi profile chưa duyệt.
11. Sau câu hỏi về phạm vi máy mới, người dùng trả lời: “Máy training/benchmark GPU riêng; giữ mục tiêu desktop trước đó”. Cấu hình GPU 16–24 GB VRAM/RAM 32 GB/SSD 500 GB dùng cho môi trường riêng này; giữ G0-D04 cho desktop ít nhất 20 GB RAM/8 GB VRAM, không suy đã có máy thực hoặc benchmark.

## Quyết định đã xác nhận và giới hạn

| Mã | Nội dung đã xác nhận | Giới hạn / việc cần tiếp tục |
| --- | --- | --- |
| G0-D01 | Mục tiêu sản phẩm gồm lớp phủ đa độ phân giải, thống kê/PDF, rừng/mất rừng, chỉ số nông nghiệp–cây trồng, đất ngập nước và vùng ngập | Bộ bảy lớp đợt đầu đã cung cấp tại G0-D07; còn quy tắc biên lớp/QC, định nghĩa giám sát rừng/mất rừng/ngập, chỉ tiêu chuyên sâu, tần suất và chất lượng |
| G0-D02 | Đợt đầu: HLS 30 m + lớp phủ/chỉ số/thống kê/PDF. Các nghiệp vụ còn lại và profile 10/5/1 m triển khai sau | Chưa có lịch, ngân sách hoặc thứ tự giữa các hạng mục đợt sau; cần spec/gate riêng theo profile. Giữ Prithvi + decoder nghiệp vụ bắt buộc theo ADR-008 |
| G0-D03 | Ưu tiên nguồn mở/miễn phí; ảnh thương mại bổ sung khi có quyền và ngân sách | Mục tiêu hỗ trợ nguồn ảnh toàn cầu qua adapter, không cam kết đã tích hợp hoặc có quyền với mọi nguồn. Miễn phí không tự đồng nghĩa được phân phối lại; kiểm license, quota và quyền asset theo nguồn |
| G0-D04 | Mục tiêu máy dự kiến: ít nhất 20 GB RAM và 8 GB VRAM | Chưa có máy tham chiếu, CPU/GPU/hãng/driver/OS/SSD hoặc dung lượng khả dụng; chưa là cấu hình tối thiểu đã kiểm chứng, không chứng minh inference/training đáp ứng |
| G0-D05 | Đợt đầu có NDVI, EVI, NDMI, MNDWI; chỉ tiêu định lượng chuyên sâu bổ sung sau | Chỉ số phổ không trực tiếp là dinh dưỡng đất, độ ẩm đất, LAI, năng suất hoặc bản đồ ngập theo sự kiện. Công thức/mapping/QA/tolerance và thống kê cần kiểm theo GEO-01; chưa chọn ngưỡng phân loại từ chỉ số |
| G0-D06 | AOI có thể vẽ trên bản đồ, lấy từ ảnh/footprint import hoặc import Shapefile | Cần kiểm CRS/geometry/topology/hash, hỗ trợ bộ file Shapefile và không được tự thu AOI theo vùng valid mask |
| G0-D07 | Bộ lớp nghiệp vụ 7 lớp IDs 0–6; `-1` là ignore/mask, không phải lớp. Model nghiệp vụ dùng T=3; spike kỹ thuật giữ T=1 | Crosswalk mở chỉ là weak labels; cần QC/nhãn độc lập, version/hash/license, quy tắc biên lớp và kiểm profile T=3. Giá trị ngưỡng mới được ghi ở G0-D09; protocol/evaluation thực còn thiếu |
| G0-D08 | Tiếp nhận yêu cầu giao nhận X–Y, phân vai nguồn nhãn và kiểm thời gian/lưới/ignore/split trước chipping; weak labels dùng warm-up train hoặc gợi ý sửa, test nghiệm thu cần tham chiếu độc lập có QC | Chưa chọn provider/nguồn nhãn/quyền thực, target period/lịch frame, split/buffer, số mẫu/người duyệt. Hiệu chỉnh dtype, năm nhuận, grid đích và xử lý loss theo SPEC-002; không dùng các tỷ lệ nhãn/chip minh họa làm gate, bộ giá trị yêu cầu mới ở G0-D09 còn khóa protocol |
| G0-D09 | Ghi nhận bộ giá trị tiêu chí nghiệm thu người dùng cung cấp: per-class/global, coverage, diện tích/CI/CRS, tài nguyên và điểm dừng theo tài liệu riêng | Chưa khóa metric/sampling/CI/coverage protocol, ngưỡng diện tích còn dạng khoảng/thiếu lớp, máy thực, CPU SLO, campaign/lịch/chi phí và owner; không có kết quả đạt hoặc bằng chứng các ngưỡng là chuẩn chung |
| G0-D10 | Máy GPU 16–24 GB VRAM/RAM 32 GB/SSD 500 GB dùng riêng cho training/benchmark; giữ mục tiêu desktop trước đó ít nhất 20 GB RAM/8 GB VRAM | Đã xác nhận phạm vi; còn cấu hình GPU/CPU/OS/driver/đĩa thực, dung lượng khả dụng, workload và SLO từng môi trường. Không thay yêu cầu CPU hoặc công bố support matrix từ cấu hình dự kiến |

## AOI, bộ lớp và profile thời gian

Chi tiết cách tạo, kiểm và cố định AOI ở [AOI policy](../../aoi-policy.md); bộ lớp/crosswalk ở [landcover taxonomy](../../landcover-taxonomy.md). Tài liệu taxonomy giữ tiêu chí nghiệp vụ người dùng cung cấp; việc quy thuộc tiêu chí cho từng nguồn mở, khả năng suy ra từ HLS và crosswalk còn cần kiểm chứng/QC. Nhãn mở là weak labels. Profile nghiệp vụ là `B × 6 × 3 × 224 × 224`; T=1 chỉ dùng spike kỹ thuật. Ba frame phải là ba quan sát thật trên cùng GridSpec, không lặp ảnh.

## Độ phân giải và tương thích model

| Mức mong muốn | Hướng xử lý | Điều phải kiểm chứng |
| --- | --- | --- |
| 30 m | HLS S30 v2 là profile khởi đầu; L30 chỉ thêm sau kiểm mapping/QA | Sáu band, QA, scale/offset, metadata, nhãn địa phương, decoder và coverage thực theo profile Prithvi |
| 10 m | Nguồn/profile riêng, ví dụ Sentinel-2 L2A nếu phù hợp; chưa chốt provider | Sentinel-2 có band 10 m và 20 m; B8A/B11/B12 không phải band gốc 10 m. Đưa về lưới 10 m không làm mọi band có chi tiết gốc 10 m; cần fine-tune/evaluation riêng |
| 5 m và 1 m | Nguồn/sản phẩm phù hợp và có quyền; chưa chọn ảnh, license hoặc checkpoint | GSD gốc, độ chính xác vị trí, band, QA, nhãn và model phù hợp. Không mặc định có SWIR hoặc tương thích profile HLS; RGB không được lặp kênh để giả sáu band |

Resample HLS 30 m thành pixel 10/5/1 m chỉ đổi lưới, không tạo quan sát chi tiết tương ứng. Nếu nghiên cứu siêu phân giải thì phải định nghĩa kết quả ước lượng và kiểm định riêng. Ghi riêng GSD nguồn, GridSpec đầu ra và miền hiệu lực model; không quảng bá độ phân giải quan trắc theo pixel đã nội suy.

Prithvi bắt buộc cho nhánh dữ liệu phù hợp ngay bản đầu, không có nghĩa một checkpoint HLS xử lý mọi cảm biến. Mỗi nhánh mở rộng cần product/preprocessing/model profile, nhãn/split/evaluation và ngân sách riêng trước công bố hỗ trợ. Đất ngập nước, nước thường xuyên, vùng ngập theo sự kiện và mất rừng theo thời gian cần định nghĩa/tập kiểm định riêng; không suy tất cả từ một bản đồ lớp phủ một ngày.

RAM/VRAM dự kiến chưa đủ để chốt tốc độ, kích thước AOI hoặc khả năng fine-tune 300M + UPerNet. Phải đo inference theo cửa sổ và tổng job riêng; training vẫn ở môi trường ngoài desktop theo thiết kế hiện tại. CPU chính thức/NVIDIA tùy chọn vẫn là đề xuất có điều kiện kiểm chứng, không suy hãng GPU chỉ từ 8 GB VRAM.

## Những gì ba tài liệu tham khảo trả lời được

Đã đọc [cẩm nang](../../../solution/cam_nang_kien_truc_ung_dung_geoai_vien_tham.md), [bản cẩm nang Claude](../../../solution/cam_nang_kien_truc_ung_dung_geoai_vien_tham_claude.md) và [hướng dẫn xây dựng](<../../../solution/Hướng dẫn xây dựng ứng dụng GeoAI cho viễn thám.md>). Hai cẩm nang có nội dung byte-identical tại lần kiểm, SHA-256 `714877edb6e364a9ea33ab9334860aac3e131fc2d1ce7acce0bb1c7012f1e775`; không coi là hai nguồn xác nhận độc lập.

| Câu hỏi G0 | Thông tin có trong tài liệu | Kết luận áp dụng |
| --- | --- | --- |
| Chọn nghiệp vụ/nguồn | Danh mục lĩnh vực, cảm biến, HLS 30 m và dataset tham khảo; hướng dẫn mục 3.2 vẫn là bảng câu hỏi/ví dụ | Dùng làm lựa chọn; phạm vi và thứ tự ở hồ sơ này được xác nhận bởi người dùng |
| Nhãn và đánh giá | Gán nhãn địa phương, QC, split không gian/thời gian, per-class F1/IoU và test vùng/năm độc lập | Kế thừa phương pháp trong SPEC-008; chưa có nhãn, split hoặc kết quả kiểm định thực |
| AOI/mùa, quyền ảnh, máy, ngưỡng và ngân sách | Không xác định đầu vào dự án cụ thể; có cấu hình và ngưỡng minh họa | Không lấy F1 ≥ 0,85, sai số diện tích ≤ 10%, 100–500 patch hay GPU server 24–48 GB làm yêu cầu đã duyệt |
| Baseline và model | Có khuyến nghị chung về model/baseline | Giữ yêu cầu Prithvi và gate tuyệt đối theo ADR-008; không áp câu “deep learning phải thắng baseline” của cẩm nang |

Các chỉ dẫn trong tài liệu tham khảo được đánh giá như nội dung nguồn. Chúng không tự thay yêu cầu trực tiếp của người dùng hoặc các quyết định đã xác nhận của GeoAI. Chưa xác minh live quyền truy cập/license/benchmark của từng provider trong đợt này.

## Đầu vào còn thiếu để đóng G0

- AOI cụ thể và geometry/CRS, thời gian/mùa; chưa được phép chọn thay người dùng. Có thể đề xuất vùng thí điểm để người dùng chọn ở bước sau.
- QC/crosswalk/nhãn độc lập của bộ 7 lớp, policy T=3 và định nghĩa nghiệm thu theo lớp; bộ bốn chỉ số đã chốt nhưng QA/tolerance, tổng hợp theo vùng/thời gian và ngưỡng diễn giải vẫn cần đặc tả/kiểm. Các chỉ tiêu đất, dinh dưỡng, độ ẩm định lượng hoặc năng suất bổ sung sau có thể cần dữ liệu thực địa/khí tượng và model riêng.
- Provider/collection/version đầu tiên, tài khoản/quyền và kiểm đọc đủ band/QA; inventory ảnh/nhãn hiện có còn chưa xác định. Chưa tạo dataset manifest hoặc bằng chứng coverage 2–3 năm.
- Nguồn nhãn/license, người duyệt, kế hoạch split/kiểm định độc lập và phân công đầu ra SPEC-008.
- CRS/VN-2000 cụ thể, operation/điểm chuẩn và protocol tolerance. Các giá trị ngưỡng theo lớp/coverage/diện tích/tài nguyên đã được cung cấp tại G0-D09; phạm vi máy đã xác nhận tại G0-D10. Còn protocol/chọn giá trị trong khoảng, máy thực, CPU workload/SLO và budget/campaign thực trước đóng G0.

Các mốc 002.1–002.3 vẫn chưa hoàn tất. Chỉ cập nhật phần quyết định đã có; không tạo manifest, coverage, nhãn hoặc benchmark giả để lấp các đầu vào còn thiếu.

## Kiểm tra hồ sơ

Đối chiếu phát biểu gốc và lựa chọn trực tiếp ở trên với phần diễn giải; kiểm cấu trúc/liên kết và đồng bộ nguồn/plans/roadmap/tracker trong [báo cáo đợt ghi nhận](../2026-11-08-g0-intake-review.md). Kết quả chỉ xác minh tài liệu và phạm vi thay đổi, không đóng G0 hay gate runtime/model.

Bổ sung AOI/bộ lớp và đồng bộ trạng thái theo [báo cáo AOI/taxonomy](../2026-11-08-aoi-taxonomy-review.md); báo cáo đợt ghi nhận trước được giữ làm lịch sử.
