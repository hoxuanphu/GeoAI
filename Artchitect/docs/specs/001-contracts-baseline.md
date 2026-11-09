# SPEC-001 — Contracts dự thảo 0.1.0

**Trạng thái:** hoàn tất phạm vi schema draft 0.1.0 theo yêu cầu code ngày 08/11/2026; 51 test/schema check đã qua và [review độc lập PASS](../evidence/codegen-2026-11-08/task-2-review-report.md). [Nhật ký/bằng chứng](../evidence/codegen-2026-11-08/progress.md). DTO API bổ sung ở SPEC-003 phải chạy lại suite/schema; chưa xác nhận runtime/gate G0/G1.
**Mục tiêu:** dev có schema Pydantic dùng lại, trường/đơn vị nhất quán và ví dụ có thể kiểm tra, không phải tự suy bảng prose.

**Kiểm lại sau tích hợp API DTOs SPEC-003:** 55 tests contracts pass, cả contracts schema và OpenAPI/client check current; [bằng chứng cuối](../evidence/codegen-2026-11-08/handoff.md), [review cuối](../evidence/codegen-2026-11-08/final-review-report.md). Con số 51 bên dưới ghi lượt hoàn tất riêng phần nền trước bổ sung API, không phải tổng suite hiện tại.

## Input và output

Input: [contracts thiết kế](../../plans/05_hop_dong_du_lieu_va_versioning.md), [domain rules](../domain-rules.md), [IPC](../ipc-protocol.md), [Prithvi](../prithvi-profile.md). Output: `backend/geoai/contracts/{common,geography,models,runs,rpc}.py`, public exports, exporter JSON Schema, fixture workflow và unittest.

Interfaces: record bền vững có schema_version/created_at; các class public và ngữ nghĩa ở [contracts.md](../contracts.md); RPC hỗ trợ capabilities/start/cancel/shutdown và attempt event. JSON Schema sinh từ Python, không viết tay. Package hiện chỉ cần Pydantic, chưa thêm GDAL/FastAPI/PyTorch.

Bổ sung draft sau review: RPC start có access_context_id/hash theo [worker resolver](../worker-resolver.md). Đã định kiểu `access.py`, đồng bộ RPC/registries/exporter và fixture/test start/context ở SPEC-001. [SPEC-009](009-importer-worker-resolver.md) tiếp tục phần native/resolver và phải chạy lại các ca tích hợp. Không tạo vòng phụ thuộc đòi resolver native hoàn tất mới viết được kiểu nền; schema metadata chưa chứng minh quyền I/O thực.

## Kiểm kê bàn giao hiện tại

| Hạng mục | Trạng thái quan sát được |
| --- | --- |
| `common.py`, `geography.py`, `models.py` | Kiểu nền đã được suite kiểm; không tải GIS/model runtime |
| `runs.py`, `rpc.py`, `access.py`, `contracts/__init__.py` | Có record run/review/report, method/event RPC, private context và registry tách durable/wire/private |
| `tools/export_contract_schemas.py`, `schemas/contracts-v0.1.0.json` | Export offline xác định; `--check` phát hiện missing/stale và không sửa artifact |
| [test contracts](../../../tests/contracts/test_contracts.py), [fixture](../../../tests/fixtures/contracts/workflow.json) | 51 test đã pass; bổ sung fixture RPC và private context, vẫn là dữ liệu tổng hợp |

Baseline được chạy mới trước sửa code: 30 tests, 1 failure/45 errors gồm subtests do thiếu implementation. Sau triển khai parent chạy lại 51 tests PASS và schema check PASS; log ở nhật ký. Đã sửa comment affine thành `[a,b,c,d,e,f]` theo [quy ước affine](../domain-rules.md), khác GDAL GeoTransform. Lịch sử kiểm tài liệu trước đó vẫn giữ nguyên.

## Điều kiện chấp nhận

- Từ chối schema_version/field lạ, thời gian naive, số không hữu hạn; UTC có thể normalize từ timezone có offset.
- Grid affine không suy biến, categorical không dùng nội suy sinh lớp; geometry WGS84 có range/ring closure hợp lệ, chưa thay topology validation GIS.
- Band/stats/shape ModelSpec nhất quán; model nghiệp vụ cần decoder/evaluation đúng trạng thái; technical evaluation không tự pass gate nghiệp vụ.
- Published manifest cần output/checksum và attempt/job khớp; revision reviewed và report official có metadata bắt buộc. Service vẫn kiểm reference/quyền/fencing/bytes/gate thực.
- RPC result/error tách biệt, id không boolean, start/cancel có attempt key, progress không vượt total; JSON-RPC không đồng nghĩa có transport.
- Ví dụ round-trip JSON, các ca sai bị từ chối, exporter chạy offline và --check phát hiện artifact lệch.

## Test phải qua và bằng chứng

```powershell
$env:PYTHONPATH = 'backend'
python -m unittest discover -s tests/contracts -v
python tools/export_contract_schemas.py --check
```

Test gồm UTC/version, namespace/secret field, geometry/grid, normalization, technical/business, publish/provenance, review/report, RPC và exporter. Fixture chỉ là JSON tổng hợp, không dùng làm dataset/golden output ML. Hoàn tất task này chưa đóng G0/G1; task tiếp theo SPEC-002 và skeleton SPEC-003.

## Checklist triển khai

- [x] Đối chiếu trường/enum/required với contracts và IPC; bổ sung kiểm thử âm và dương cho invariant liên trường trong phạm vi draft.
- [x] Hoàn thiện các record run/RPC/context, public exports và registry; không thêm GDAL/model runtime vào package contracts.
- [x] Triển khai exporter xác định, sinh schema rồi kiểm missing/stale artifact bằng `--check`.
- [x] Chạy suite, lưu kết quả/environment/lệnh vào [bằng chứng](../evidence/codegen-2026-11-08/task-1-report.md), chạy lại độc lập và review; cập nhật roadmap/tracker.

Giới hạn đã biết: fixture chỉ có một asset blue nhưng ModelSpec mô tả sáu kênh; các record là ví dụ cấu trúc riêng lẻ, không phải workflow HLS hợp lệ. Tolerance, mean/std, hash và số liệu trong fixture không được dùng cho inference/nghiệm thu.

Giới hạn profile PHY: `PhysicalModelSpec`/`JobSpec` giữ thiết kế tham chiếu; `RunManifest` từ chối physical refs/provenance cho tới khi có profile có kiểu riêng trong spec G4. Không nhận dict tùy ý để giả đủ parameter/forcing/solver provenance. Các kiểm reference/quyền/fencing/bytes và toàn bộ native path/handle của context còn ở service/SPEC-009/004.
