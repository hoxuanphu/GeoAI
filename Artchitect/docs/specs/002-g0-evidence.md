# SPEC-002 — Bằng chứng và quyết định G0

**Trạng thái:** đã ghi nhận một phần yêu cầu và quyết định; chờ dữ liệu/quyết định còn thiếu, G0 chưa đạt. **Mục tiêu:** đóng G0 bằng đầu vào thực và quyết định có người chịu trách nhiệm, không tự bịa ngưỡng để unblock phát hành.

## Quyết định từng phần ngày 08/11/2026

[Decision record G0](../evidence/g0/decision-record.md) lưu phát biểu trực tiếp của người dùng và phần diễn giải. Đã chốt chia đợt: HLS 30 m + lớp phủ/chỉ số/thống kê/PDF trước; rừng/mất rừng, đất ngập nước/ngập lụt và profile 10/5/1 m sau. Bốn chỉ số đầu là NDVI/EVI/NDMI/MNDWI; chỉ tiêu định lượng chuyên sâu bổ sung sau. Nguồn mở/miễn phí trước, ảnh thương mại sau khi có quyền và ngân sách. Mục tiêu máy dự kiến ít nhất 20 GB RAM/8 GB VRAM, chưa là máy tham chiếu hoặc support matrix đã kiểm.

Cách tạo AOI đã được xác nhận: vẽ trên bản đồ, dựa vào footprint ảnh vệ tinh import hoặc import Shapefile theo [AOI policy](../domain/aoi-policy.md). Đã cung cấp [bộ bảy lớp](../domain/landcover-taxonomy.md) IDs 0–6, `ignore_index = -1` và dấu hiệu đa thời gian T=3; đây là quyết định về yêu cầu, chưa là nhãn/QC/model đã nghiệm thu.

Còn thiếu AOI kiểm định cụ thể/thời gian, QC/crosswalk/nhãn độc lập, policy chọn ba frame/QA/tolerance và thống kê chỉ số, dữ liệu/quyền từng nguồn, coverage thực, hardware/workload và người phụ trách. Người dùng đã cung cấp các giá trị ngưỡng chất lượng/coverage/diện tích/CRS/tài nguyên; protocol, các khoảng lựa chọn và ngân sách thực còn cần khóa theo [tiêu chí nghiệm thu](../domain/acceptance-criteria.md). HLS chỉ ở 30 m; 10/5/1 m cần nguồn/profile/model và kiểm định riêng. Không dùng resample để tuyên bố chi tiết quan trắc mới. Các mốc 002.1–002.3 chưa hoàn tất; [kiểm tài liệu AOI/bộ lớp](../evidence/2026-11-08-aoi-taxonomy-review.md) không thay kiểm dữ liệu hoặc duyệt G0.

## Input/output

Input: nhu cầu chủ nghiệp vụ, AOI/CRS, dữ liệu nhãn/ảnh, hardware có thể dùng và ngân sách. Output dự kiến trong `Artchitect/docs/evidence/g0/`: `decision-record.md`, `dataset-manifest.json`, `coverage-summary.csv`, `coverage-map` có georeference, `workload-profile.json`, `label-plan.md`. Chỉ tạo artifact bằng dữ liệu thật hoặc quyết định được xác nhận, không tạo file rỗng.

| Đầu vào cần chốt | Nội dung và chủ trì |
| --- | --- |
| Feature/class schema | Đã cung cấp bộ 7 lớp IDs 0–6 và `-1` ignore, cùng NDVI/EVI/NDMI/MNDWI trên HLS 30 m; còn QC/crosswalk cuối, policy chỉ số, mục đích và người duyệt |
| AOI/nguồn/quyền | Cách tạo đã chốt vẽ/footprint ảnh import/Shapefile; còn geometry/CRS/hash của AOI kiểm định, mùa/2–3 năm, provider/collection; GIS/data thử đọc sáu band/QA và xác thực |
| Coverage | Từng ngày, best day/số ngày đạt theo tháng, valid observations và union/composite riêng; policy Fmask/band validity/hash rõ |
| Nhãn/split | WorldCover/JAXA là nhãn tham khảo theo version; cần license/hash/QC, nhãn độc lập, người duyệt, khớp ngày, vùng/mùa/lớp hiếm và kế hoạch train/validation/test trước chipping |
| Địa lý | CRS/VN-2000/vertical datum cần hỗ trợ, operation/grid/điểm chuẩn và tolerance có nguồn |
| Ngân sách | CPU/GPU/OS/model cụ thể, RAM/đĩa khả dụng, workload/window/overlap và thời gian job tối đa |
| Gate/điểm dừng | Ngưỡng tuyệt đối theo lớp, coverage, số vòng và trần chi phí/thời gian, chủ dự án quyết định khi không đạt |
| Trách nhiệm giao nhận | Ghi người/đơn vị thực hiện và người duyệt cho dataset/nhãn/split, training/checkpoint, evaluation, pack và tích hợp theo SPEC-008; không cần sáu người riêng nhưng không để đầu ra thiếu chủ sở hữu |

