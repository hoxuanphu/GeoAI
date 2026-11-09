# Ma trận kiểm importer và resolver

**Trạng thái:** tiêu chí thiết kế/acceptance của [SPEC-009](specs/009-importer-worker-resolver.md), chưa có implementation hoặc kết quả test. Đọc cùng [worker resolver](worker-resolver.md), [bảo mật nguồn](../plans/14_bao_mat_server_va_van_hanh.md) và [IPC](ipc-protocol.md).

## Phạm vi và policy

Importer xử lý file/archive/model pack do người dùng chọn hoặc tải qua provider adapter đã đăng ký. Không tin file chỉ vì có đuôi GeoTIFF/GeoPackage hoặc có hash; hash không chứng minh nguồn tin cậy. Worker chỉ mở dependency được cấp và không phải sandbox chống mã độc cùng tài khoản. G0 chọn dữ liệu/provider và ngân sách; G1 kiểm policy bằng fixture nhỏ, chưa có quyền tải dữ liệu khách hàng để thử.

Trước xử lý phải có import policy version cùng giới hạn số entry, tổng bytes giải nén, bytes mỗi file, độ sâu lồng, tỷ lệ nén, thời gian, requests/redirect, network endpoints và loại driver/file. Không có policy/limit thì từ chối thao tác tương ứng; không dùng vô hạn mặc định. Giá trị test phải được ghi là fixture policy, không tự trở thành quota/G0 budget đã duyệt. Native parsing chạy worker/process phù hợp, log đã lọc và cancel có deadline; timeout không là lý do tự công bố file viết dở.

## Ca kiểm local và archive

| ID | Input/tình huống | Kết quả bắt buộc |
| --- | --- | --- |
| IMP-01 | Archive entry `../escape.tif`, `..\escape.tif`, root/drive path, UNC/device path | Từ chối trước ghi ra ngoài staging; kiểm separator chuẩn hóa, không chỉ tìm chuỗi `../` |
| IMP-02 | Windows ADS, tên thiết bị dành riêng, trailing dot/space và tên trùng sau case/Unicode normalization | Từ chối tên mơ hồ/đụng đích theo policy; không overwrite file đã có hoặc escape qua tên đặc biệt |
| IMP-03 | Symlink/junction/reparse point/hardlink trong archive hoặc ancestor đích | Không follow ra ngoài vùng được cấp; bản đầu từ chối entry link khi giải nén; không coi commonprefix là kiểm containment |
| IMP-04 | Đổi junction/file giữa kiểm path và open/use | Handle/file identity và destination thực vẫn đúng; nếu không bảo đảm thì fail, không dùng check-path trước rồi mở lại mù |
| IMP-05 | Nhiều entry, file cực lớn, archive lồng/tỷ lệ nén cao, khai uncompressed size sai | Chặn theo số đo thực trong lúc giải nén, không chỉ tin header; giới hạn bytes/time/depth, cleanup staging chưa công bố |
| IMP-06 | Archive hỏng, cancel, hết đĩa hoặc process crash giữa giải nén | Không kích hoạt pack/đăng ký asset hoàn chỉnh; cleanup/recovery không xóa dữ liệu nguồn của người dùng |
| IMP-07 | External input được người dùng đăng ký ngoài project | Đọc read-only đúng file có ID/hash/permission; không tự cấm vì nằm ngoài project và không cấp quyền mọi file cùng thư mục |
| IMP-08 | External file đổi nội dung/identity sau đăng ký hoặc trong lúc cấp grant | Từ chối version cũ hoặc materialize immutable copy; không chỉ dựa size/mtime, không thay InputSnapshot âm thầm |
| IMP-09 | VRT trỏ file ngoài allowlist, `/vsicurl/`, `/vsizip/`, nguồn HTTP/UNC hoặc pixel function tùy ý | Từ chối dependency chưa đăng ký và code động. VRT không bật mặc định cho import bản đầu; chỉ hỗ trợ khi parser/driver allowlist và toàn dependency đã kiểm |
| IMP-10 | Native format cần file phụ, sidecar mask/overview/QA hoặc path tìm kiếm mặc định | Chỉ mở dependency đã liệt kê; không scan thư mục hoặc truy cập mạng ngầm. Nếu driver không giới hạn được thì chuẩn hóa sang format an toàn hoặc chưa hỗ trợ |
| IMP-11 | Model pack đúng checksum nhưng nguồn/signature/license/implementation không hợp lệ | Không kích hoạt executable/pickle/plugin từ pack; chỉ registry runtime tin cậy và conversion policy đã kiểm |

