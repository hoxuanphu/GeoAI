# Ubuntu22 debug shell preview

Command: tools/ubuntu-build/run.sh bash tools/ubuntu-build/build-preview.sh
Private Ubuntu22.04.5 amd64 builder, GTK3/WebKitGTK4.1/Rust1.99.1/Tauri2.
Build and dpkg install exit0 (build.log/install.log). Installed executable stayed
alive eight seconds under Xvfb/dbus before intentional timeout124. AT-SPI bus
warning is retained in runtime.log; this is not rendered UI or accessibility proof.

Artifact: .venv-ubuntu-env/target/debug/bundle/deb/GeoAI_0.1.0_amd64.deb,
46.88MiB, SHA256 877f64d1f3d501637ad66177bb31765fa41abe26febec6a5bb91ab4055fea0d3.
Package geo-ai 0.1.0 amd64 depends on GTK3/WebKitGTK4.1. No maintainer scripts;
placeholder Tauri icon license/notice included. Not installed on host.

This artifact predates B-01 and packages the existing desktop shell only. Linux
bootstrap still returns windows_required; no Python runtime/backend is included.
No real user-manager/ext4, clean-machine/offline/upgrade, Wayland or native job
flow acceptance; G3 is open. Rebuild after foundation integration before claiming
an artifact corresponding to latest source. Cached package is ignored and internal.
