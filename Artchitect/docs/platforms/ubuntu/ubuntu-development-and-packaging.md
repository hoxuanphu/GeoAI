# Ubuntu: môi trường phát triển và phương án đóng gói

**Ngày:** 10/11/2026. **Mục tiêu:** Ubuntu 22.04 LTS và Ubuntu 24.04 LTS. **Trạng thái:** hướng dẫn chuẩn bị/kiểm trong tương lai, chưa là hướng dẫn cài sản phẩm đã phát hành. Chưa có runtime Linux, `.deb` hoặc kết quả Linux/Cloud trong đợt này.

Đọc [ADR-012](../../adr/ADR-012-ubuntu-desktop.md), [kiến trúc Ubuntu](ubuntu-desktop-architecture.md), [ma trận kiểm](ubuntu-validation-matrix.md) và [hướng dẫn dev chung](../../guides/development-guide.md). Các lệnh Bash dưới đây chỉ là quy trình dự kiến cho executor Ubuntu; **không được chạy trong đợt tài liệu trên Windows**.

Gen code foundation theo [SPEC-010](../../specs/010-ubuntu-foundation.md), [native profile](ubuntu-native-profile.md) và [interface adapter](ubuntu-adapter-interfaces.md). Profile kỹ thuật chọn Python 3.12 riêng, x86_64/ext4 và hai LTS để kiểm; patch/toolchain/dependency lock chỉ khóa từ resolve thực. Foundation chưa nghiệm thu `.deb` hoặc G3.

## 1. Profile cần chuẩn bị

| Thành phần | Yêu cầu/đề xuất | Cần khóa bằng bằng chứng |
| --- | --- | --- |
| OS/CPU | Cả 22.04 LTS và 24.04 LTS; amd64/x86_64 là profile đề xuất đầu | Point release, kernel, image digest/VM snapshot, filesystem/mount |
| Desktop | WebKitGTK 4.1, GTK, session D-Bus, user manager/cgroup | Package version, X11/Wayland, Mesa/GPU; mỗi session type kiểm riêng |
| Python | Repo yêu cầu `>=3.12`; runtime riêng cho sidecar/worker | Chọn phiên bản cụ thể từ resolve thực; native library/data và hash pack |
| Frontend | Node/npm đáp ứng engines của Vite/Vitest đã resolve; dùng `package-lock.json` hiện có | Node/npm version, lock hash, DOM/typecheck/build |
| Rust/Tauri | Toolchain đáp ứng crate/MSRV thực, target Linux tương ứng | Rust/Cargo/CLI version, Cargo.lock khi resolve thật, build provenance |
| GIS/PDF/offline | GDAL/PROJ/database/grid, codec, Typst/font, laz-perf WASM theo task | Inventory/license/hash và đường tra cứu giới hạn trong pack |
| AI | CPU theo profile Prithvi; CUDA/NVIDIA là pack riêng | ORT/PyTorch/runtime/driver tương thích và output/benchmark theo gate |

Không thay `/usr/bin/python3` hoặc ghi package vào Python hệ thống để đạt `>=3.12`. Dev có thể dùng môi trường cô lập; sản phẩm cần runtime riêng, không đòi khách hàng cài Python/Node/Rust. Chọn portable environment hay PyInstaller onedir theo ADR-006 bằng fixture; chưa có quyết định freeze cuối. Không viết lockfile giả hoặc tự bỏ pin để resolve thành công.

## 2. Preflight trên executor thực

Chạy trong checkout có đúng revision và thay đổi local cần kiểm. Ghi exit code từng lệnh, lọc user path/hostname không cần thiết khỏi bằng chứng chia sẻ. Không dump toàn bộ environment.

```bash
cat /etc/os-release
uname -m
uname -r
getconf GNU_LIBC_VERSION
python3 --version
node --version
npm --version
rustc --version
cargo --version
pkg-config --modversion webkit2gtk-4.1
systemctl --user is-system-running
stat -fc %T /sys/fs/cgroup
```

