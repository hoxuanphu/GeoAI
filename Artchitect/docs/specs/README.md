# Đặc tả task

Đọc [roadmap](../roadmap.md) trước chọn task. Mỗi spec ghi mục tiêu, dependency, input/output, giới hạn, acceptance và test phải chạy. Các đường code/test chưa tồn tại là **deliverable dự kiến**, không bằng chứng đã triển khai. Người dùng đã yêu cầu triển khai code ngày 08/11/2026; theo dõi trạng thái thực và bằng chứng ở tracker/spec, không suy gate đạt từ việc đã tạo file.

Trạng thái/mốc con tổng hợp được theo dõi tại [task tracker](../task-tracker.md); acceptance chi tiết và bằng chứng đóng task vẫn nằm trong spec tương ứng. Cập nhật cả hai khi bàn giao và đồng bộ roadmap nếu gate/phạm vi đổi.

| Spec | Mục tiêu | Dependency |
| --- | --- | --- |
| [000](000-documentation-baseline.md) | Hoàn thiện tài liệu AI/dev, trạng thái trung thực và kiểm liên kết | Yêu cầu chỉ làm tài liệu, đề xuất v1.4 |
| [001](001-contracts-baseline.md) | Contracts/schema dự thảo dùng chung, ví dụ và negative tests | Thiết kế v1.4 |
| [002](002-g0-evidence.md) | Hồ sơ dữ liệu/gate/ngân sách G0; đã có decision record từng phần, G0 chưa đạt | Đầu vào nghiệp vụ/GIS/ML còn thiếu theo spec |
| [003](003-desktop-shell.md) | UI khởi động sidecar, health/capabilities và dừng sạch | Contracts, ADR-001/006 |
| [004](004-jobs-and-publish.md) | Job/attempt/IPC/staging/publish/recovery | Kiểu nền contracts, launcher SPEC-003; nghiệm thu với resolver SPEC-009 |
| [005](005-prithvi-spike.md) | Tách rủi ro dữ liệu/shape/export/CPU khỏi nhãn | Đầu vào G0 tương ứng, SPEC-004 |
| [006](006-landcover-workflow.md) | Luồng Prithvi nghiệp vụ tới review/PDF | G0 đóng, G1 đạt phần phụ thuộc gồm resolver SPEC-009; model pack/test từ SPEC-008 |
| [007](007-g1-platform-validation.md) | GIS/viewer/PDF/bundle kỹ thuật và tổng hợp phần G1 còn lại | SPEC-001/003/004, fixture/CRS/hardware; SPEC-005 khi đo cùng AI |
| [008](008-training-evaluation-model-pack.md) | Sản xuất dataset/split/recipe/checkpoint/evaluation/model pack đầu vào SPEC-006 | G0/profile/nhãn/ngân sách tương ứng; promotion chạy lại export/runtime G2 |
| [009](009-importer-worker-resolver.md) | Bootstrap/context, importer/path/provider policy và worker resolve/candidate isolation | Kiểu nền SPEC-001, launcher SPEC-003; tích hợp SPEC-004, không dependency vòng |

SPEC-008 có phần chuẩn bị chạy song song G1, không đặt sau toàn bộ SPEC-007 chỉ vì số thứ tự lớn hơn. SPEC-009 dùng fixture để tạo resolver trước khi nghiệm thu SPEC-004; phần schema/start/context được đồng bộ cùng SPEC-001 trong lần tích hợp. Phần schema/context được kiểm riêng không chứng minh native resolver đã đạt acceptance.

Chỉ sửa code trong phạm vi spec đang làm. Phát hiện thay đổi hợp đồng/module/gate thì cập nhật spec/docs/schema/test liên quan; nếu thay thiết kế, cập nhật nguồn và ADR. Task nối tiếp không tự được coi hoàn tất vì dependency đã có file. G3/G4 lập spec riêng khi có nhu cầu và bằng chứng đầu vào, không tạo task solver trống.

Mỗi spec thực thi phải được bổ sung ngày chạy, môi trường, lệnh, kết quả và đường dẫn log/artifact theo [quy tắc bằng chứng](../testing-strategy.md). Giá trị nghiệp vụ còn chờ quyết định được nêu như dependency chưa đáp ứng; không dùng số trong ví dụ làm ngưỡng được duyệt.
