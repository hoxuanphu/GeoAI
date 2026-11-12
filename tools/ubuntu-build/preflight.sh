#!/usr/bin/env bash
# Safe inventory: versions and capability probes, no environment/credential dump.
set -euo pipefail
cat /etc/os-release
id
getconf GNU_LIBC_VERSION
uname -m
node --version
npm --version
rustc --version
cargo --version
rustup component list --installed
python3.12 --version
cc --version | head -1
pkg-config --modversion webkit2gtk-4.1 gtk+-3.0 openssl librsvg-2.0
patchelf --version
command -v dpkg-deb desktop-file-validate xvfb-run dbus-run-session
stat -fc %T /sys/fs/cgroup
printf 'User manager: '
if command -v systemctl >/dev/null; then
    systemctl --user is-system-running 2>/dev/null || true
else
    printf "unavailable (build container)\n"
fi