Python hệ thống hiện ra ở preflight chỉ để nhận diện môi trường; suite phải dùng interpreter của runtime đã chọn và ghi `sys.executable`/version đã lọc path. Container có thể không có `systemctl --user`, display, D-Bus hoặc GPU: vẫn có thể chạy kiểm thuần, nhưng native/desktop được ghi chưa kiểm. Không yêu cầu bật systemd/privileged Docker chỉ để sửa màu trạng thái test.

Dev/build cần các package hệ thống theo Tauri và package resolver của LTS. Danh sách khởi điểm từ upstream gồm `build-essential`, `pkg-config`, `libwebkit2gtk-4.1-dev`, `libssl-dev`, `librsvg2-dev`, `libxdo-dev`; indicator chỉ khi app dùng tính năng tương ứng. `curl`/`wget` là công cụ tải tùy quy trình, không là dependency runtime bắt buộc. Package index của cả hai LTS có WebKitGTK 4.1 dev; repository/component và quyền cài phải được preflight, không giả đã cấu hình. Danh sách này chưa là dependency lock hoặc xác nhận apt install đã chạy.

## 3. Kiểm backend/frontend và điều kiện build native

Sau khi đã restore đủ dependency vào môi trường đã khóa, các lệnh repo hiện có có thể dùng làm khởi điểm:

```bash
PYTHONPATH=backend python -m unittest discover -s tests/contracts -v
PYTHONPATH=backend python tools/export_contract_schemas.py --check
PYTHONPATH=backend python tools/export_api_client.py --check
PYTHONPATH=backend python -m unittest discover -s tests/storage -v
PYTHONPATH=backend python -m unittest discover -s tests/integration -v
PYTHONPATH=backend python -m unittest discover -s tests/architecture -v
```

Trong `apps/desktop`, dùng các script hiện có:

```bash
npm ci
npm test
npm run typecheck
npm run build
```

Suite Windows có thể skip hoặc lỗi import khi đưa sang Linux; phải lưu đúng pass/fail/skip và phân loại để sửa trong task adapter. Không tắt cả suite native hoặc biến skip thành bằng chứng Linux pass. Exporter `--check` chỉ kiểm artifact hiện hành, không chứng minh nội dung native context đã đúng trên Linux.

`npm run build` chỉ là frontend. Chỉ thử `npm run tauri -- build` sau khi adapter/entrypoint Linux, supervisor/bootstrap, FD transport và cấu hình sidecar đã được triển khai theo SPEC-003/009. Hiện nhánh non-Windows trả `windows_required`, `bundle.active=false`; đổi cờ bundle không làm app tương thích. Tạo `.deb` còn cần cấu hình bundle/resource/sidecar, dependency và metadata đã kiểm; không phát hành scaffold.

## 4. Phương án `.deb` và kiểm ABI

1. Build từ Ubuntu 22.04 với toolchain/runtime được resolve thực; ghi image digest và dependency inventory. Native Python/GDAL/ORT/Typst hoặc tool tải sẵn cũng phải có ABI phù hợp, không chỉ binary Rust.
2. So portable environment với freeze onedir bằng fixture có GIS/model/PDF khi đủ dependency. Kiểm dynamic loader, `.so`, RPATH/RUNPATH, font, PROJ grids, certificate trust và plugin path; không dựa `LD_LIBRARY_PATH`/cache trên máy build. Bootstrap không nhận `LD_PRELOAD`, `PYTHONPATH` hay plugin search path không tin cậy từ project.
3. Kiểm ELF architecture và symbol requirements bằng `file`/`readelf`, inventory dependency bằng công cụ pack/build. Không dùng `ldd` để thăm dò binary không tin cậy. Kiểm cả sidecar và mọi native extension, không chỉ executable ngoài cùng.
4. `.deb` khai dependency thực theo LTS; `libwebkit2gtk-4.1-dev` là package build, không ép khách hàng cài toàn bộ `-dev`. Thư viện runtime GTK/WebKitGTK và chuyển đổi tên/ABI như `t64` phải được resolver kiểm trên cả hai LTS. Build trên 22.04 chỉ giảm rủi ro glibc, không bảo đảm một gói chạy được cả hai. Nếu không thể dùng một gói thì tách artifact theo LTS và ghi rõ.
5. Gói app không ghi project/cache vào thư mục cài; không chạy app/coordinator bằng root từ maintainer script. Runtime không sửa dependency hệ thống, không cài CUDA driver, không bật service toàn máy hoặc lingering.
6. Artifact có SHA-256, manifest/version/license/SBOM và provenance build; chữ ký/kênh cập nhật cần quy trình phát hành riêng. Model pack kiểm nguồn, license, decoder/profile/evaluation và tương thích, không tự tải weights ở lần mở đầu.