## Nhóm 3 — Nguồn ảnh và đóng gói input X

Nội dung người dùng cung cấp ngày 08/11/2026 được cụ thể hóa dưới đây sau đối chiếu profile hiện có. Chốt quy tắc dữ liệu không đồng nghĩa đã chọn provider, có quyền đọc asset hoặc hoàn thành nhóm đầu vào G0. [Báo cáo đối chiếu X–Y](../evidence/2026-11-08-input-label-review.md) phân biệt phần tiếp nhận và các khẳng định chưa được kiểm chứng.

| Thành phần X | Quy tắc giao nhận |
| --- | --- |
| Sản phẩm/nguồn | HLS S30 v2 surface reflectance, 30 m. GIS/data ghi provider/collection/version, scene/asset IDs, acquisition dates, hash và quyền đọc; phải thử đọc thực sáu band và QA. Không coi link catalog là bằng chứng truy cập |
| Sáu band | B02, B03, B04, B8A, B11, B12 theo thứ tự Blue/Green/Red/Narrow NIR/SWIR1/SWIR2; không dùng RGB hoặc lặp kênh để thay thế |
| Scale/offset | Với DN HLS S30 v2 gốc, hệ số reflectance 0,0001 phải đối chiếu metadata sản phẩm/provider; adapter xác định dữ liệu đã được scale hay chưa. Nhận diện fill/NoData trước biến đổi, không scale hai lần; mean/std phải cùng đơn vị theo checkpoint |
| Tensor | Profile nghiệp vụ `B × 6 × 3 × 224 × 224`; ba frame thật theo thứ tự thời gian trên cùng GridSpec. T=1 chỉ là spike kỹ thuật; không mở tự do T=1–4 hoặc chip 512 chỉ từ nội dung tham khảo. Ảnh nguồn có thể được lưu tách band/frame rồi dựng tensor có provenance, không bắt buộc một GeoTIFF chứa toàn tensor |
| QA và masks | Fmask riêng cho từng frame, band-validity/footprint/AOI mask và policy version/hash. QA không là kênh phổ thứ bảy. Không dùng toàn byte Fmask khác 0 để mask; giữ nước hợp lệ. Fmask không bảo đảm phát hiện mọi mây mỏng/sương mù, cần QC và policy đúng phiên bản |
| TL metadata | Acquisition date của từng frame và tâm cửa sổ WGS84 từ metadata tin cậy; lưu ngày đầy đủ, kiểm năm nhuận/ngày thứ 366 khi hợp lệ. Encoding year/day-of-year và chỉ số ngày theo đúng code/model revision, không tự ép mọi năm về 1–365 hoặc đặt ngày giả cho composite |
| Không gian | CRS/affine/width/height, GridSpec/hash, TransformSpec và căn chỉnh ảnh/QA/nhãn phải khớp trên lưới phân tích. Nếu dùng raster tham chiếu thì giữ đúng reference grid; nếu qua nhiều tile/múi thì warp về grid đích đã chọn theo domain rules |

Policy chọn ngày/mùa của ba frame, composite, thiếu frame/fallback và valid observations tối thiểu vẫn cần khóa trước chạy thật. Không suy khả năng tương thích mọi Prithvi-EO-1.0/2.0 từ một bài báo hoặc từ việc tensor có cùng số chiều.

## Nhóm 4 — Nhãn Y, nguồn tham chiếu và split

Mỗi mẫu phân đoạn gồm chuỗi ảnh X, nhãn mục tiêu Y, masks và metadata/lineage liên kết bằng sample ID và asset/version/hash. Y là raster phân loại một band `(H, W)`; khi vào batch thành `(B, H, W)`, khớp grid và footprint của X. Y mô tả lớp phủ ở **ngày hoặc kỳ tham chiếu được định nghĩa**, không có nghĩa một nhãn 2D đồng thời đúng ở cả ba ngày nếu đối tượng đã biến động.

