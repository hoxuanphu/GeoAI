# SPEC-000 — Bộ tài liệu bàn giao cho AI/dev

**Trạng thái:** hoàn tất phạm vi tài liệu ngày 08/11/2026; bằng chứng tại [báo cáo kiểm tài liệu](../evidence/2026-11-08-documentation-review.md). Chưa triển khai code hoặc đóng gate runtime.
**Mục tiêu:** dev biết phải đọc gì, phần nào đã chốt, file nào cần tạo và lấy bằng chứng nào trước khi đánh dấu hoàn tất.
**Phạm vi được yêu cầu:** chỉ viết tài liệu; giữ nguyên mã, test, fixture và cấu hình đang có. Không triển khai tiếp SPEC-001–007.

Baseline trên được giữ làm lịch sử; đợt bổ sung sau review mở rộng phạm vi tài liệu tới SPEC-008/009, ADR-011 và resolver/security, vẫn chưa code SPEC-001–009.

## Đầu vào và đầu ra

Đầu vào: yêu cầu người dùng, [đề xuất v1.4](../../solution/de_xuat_kien_truc_he_thong_geoai_tong_hop.md), [kiến trúc 1.1](../../kien_truc_he_thong.md), bộ plans, bảng cấu trúc docs được chọn và hiện trạng file.

Đầu ra: chỉ mục/roadmap, architecture/contracts/domain/Prithvi/IPC/physical models, mười ADR có trạng thái, SPEC-001–007, [hướng dẫn dev](../guides/development-guide.md), [ma trận kiểm tra](../guides/testing-strategy.md) và báo cáo bằng chứng kiểm tài liệu. SPEC-007 bổ sung phần nền tảng G1 ngoài spike model. Đồng bộ đường dẫn ADR từ tài liệu nguồn sang `Artchitect/docs/adr/`; không thay yêu cầu Prithvi hay tự chốt gate.

## Điều kiện hoàn tất

- [x] Mỗi nhóm trong bảng tài liệu người dùng có file thực và chỉ dẫn khi đọc.
- [x] Không mô tả schema/exporter/runtime chưa hoàn chỉnh như đã triển khai hoặc pass; file đích tương lai được ghi bằng đường dẫn dự kiến.
- [x] Contracts có ngữ nghĩa để làm đầu vào triển khai, IPC có state/race/publish rõ, GIS/Prithvi/toán–vật lý giữ đơn vị và giới hạn; chưa là spec của từng PHY G4 chưa được chọn.
- [x] ADR-001–010 có bối cảnh, lựa chọn, phương án, hệ quả và điều kiện kiểm chứng; trạng thái đề xuất tách khỏi yêu cầu sản phẩm đã xác nhận.
- [x] Spec thực thi có dependency, input/output, acceptance, ca kiểm và giới hạn; không dùng ví dụ tổng hợp làm bằng chứng G0–G4.
- [x] Kiểm liên kết/file/anchor, UTF-8, code fence, JSON ví dụ và đồng bộ sổ ADR; lưu phạm vi và kết quả trong `Artchitect/docs/evidence/2026-11-08-documentation-review.md`.
- [x] Hash các file không phải Markdown trước/sau giống nhau; không tạo thêm mã, test, fixture hay cấu hình.

## Bằng chứng và giới hạn

Đã lưu [báo cáo kiểm tài liệu](../evidence/2026-11-08-documentation-review.md), đối chiếu phạm vi trên bằng kiểm cấu trúc và review nội dung. Các phép kiểm này không chứng minh renderer Mermaid, schema validator, PROJ/GDAL, model, solver, desktop hay installer chạy được. G0 và SPEC-001 tiếp tục chưa hoàn tất.

## Điều chỉnh vị trí tài liệu

Ngày 08/11/2026, người dùng yêu cầu chuyển bộ tài liệu vào `Artchitect/`. Di chuyển đủ 31 file sang `Artchitect/docs/`, giữ các thư mục con ADR/specs/evidence; cập nhật liên kết nội bộ/nguồn, README, AGENTS và đường dẫn deliverable tài liệu. Không tạo bản sao thư mục cũ, không thay mã hoặc cấu hình; kiểm tra sau di chuyển được ghi bổ sung trong báo cáo bằng chứng.

## Bổ sung sau review kiến trúc

**Trạng thái đợt bổ sung:** hoàn tất phạm vi tài liệu ngày 08/11/2026; [bằng chứng kiểm trực tiếp](../evidence/2026-11-08-review-followup.md). Chưa nghiệm thu runtime, model hoặc G0–G4.

