# Kiểm tài liệu bổ sung sau review ngày 08/11/2026

**Task:** [SPEC-000, đợt bổ sung](../specs/000-documentation-baseline.md). **Múi giờ:** Asia/Bangkok (UTC+07:00).
**Trạng thái:** hoàn tất phạm vi tài liệu bổ sung sau review; các phép kiểm cấu trúc và đối chiếu nêu dưới đạt. Chưa nghiệm thu runtime/model hoặc G0–G4.

## Phạm vi

Theo yêu cầu người dùng, bổ sung bốn khuyến nghị đã đối chiếu: SPEC-008 dataset/training/evaluation/model pack; ADR-011 execution owner local; worker resolver và start context; SPEC-009/ma trận importer-resolver security. Cập nhật dependency/roles/acceptance và tài liệu nguồn/plans chịu ảnh hưởng, giữ baseline v1.4/kiến trúc 1.1 bằng ghi chú bổ sung ngày 08/11/2026.

Chỉ thay Markdown; không sửa schema Pydantic, fixture, test, cấu hình hoặc tạo mã. SPEC-001 vẫn dang dở; các kiểu/context/start fields mới chỉ là draft phải hiện thực khi người dùng yêu cầu triển khai. Không tự đặt AOI/nhãn/ngưỡng/hardware/budget/hyperparameter hoặc xác nhận tên người được giao.

## Phép kiểm và kết quả

Chạy kiểm trực tiếp bằng `python -X utf8 -` qua PowerShell here-string/stdin, chỉ dùng thư viện chuẩn, không thêm script sản phẩm. Đã đọc output và exit code 0. Phạm vi gồm toàn bộ Markdown trong `Artchitect/docs/`, `Artchitect/plans/`, bản tổng hợp, kiến trúc, AGENTS và README ở root. Bộ kiểm dùng parser đơn giản cho cấu trúc hiện có, không là parser CommonMark đầy đủ.

| Phép kiểm | Kết quả |
| --- | --- |
| UTF-8 và inventory Markdown | 59 file đọc được; không phát hiện ký tự thay thế/control bất thường |
| Liên kết nội bộ | 510 lượt resolve, 74 lượt có anchor; không có file/anchor thiếu |
| Bảng/fence/JSON | 123 bảng khớp số cột; không có fence chưa đóng; 5 block JSON parse được và không chứa NaN/Infinity |
| Mermaid | 8 block không rỗng và fence đóng; chưa render/kiểm syntax bằng engine |
| ADR | 11 hồ sơ đủ sáu mục, sổ ADR nguồn/plans khớp; ADR-011 giữ trạng thái đề xuất có điều kiện |
| Đồng bộ nguồn | 7 nhóm đoạn bổ sung nguồn/plans và 3 dòng ma trận gate mới khớp sau bỏ markup liên kết |
| Security acceptance | Đủ 25 ID duy nhất: IMP-01–11, NET-01–06, RES-01–08; đây là danh sách ca cần thực hiện, chưa có test pass |
| Giữ nguyên implementation | 8 file code/test/fixture/config có SHA-256 trước/sau trùng; không thêm/xóa file loại này trong phạm vi kiểm kê |

Inventory không đổi: `backend/geoai/__init__.py`, `backend/geoai/contracts/{common,geography,models}.py`, `tests/contracts/test_contracts.py`, `tests/fixtures/contracts/workflow.json`, `pyproject.toml`, `.gitignore`. Không kiểm lại package môi trường/venv như source sản phẩm.

Review nội dung đã đối chiếu: training không dependency vòng với workflow/UI; resolver có thể dựng fixture trước nghiệm thu SPEC-004; kiểu nền SPEC-001 tách khỏi nghiệm thu schema/context tích hợp; execution owner khác writer/fencing/pin; external input không bị cấm hàng loạt; context private không giả là sandbox; CPU chính thức/NVIDIA tùy chọn; ADR còn đề xuất và G0–G4 chưa đóng. Không gán thông số nghiệp vụ hoặc người thực hiện chưa được xác nhận.

Đợt này thêm sáu file Markdown: hai spec, ADR-011, worker resolver, security matrix và báo cáo này; đồng bộ 29 file Markdown đã có. SPEC-008/009 chưa triển khai, SPEC-001 còn thiếu deliverable như trước. Baseline v1.4/kiến trúc 1.1 được giữ, bổ sung lịch sử/nội dung cùng ngày thay vì mô tả thay đổi là đã phát hành API mới.

## Giới hạn

Không chạy suite contracts, training/evaluation/benchmark, Windows process/handle/security, driver GIS, model, installer hoặc renderer Mermaid. Kiểm cú pháp JSON không thay validation bằng Pydantic; kiểm link không xác minh website ngoài. Đặc tả acceptance mới không chứng minh đã có test pass. Báo cáo baseline/di chuyển trước đó được giữ riêng, không đổi kết quả lịch sử thành bằng chứng mới.