Giữ IDs 0–6 và `ignore_index = -1`. Đề xuất lưu signed Int16 như taxonomy; nếu dùng UInt8 thì dùng NoData 255 và mapping tường minh 255 ↔ -1 trước loss/metrics, kiểm round-trip. Không ghi -1 trực tiếp vào UInt8. Dtype raster là lựa chọn lưu trữ, dtype tensor target phải theo loss/backend; khóa lựa chọn thực trong DatasetVersion/profile khi triển khai.

| Nguồn nhãn | Vai trò được tiếp nhận | QC/bằng chứng bắt buộc |
| --- | --- | --- |
| Weak/proxy: WorldCover, JAXA; Dynamic World là nguồn ứng viên bổ sung | Dùng cho warm-up/pre-finetuning trên train hoặc làm gợi ý để con người sửa; không dùng nguyên bản làm test nghiệm thu hay nhãn validation để chọn model nghiệp vụ. Muốn dùng khác phạm vi này cần review/version lại policy | Ghi source/year/version/license/hash, crosswalk và QC; nguồn tự động không tự thành nhãn tham chiếu độc lập |
| Giải đoán ảnh | Có thể làm train tinh chỉnh, validation hoặc test tham chiếu độc lập nếu đáp ứng protocol | Ghi nguồn ảnh/ngày/quyền dùng, người giải đoán và người duyệt, ontology/kỳ tham chiếu, độ chắc chắn, lỗi vị trí và cách giải quyết bất đồng; người duyệt test cần dữ liệu tham chiếu độc lập với model/crosswalk sinh train |
| Thực địa/UAV/bản đồ chuyên ngành | Bổ sung/kiểm định lớp khó hoặc chuyên sâu theo phạm vi nguồn | Ghi ngày khảo sát, độ chính xác vị trí, nguồn/phương pháp/pháp lý và mapping sang lớp phủ vật lý; bản đồ thửa/hiện trạng sử dụng đất không tự đồng nghĩa nhãn lớp phủ của mọi pixel 30 m |

Với weak/proxy labels, phải ghi version/year/license/hash, crosswalk theo taxonomy, chênh lệch thời gian/biến động và policy đưa 10 m về grid 30 m. Không mặc định phủ kín AOI, miễn phí cho mọi mục đích hoặc có một mức độ chính xác chung. Dynamic World chưa được chọn provider, khóa crosswalk hoặc tích hợp. Ảnh nhìn được trên Google Earth/Bing/Planet không tự cấp quyền trích xuất, huấn luyện hoặc phân phối; nguồn ảnh giải đoán cụ thể còn chờ xác nhận. Không tự công bố nhãn giải đoán là ground truth không sai số hoặc độ chính xác >95%.

### Bốn kiểm soát bắt buộc trước khóa dataset

1. **Thời gian:** ghi ngày/kỳ mục tiêu Y và acquisition dates của X; kiểm tương thích lớp theo mùa/vụ, thời kỳ quan sát và thay đổi sử dụng/lớp phủ. Cùng năm chưa đủ cho lớp biến động nhanh. Nhãn 2021 không tự áp cho HLS 2025; khác kỳ cần bằng chứng ổn định hoặc review/lọc biến động, chưa chốt tolerance ngày thay người duyệt.
2. **Lưới:** X, Y và QA/masks cuối có cùng CRS, affine, width/height và grid hash; kiểm overlay độc lập để phát hiện lệch nửa pixel, sai trục hoặc đăng ký nguồn sai. Rasterize polygon trực tiếp trên grid đích theo policy all-touched/pixel-center/biên đã khóa; nhãn phân loại resample nearest/mode/majority theo policy có kiểm purity/tie/ignore, không bilinear/cubic. Cùng GridSpec không tự chứng minh nguồn đã đồng đăng ký chính xác.
3. **Biên/khuyết:** pixel chưa chắc chắn được ignore/pending review kèm reason mask và provenance; không tự ignore mọi ranh giới hoặc ấn định 30% diện tích. Báo diện tích/số mẫu bị bỏ theo lớp/vùng và mức đại diện của tập kiểm. Loss phải cấu hình `ignore_index = -1` hoặc mask tương đương, metrics cũng lọc rõ; toàn batch chỉ có ignore phải xử lý hữu hạn/skip, không tạo loss NaN hoặc điểm số giả. Mask nhãn không thay mask quan sát/coverage ảnh.
4. **Split độc lập:** chia khối không gian và group theo scene/nguồn nhãn/thửa cùng thời gian trước chipping/augmentation. Kiểm chips chồng lấn, bản sao, cửa sổ ba frame dùng chung nguồn và khoảng cách/buffer theo thiết kế được duyệt; khác xã/huyện vẫn chưa tự chứng minh độc lập. Không random chip kề nhau từ cùng AOI giữa train/validation/test. Freeze test và cách lấy mẫu trước chọn model; validation dùng chọn model, test chỉ đánh giá độc lập theo protocol. Chưa chốt tỷ lệ split, buffer, số chip hoặc số vòng thử.