- [x] SPEC-008 xác định input/output, trách nhiệm, recipe/evaluation/model pack và dependency của SPEC-006; không đặt dữ liệu/ngưỡng/hyperparameter giả.
- [x] ADR-011 nêu phương án, phạm vi account/session, một owner/job nặng, khóa/fencing/lease và recovery còn worker sống; giữ trạng thái đề xuất.
- [x] Worker resolver có bootstrap/context/schema draft, cấp quyền read/write, external input, revocation/candidate; không đưa URL/credential hoặc path UI vào worker.
- [x] SPEC-009 và security matrix có ca âm/dương archive/path/reparse/VRT/network/context/candidate; dependency không vòng với SPEC-004.
- [x] Đồng bộ đề xuất nguồn, plans chịu ảnh hưởng, kiến trúc, AGENTS, indexes, roadmap, specs và testing strategy; G0–G4 vẫn chưa đạt.
- [x] Kiểm UTF-8, link/anchor, fence/bảng/JSON, ADR và đồng bộ nguồn; hash code/test/fixture/config không đổi, không tạo file triển khai.

## Tracker tiến độ

Ngày 08/11/2026, bổ sung [task tracker](../task-tracker.md) theo yêu cầu người dùng: bảng SPEC-000–009, mốc con, dependency, vai trò dự kiến, việc chờ, bằng chứng và lịch sử cập nhật. Không suy phần trăm dự án từ checkbox hoặc coi tài liệu/spec đã viết là code đã nghiệm thu. Trạng thái khởi tạo và kết quả kiểm được ghi tại [bằng chứng tracker](../task-tracker.md#tracker-verification); không thay kết quả lịch sử của các đợt baseline/review trước.

Đã hoàn tất phạm vi khởi tạo tracker sau kiểm cấu trúc/độ phủ và hash file implementation; các task triển khai và gate giữ nguyên trạng thái.

## Vẽ lại kiến trúc desktop ngày 09/11/2026

**Trạng thái:** hoàn tất phạm vi tài liệu sau kiểm cấu trúc; không nghiệm thu renderer hoặc runtime. Người dùng chọn Windows desktop theo thiết kế GeoAI hiện tại, lưu Markdown và trình bày sơ đồ trong chat; không chọn kiến trúc web/server của hướng dẫn đính kèm.

- [x] Tạo [bộ sơ đồ desktop chi tiết](../platforms/windows/desktop-architecture-diagrams.md): 6 flowchart, 1 sequence diagram, 1 state diagram; kèm trách nhiệm module, quyền ghi, pipeline, provenance, storage, training và ánh xạ gate.
- [x] Nối từ [architecture](../architecture.md), đồng bộ roadmap/tracker; không thay yêu cầu, schema, mã nguồn, dependency hoặc trạng thái ADR.
- [x] Đối chiếu với architecture/ADR-011, IPC/resolver, contracts, Prithvi/domain rules và SPEC-008; giữ G0 chưa đạt và tách thiết kế đích khỏi hiện trạng triển khai.

**Bằng chứng kiểm trực tiếp:** PowerShell trên Windows, 09/11/2026, đọc UTF-8 strict bằng `System.Text.UTF8Encoding(false, true)`; regex kiểm link Markdown cục bộ qua URI decode + `Test-Path`, đếm code fence/loại diagram và cặp dấu bao; `git diff --check` cho tài liệu liên quan. Bộ sơ đồ: 26 links tới file/thư mục có thật, 16 fence cân bằng, 8 diagram (6 flowchart + 1 sequence + 1 state), cặp dấu bao cân bằng. Architecture: 16 links hợp lệ, 2 fence cân bằng. Lần kiểm đầu đặt nhầm kỳ vọng 9 diagram nên báo lỗi; đã sửa kỳ vọng theo 8 diagram thực tế và chạy lại pass, không thêm sơ đồ chỉ để đạt số đếm.

**Giới hạn:** không có Mermaid parser/CLI sẵn trong môi trường đã probe; không cài dependency chỉ để kiểm tài liệu. Chưa parse/render Mermaid tự động; kiểm dấu bao không thay parser. Không chạy suite runtime vì chỉ thay tài liệu; bằng chứng này không chứng minh GIS/model/native/database/installer hoặc G0–G4 đạt. Giữ nguyên các thay đổi backend và môi trường có sẵn trong working tree.

## Phát triển tài liệu Ubuntu ngày 10/11/2026

**Phạm vi:** tiếp tục tài liệu Ubuntu 22.04 LTS và Ubuntu 24.04 LTS theo yêu cầu người dùng; không triển khai adapter/runtime hoặc đổi schema/fixture/config sản phẩm. **Trạng thái đợt này:** hoàn tất phạm vi tài liệu sau kiểm trực tiếp, [kết quả](../evidence/ubuntu-2026-11-10/results.json) và [review/giới hạn](../evidence/ubuntu-2026-11-10/review.md). Baseline và kết quả lịch sử bên trên không bị thay thế.

- [x] ADR-012 phân biệt yêu cầu OS đã xác nhận với đề xuất kỹ thuật; liên kết ADR-001/006/011, không ghi Accepted hoặc thay yêu cầu Prithvi.
- [x] Kiến trúc có sơ đồ/module, owner/supervisor/cgroup, recovery, private FD, resolver, publish/durability và storage/XDG.
- [x] Guide nêu preflight/dependency/runtime Python, build ABI/`.deb`, offline/upgrade/uninstall; không mô tả lệnh dự kiến thành kết quả đã chạy.
- [x] Ma trận UB-01–20 ghi scope/bằng chứng hai LTS, task/dependency trước G0 và phân biệt container/desktop/GPU/máy sạch; runtime cases vẫn chưa chạy.
- [x] Đồng bộ nguồn tổng hợp/kiến trúc/plans, docs/indexes, SPEC-003/004/009, roadmap/tracker và kiểm UTF-8/link/anchor/fence/trạng thái; đối chiếu hash implementation trước/sau.

Bằng chứng/lệnh/giới hạn ở báo cáo Ubuntu: kiểm cấu trúc pass, 145 file bảo vệ ngoài `Artchitect/` không đổi hash. Mermaid mới chỉ kiểm text, chưa parse/render; không chạy suite runtime chỉ để nghiệm thu sửa Markdown. Kỹ thuật Linux và G0–G4 giữ trạng thái chưa nghiệm thu.

## Sắp xếp tài liệu theo chủ đề ngày 10/11/2026

**Phạm vi:** theo lựa chọn của người dùng, sắp xếp tài liệu vào thư mục nền tảng, nghiệp vụ, hướng dẫn và dự án; cập nhật mục lục/đường đọc, giữ liên kết cũ qua các trang tương thích và giữ file bắt buộc của AGENTS tại đường dẫn cũ. **Trạng thái:** hoàn tất phạm vi sắp xếp tài liệu sau kiểm trực tiếp; xem [báo cáo](../evidence/docs-organization-2026-11-10/review.md) và [kết quả](../evidence/docs-organization-2026-11-10/results.json).

- [x] Đặt 10 tài liệu chính trong thư mục chủ đề và giữ anchor cũ qua trang tương thích.
- [x] Nhóm mục lục theo nhu cầu đọc, thêm chỉ mục nhóm và bằng chứng; cập nhật liên kết tài liệu đang sử dụng.
- [x] Kiểm liên kết/anchor và tính toàn vẹn file được bảo vệ; ghi lệnh, kết quả, giới hạn và đường dẫn bằng chứng.

Việc sắp xếp không đổi yêu cầu/ADR/schema, kết quả lịch sử, runtime hoặc gate. Snapshot/log và công cụ kiểm Ubuntu cũ được giữ nguyên theo thời điểm ban đầu; để chạy lại kiểm cũ cần checkout tương ứng, còn cấu trúc hiện tại được kiểm bằng công cụ của đợt sắp xếp.

## Hoàn thiện SPEC-010 Ubuntu foundation ngày 10/11/2026

**Phạm vi:** người dùng yêu cầu hoàn thiện spec trước. Viết [SPEC-010](010-ubuntu-foundation.md) cùng [native profile](../platforms/ubuntu/ubuntu-native-profile.md) và [interface adapter](../platforms/ubuntu/ubuntu-adapter-interfaces.md), đồng bộ nguồn/ADR/specs/tracker. **Trạng thái:** hoàn tất rà soát/kiểm tài liệu; code, Pydantic/schema/client, test sản phẩm và dependency giữ nguyên.

- [x] Đặc tả có target/phạm vi/dependency/file/interface, protocol, error/cleanup và tiêu chí fixture thật; phân biệt spec hoàn tất với code chưa làm.
- [x] Rà độc lập và sửa các khoảng trống quan trọng về creator identity, stop race và generation recovery; giữ ADR kỹ thuật đề xuất.
- [x] Kiểm UTF-8/link/anchor/fence/tables, độ phủ 010-T01–09 và mốc 010.1–010.3; hash code/config/test/bằng chứng cũ trước/sau không đổi.

Lệnh/kết quả và giới hạn tại [hồ sơ SPEC-010](../evidence/spec010-2026-11-10/review.md). Đã đóng mốc tài liệu 000.7 sau kiểm; các mốc code SPEC-010 và gate giữ chưa hoàn tất.

## Lập plan Ubuntu foundation chi tiết ngày 10/11/2026

**Yêu cầu:** dùng Superpowers lập plan thật kỹ để AI gen code từng bước. **Phạm vi:** tài liệu kế hoạch, không thực thi task code. **Trạng thái:** hoàn tất sau self-review và kiểm tài liệu. [Plan tổng](../superpowers/plans/2026-11-10-ubuntu-foundation.md), 5 phần A–E và catalog/handoff có 26 task/133 bước dự kiến; [bằng chứng kiểm](../evidence/ubuntu-plan-2026-11-10/review.md).

- [x] Đối chiếu source hiện tại/SPEC-010, phân file/interface/dependency và quy định cho implementer context nhỏ.
- [x] Self-review task/step/type/Review Focus/coverage; ghi test/assertions, lệnh targeted, expected results, checkpoint/handoff và điều kiện fail/skip/not_run.
- [x] Kiểm cấu trúc/liên kết, 26 task/9 suite/mốc triển khai chưa tick; hash source/config/schema/test/bằng chứng lịch sử không đổi.

Đã đóng mốc tài liệu 000.8 sau kiểm; task A-01–E-05, mốc010.1–010.3 và G0–G4 giữ chưa hoàn tất.