`.deb` là đề xuất ưu tiên cho hai Ubuntu LTS; AppImage/Flatpak không được dùng để tuyên bố hết vấn đề ABI, portal hoặc containment. Chưa đặt tên file sản phẩm, URL tải, dung lượng hay support matrix giả.

## 5. Máy sạch, offline, nâng cấp và gỡ

| Tình huống | Kiểm cần thực hiện trước công bố |
| --- | --- |
| Cài online | VM desktop sạch từng LTS, tài khoản thường chạy app, chỉ quyền cài gói dùng quản trị; không có môi trường dev/Python/Rust cài sẵn |
| Cài offline | Ngoài app/model/runtime pack phải có đầy đủ dependency OS hợp lệ và cách cấp từ media/repo offline tin cậy; kiểm chữ ký/license/version; ngắt mạng từ trước install và launch |
| Chạy offline | Bản đồ/COG/COPC, WASM, font/PDF, PROJ grids, TLS resources và model không cần CDN/download ngầm; tách thiếu dữ liệu nền khỏi thiếu runtime |
| Nâng cấp | Dừng/drain workload, backup SQLite nhất quán và artifact inventory trước migration; không update binary dưới process đang chạy; thử interruption/disk-full |
| Rollback/restore | Binary cũ không mở DB mới tùy ý; restore backup đã kiểm hoặc migration ngược đã được thiết kế; không hứa downgrade tự động |
| Gỡ/purge | Dừng workload thuộc app theo danh tính đã xác minh; giữ project/model/input của người dùng theo policy; xóa dữ liệu người dùng chỉ bằng thao tác riêng có chủ đích |
| Chuyển Windows–Ubuntu | Export/import bundle/backup đã kiểm, case/Unicode/relative refs/license/CRS; không copy `.db` đang mở hoặc context/session/token |

Các bước trên là tiêu chí phát triển và phát hành, chưa là hướng dẫn người dùng cuối có thể làm với build hiện tại. Container không thay VM máy sạch, Xvfb không thay Wayland/hardware GPU, và kiểm CPU không thay nghiệm thu NVIDIA. G3 chỉ đóng theo hồ sơ phát hành riêng; không kéo toàn bộ nghiệm thu bộ cài vào kết quả schema/Cloud.

<a id="nguồn-đã-đối-chiếu"></a>

## 6. Nguồn đã đối chiếu

Đọc ngày **10/11/2026**; các nguồn mô tả primitive/upstream, không chứng minh GeoAI đã chạy:

