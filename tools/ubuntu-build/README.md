# Ubuntu 22.04 build environment

Run from the repository root. Docker must be running and accessible to the current user.

```bash
tools/ubuntu-build/build-image.sh
tools/ubuntu-build/run.sh bash tools/ubuntu-build/setup.sh
tools/ubuntu-build/run.sh bash
```

The image targets amd64 and contains Ubuntu 22.04, GTK 3/WebKitGTK 4.1 development libraries, OpenSSL, librsvg, libxdo, a C/C++ compiler, Rust/Cargo 1.99.1, Node 24.20/npm 11.19 and managed CPython 3.12.16. Base images are pinned by resolved digest; uv is pinned to 0.13.7. Python 3.10 supplied by Ubuntu is preserved. Xvfb and session D-Bus support future headless GUI smoke tests.

Commands execute as the current user's UID/GID in a reusable container named `geoai-ubuntu-22-<uid>-<workspace-key>`. This avoids repeated image copies with the Cloud vfs driver. If the image changes, the wrapper asks you to finish active commands and remove the old named container before recreating it. It never replaces an active builder automatically. The repository is mounted at `/workspace/GeoAI`. Dependencies and compiler cache are isolated in the ignored `.venv-ubuntu-env/` directory; host `.venv` and host `node_modules` are preserved. The wrapper activates `/state/python` through PATH/VIRTUAL_ENV, so `python` and `python3` use CPython 3.12 after setup. `/usr/bin/python3` remains Ubuntu's system interpreter. `PYTHONPATH` points to the mounted backend. System packages are installed only while building the image.

Examples:

```bash
tools/ubuntu-build/run.sh /state/python/bin/python -m unittest discover -s tests/contracts -v
tools/ubuntu-build/run.sh bash -c 'cd apps/desktop && npm test && npm run build'
tools/ubuntu-build/run.sh cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml
```

`GEOAI_UBUNTU_IMAGE` overrides the image tag; `GEOAI_UBUNTU_STATE_DIR` overrides the absolute state directory. Keep different state directories for different OS/toolchain profiles. Re-run `setup.sh` after dependency changes. Build scripts mount the configured system CA bundle and forward inherited HTTP proxy settings with TLS verification enabled; they do not store credentials or session certificates in the image.

This prepares compilation and packaging tools. It does not enable Linux backend execution, change capabilities, configure a release `.deb`, or provide a systemd user manager, Ubuntu Desktop VM, Wayland or Windows acceptance. A container shares the host kernel; full lifecycle and clean-machine acceptance still need suitable Ubuntu 22.04/24.04 executors.

Run `tools/ubuntu-build/run.sh bash tools/ubuntu-build/verify.sh` to record separate statuses/logs for preflight, backend suites, generated artifacts, frontend, Xvfb/D-Bus and Cargo check. Any failed command returns an overall nonzero status; Windows-only skips are not native acceptance. Logs are kept under the local state directory.

Build the current desktop shell preview as a debug `.deb` on Ubuntu 22.04:

```bash
tools/ubuntu-build/run.sh bash tools/ubuntu-build/build-preview.sh
```

The package is written under `.venv-ubuntu-env/target/debug/bundle/deb/`. It contains the current shell and embedded frontend, not the Python runtime or Linux execution backend. It is an internal development preview with the temporary Tauri icon; packaging does not close SPEC-010 or G3. The configuration override leaves the main Windows/release bundle config unchanged. The icon's source/license notices are included as package resources.
