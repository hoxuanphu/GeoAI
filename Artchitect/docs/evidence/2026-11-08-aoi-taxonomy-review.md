# Đối chiếu AOI và bộ bảy lớp ngày 08/11/2026

**Task:** [SPEC-002](../specs/002-g0-evidence.md), ghi nhận yêu cầu từng phần. **Múi giờ:** Asia/Bangkok (UTC+07:00). **Phạm vi:** tài liệu; không tiếp tục code, G0 chưa đạt.

## Nội dung đối chiếu

Yêu cầu trực tiếp hiện tại xác nhận AOI được vẽ trên bản đồ, dựa vào ảnh vệ tinh import hoặc import Shapefile; cung cấp bảy lớp IDs 0–6, `ignore_index = -1`, mô tả vật lý, dấu hiệu HLS S30/đa thời gian và crosswalk WorldCover/JAXA. [AOI policy](../aoi-policy.md), [taxonomy](../landcover-taxonomy.md), profile và một số tài liệu nguồn đã có phần ghi nhận này trong baseline đầu phiên; đợt này giữ nội dung đó và hoàn thiện các chỗ chưa đồng bộ.

[Decision record](g0/decision-record.md) bổ sung nguyên văn phát biểu AOI, phân biệt cách diễn giải footprint/snapshot với phát biểu gốc, sửa hai liên kết trỏ sai thư mục và bỏ cách ghi T=1 như xác nhận mới của người dùng. Bảng hiện tại nêu T=3 ở mô tả cây trồng; baseline áp profile T=3 cho model nghiệp vụ bảy lớp, T=1 cho spike kỹ thuật. SPEC-008 trước còn ghi input T=1/224; đã đồng bộ thành T=3/224 và ghi yêu cầu kiểm riêng, không lặp ảnh.

Đồng bộ SPEC-002/006/008, roadmap, tracker, architecture, kiến trúc hệ thống, domain rules và chỉ mục. Giữ bảy lớp học; -1 không thành kênh thứ tám, lớp 0 không là NoData. Lớp 4 wetland/mangrove có trong bản đồ đầu; luồng giám sát ngập chuyên biệt ở đợt sau. AOI người dùng chọn không bị thu theo valid mask. WorldCover/JAXA chỉ là weak labels có phiên bản, ao nuôi chuyển nhãn có điều kiện, wetland cây gỗ cần nhãn bổ sung và nhãn test phải độc lập. Dấu hiệu phổ chưa là luật/ngưỡng định lượng đã kiểm.

Đề xuất tổng hợp và plans 03/06/07 đã ghi cách tạo AOI, bảy lớp và T=3 trong baseline; đợt này đối chiếu các đoạn đó, không sửa quyết định Prithvi tại ADR-008 hoặc đổi kiến trúc cần ADR thay thế. Các bằng chứng kiểm tài liệu cũ giữ nguyên kết quả lịch sử.

## Kiểm tra và kết quả

Chạy Python trên Windows/PowerShell tại root GeoAI, đọc file UTF-8 và đối chiếu SHA-256 với inventory chụp đầu phiên. Bộ kiểm tạm nằm ngoài workspace; không thêm script/test/config vào dự án. Lệnh thực:

```powershell
python -X utf8 'C:/Users/phuhx1/AppData/Local/Temp/geoai-aoi-intake-k201rkfq/verify_docs.py'
```

Kết quả trực tiếp: exit code 0, không phát hiện lỗi qua 72 Markdown, 590 liên kết nội bộ (75 có anchor), 187 bảng và 5 block JSON parse được; UTF-8/control và code fence đạt theo parser cấu trúc đơn giản. Chỉ kiểm file/anchor đích nội bộ, không kiểm URL ngoài, không render Markdown/Mermaid hoặc xác minh nội dung khoa học từ website.

Đối chiếu đủ tám ID trong bảng (0–6 và -1), bảy quyết định G0-D01–D07, 31 ID mốc tracker duy nhất; chỉ 000.1–000.3 đã checked. Chín tài liệu nguồn/spec/roadmap chứa các nội dung AOI/bảy lớp/profile cần đồng bộ; SPEC-008 không còn input `profile T=1/224`. Kiểm này xác nhận nội dung tài liệu, không phải shape test trên model thật.

Inventory trước/sau: sửa 11 Markdown và thêm báo cáo này, không xóa file; SHA-256 của cả 8 file mã/test/fixture/config giữ nguyên. Hoàn tất đợt đối chiếu tài liệu này; SPEC-002 vẫn chờ đầu vào, 002.1–002.3 và G0 chưa hoàn tất. Kết quả các báo cáo cũ không được sửa thành số đo mới.

## Còn chờ

Các mốc 002.1–002.3 chưa hoàn tất: còn AOI kiểm định/thời gian, QC/crosswalk/nhãn/split/license và người duyệt; provider/band/QA/coverage thực; lịch ba frame, CRS/tolerance, hardware/workload/gate/budget/điểm dừng. Không chạy contracts/runtime/model, không kiểm lại nguồn web/license, không tải ảnh/nhãn/trọng số hoặc benchmark. Kiểm tài liệu không chứng minh model, importer, CRS hoặc UI đã hoạt động.