- [Tauri 2 — Debian](https://v2.tauri.app/distribute/debian/): build trên nền cũ nhất có WebKitGTK 4.1, ví dụ Ubuntu 22.04; chú ý glibc.
- [Tauri 2 — prerequisites](https://v2.tauri.app/start/prerequisites/): dependency build Linux.
- [Ubuntu Jammy](https://packages.ubuntu.com/jammy/libwebkit2gtk-4.1-dev) và [Ubuntu Noble](https://packages.ubuntu.com/noble/libwebkit2gtk-4.1-dev): package WebKitGTK 4.1 dev; phiên bản security/update phải ghi từ executor thực.
- [systemd v249 — service](https://github.com/systemd/systemd/blob/v249/man/systemd.service.xml) và [kill](https://github.com/systemd/systemd/blob/v249/man/systemd.kill.xml): main-process lifecycle và dọn control group; dùng bản upstream theo tag để tránh mặc định dựa tính năng mới. Các URL man/249 trên freedesktop timeout trong lượt kiểm, đã đọc raw XML cùng tag từ upstream.
- [XDG Base Directory](https://specifications.freedesktop.org/basedir/latest/): config/data/state/cache/runtime và quyền runtime directory.
- [Linux man-pages — flock](https://man7.org/linux/man-pages/man2/flock.2.html), [openat2](https://man7.org/linux/man-pages/man2/openat2.2.html), [fsync](https://man7.org/linux/man-pages/man2/fsync.2.html): advisory lock, giải quyết path theo directory FD và durability. Chỉ dùng flag có trên kernel mục tiêu đã probe; không lấy toàn bộ tính năng trong man-page mới làm baseline LTS.

## Chuẩn bị executor build trong Cloud 11/11/2026

Theo yêu cầu ưu tiên chuẩn bị bản build Ubuntu, đã thêm bộ công cụ tại `tools/ubuntu-build/`. Host Cloud hiện là Debian 13; image Docker dùng Ubuntu 22.04 làm nền biên dịch glibc cũ nhất trong phạm vi dự kiến. Xem [hướng dẫn builder](../../../../tools/ubuntu-build/README.md).

Chạy từ root repository:

```bash
tools/ubuntu-build/build-image.sh
tools/ubuntu-build/run.sh bash tools/ubuntu-build/setup.sh
tools/ubuntu-build/run.sh bash tools/ubuntu-build/preflight.sh
tools/ubuntu-build/run.sh cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml
```

Đây là chuẩn bị/kiểm compiler và thư viện cho shell, có thể thực hiện trước khi hoàn tất A-01. Không đổi acceptance của backend/worker/lifecycle hoặc công bố gói runtime đã sẵn sàng. Container không thay Ubuntu Desktop/systemd user manager, Windows regression hoặc kiểm máy sạch. `.venv-ubuntu-env/` là state local đã được gitignore; script không thay Python/Node dependency đang dùng trên host.

Kết quả chạy thực và giới hạn của executor: [bàn giao 11/11/2026](../../evidence/ubuntu-build-environment-2026-11-11/handoff.md). Cargo check/native-link pass; chưa tạo installer hoặc nghiệm thu runtime Linux.

### Runner foundation hiện có (11/11/2026)

Hai script không cài dependency hoặc chạy bootstrap để thu descriptor. Chọn directory
mới cho từng lần chạy; preflight và runner được dùng chung directory có marker của task,
nhưng từ chối ghi đè `env.json`/`results.json` hoặc hồ sơ lịch sử không có marker.
Ví dụ trong builder Ubuntu 22.04 đã chuẩn bị:

```bash
tools/ubuntu-build/run.sh python tools/ubuntu_foundation_preflight.py --output Artchitect/docs/evidence/ubuntu-foundation-2026-11-11/A-05/ubuntu22-reviewed-baseline
tools/ubuntu-build/run.sh python tools/ubuntu_foundation_check.py --layer portable --output Artchitect/docs/evidence/ubuntu-foundation-2026-11-11/A-05/ubuntu22-reviewed-baseline
```

`portable` chạy sáu suite Python bằng unittest result object, schema/API exporter,
`pip check`, frontend test và build. `results.json` chỉ giữ exit/counts/skip và reason code; không lưu raw stdout/stderr,
argv hoặc môi trường của process. Khi cần chẩn đoán lỗi, chạy riêng check tương ứng. Layer native/desktop chưa được runner cung cấp; nhập các layer đó bị lỗi input,
không chuyển về portable. Cargo/native-link/Xvfb vẫn dùng `tools/ubuntu-build/verify.sh`
cho kiểm build riêng, không suy native acceptance từ portable hoặc container.