Archive giải nén vào staging mới, không ghi thẳng lên project/model pack đang dùng. Dữ liệu tồn tại chỉ thành asset/pack hợp lệ sau kiểm nội dung, inventory/hash và transaction đăng ký; lỗi một entry không để phần còn lại được coi như import thành công khi workflow không cho phép partial.

## Ca kiểm network và provider

| ID | Input/tình huống | Kết quả bắt buộc |
| --- | --- | --- |
| NET-01 | URL/host/port/scheme ngoài policy provider, URL có userinfo hoặc client tự truyền URL thay asset ID | Không tạo generic URL fetcher; resolve qua adapter và allowlist endpoint/collection được cấu hình tin cậy |
| NET-02 | Redirect sang host/port không cho phép hoặc vượt hop limit | Kiểm mọi hop, không chỉ URL đầu; không forward Authorization/cookie sang origin mới, không log signed query |
| NET-03 | Host cho phép nhưng DNS/CNAME/IP thực tới loopback/private/link-local/metadata endpoint ngoài policy | Kiểm địa chỉ thực cho từng kết nối/redirect, xử lý DNS rebinding; từ chối nếu policy không cấp. Không chỉ so hostname |
| NET-04 | Provider nội bộ hợp lệ trên mạng riêng | Chỉ cho phép bằng profile triển khai được quản trị tin cậy và kiểm chứng riêng; không để project file mở policy mạng. Loopback API control của app không trở thành đích download |
| NET-05 | Stream vượt Content-Length/quota, timeout, redirect loop, response không đúng format | Giới hạn bytes thực/total deadline/redirect; không tin header, không vô hạn retry, không publish partial |
| NET-06 | Credential/signed URL hết hạn, endpoint trả auth/quota/lỗi provider | Resolve lại đúng asset/version theo policy và retry có giới hạn; không thay scene/provider hoặc log response chứa secret |

Allowlist phải đủ chặng data host thực của provider được chọn; không giả định hostname catalog cũng chứa mọi asset. Chưa biết provider thì giữ trạng thái thiếu cấu hình thay vì mở mọi host. Test network dùng server/transport/DNS kiểm soát trong fixture, không gọi địa chỉ metadata thật hoặc mạng nội bộ không được phép.

## Ca kiểm worker context và candidate

| ID | Tình huống | Kết quả bắt buộc |
| --- | --- | --- |
| RES-01 | Bootstrap handle/registry khác worker, descriptor schema lạ hoặc context hash khác bytes | Không accepted; không fallback sang đọc path UI hoặc context cache cũ |
| RES-02 | Context thiếu dependency, job/snapshot/hash/owner epoch sai, ID chứa path | Từ chối trước compute; không tìm lại catalog hoặc đọc DB để đoán |
| RES-03 | Context của project khác, attempt/token cũ, context replay sau restart | Từ chối start/publication theo registry đang hoạt động; không khôi phục quyền bằng ID giống nhau |
| RES-04 | Worker ghi input/model/context/DB hoặc staging của attempt khác | Resolver không cấp handle/quyền ứng dụng cho thao tác; process riêng chưa là sandbox OS nên không tuyên bố chặn mọi mã độc |
| RES-05 | Candidate ID của project/attempt khác, đường dẫn tự khai, token thu hồi | Coordinator từ chối dù file tồn tại hoặc checksum đúng; không publish cho job đang active |
| RES-06 | Candidate đúng ID nhưng file reparse/hardlink ngoài staging, bytes đổi sau gửi event hoặc thiếu file | Kiểm ownership/handle/bytes/hash lại trước commit; không phục vụ file chưa đăng ký |
| RES-07 | Worker cũ vẫn sống sau owner crash/cancel | Thu hồi token/context start, dừng/đợi process trước cấp compute mới; pin dữ liệu cần resume được giữ theo policy |
| RES-08 | Artifact model/cache dùng chung hai run | Quyền đọc/lease theo content ID và owner; đóng một context không xóa bytes run khác còn pin/lease |

## Bằng chứng cần lưu

Mỗi ca có policy version, fixture IDs/hash, process/OS khi dùng native, kết quả mong đợi/thực, exit code và log đã lọc. Dùng sentinel ngoài vùng ghi và kiểm hash trước/sau để chứng minh từ chối không làm thay đổi file đích; thêm ca dương hợp lệ để tránh đạt test bằng cách cấm mọi input. Phải phân biệt invalid input, unsupported format/policy, lỗi quyền, resource exhausted và stale attempt. Chưa có ca nào pass chỉ từ việc bảng này đã được viết.