### Giao việc và bằng chứng nghiệm thu nhóm 3/4

| Gói giao nhận dự kiến | Vai trò thực hiện / người duyệt dự kiến | Bằng chứng cần có khi triển khai |
| --- | --- | --- |
| Sample manifest X–Y | GIS/data + ML / reviewer GIS | Sample/asset IDs/hash, provider/product/license, band order/units/scale, frame dates, target period, GridSpec/TransformSpec, QA/label masks và label provenance; resolve được trên dữ liệu có quyền |
| Label plan + split manifest | GIS/data/giải đoán / chủ nghiệp vụ và reviewer độc lập | Nguồn nhãn/phân vai warm-up vs tham chiếu, QC/bất đồng/ignore reasons, class mapping, region/time groups và bản đồ/báo cáo overlap/leakage trước chipping |
| Báo cáo kiểm cặp mẫu | GIS/data + ML/QA / reviewer GIS/ML | Lệnh/environment/input hashes; overlay/grid/registration, categorical resample không sinh lớp lạ, dtype round-trip, scale đúng một lần, năm nhuận, ignored-loss/metrics và all-ignore batch; có ca âm sai grid/ngày/mask |

Đây là nội dung hồ sơ dự kiến trong dataset manifest/label plan và deliverable SPEC-008, chưa tạo schema trao đổi mới hoặc file manifest rỗng. Tên người giao/nhận/duyệt, nguồn cụ thể, số lượng mẫu và kết quả kiểm thực còn thiếu. Khi triển khai manifest có kiểu phải đi theo SPEC-001/Pydantic, docs/fixture/test cùng task; đợt này không thay schema/code.

## Bộ ngưỡng người dùng cung cấp và điều kiện khóa protocol

[Tiêu chí nghiệm thu](../domain/acceptance-criteria.md) giữ bảng F1/IoU/PA/UA cho đủ bảy lớp và macro/OA, coverage mùa khô 97%/mùa mưa 90%, sai lệch diện tích lớp 0/1/2 ≤8%, CI 95%, RMSE VN-2000 ≤15 m/diện tích AOI ≤0,1%; ghi tài nguyên/SLA GPU, training cap và early stopping. Các giá trị là yêu cầu cung cấp, chưa là kết quả đã đạt hay chuẩn chung được xác minh từ bài báo.

Người dùng đã xác nhận máy GPU 16–24 GB VRAM/RAM 32 GB/SSD 500 GB dùng riêng cho training/benchmark; desktop giữ mục tiêu ít nhất 20 GB RAM/8 GB VRAM (G0-D10). Để khóa 002.3 còn cần protocol lấy mẫu/metric/CI/cỡ mẫu, phạm vi coverage T=3 và hai nhánh số quan sát, ngưỡng diện tích lớp 3/4 và lựa chọn 10–15%, operation/điểm chuẩn, máy thực/CPU SLO, ranh giới đo thời gian và số vòng/chi phí/lịch campaign cụ thể. [Báo cáo đối chiếu](../evidence/2026-11-08-acceptance-review.md) lưu các hiệu chỉnh; không tự chọn 3 hay 5 vòng. G0 chốt budget, không cho tự fine-tune trước dependency SPEC-008.

## Chấp nhận và kiểm tra

- Chủ nghiệp vụ/chủ dự án xác nhận decision record với ngày và phạm vi; mọi giá trị còn thiếu giữ trạng thái chưa chốt, G0 chưa pass.
- Data manifest resolve đúng asset/version/hash; không chứa credential hoặc signed URL. Coverage không dùng percent-cloud scene thay mask AOI.
- Review độc lập một số scene/ngày và kiểm tổng diện tích valid/invalid bằng AOI; fixture nhỏ tính tay đối chiếu thống kê tự động.
- Workload profile có lệnh đo reproducible, chưa gắn ước tính throughput thành benchmark. Split kiểm overlap; chưa cần toàn bộ nhãn đã hoàn tất để spike G1.

Các phép kiểm dữ liệu thực phụ thuộc provider/AOI chưa được cung cấp nên chưa có test executable. Khi chọn provider, task data tiếp theo phải có fixture offline cho QA/coverage và opt-in live check có cấu hình credential, không hard-code tài khoản. Chỉ chuyển G0 khi đủ bằng chứng, có thể song song SPEC-003/004 bằng fixture tổng hợp.
