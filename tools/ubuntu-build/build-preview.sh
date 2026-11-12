#!/usr/bin/env bash
# Build only the current shell preview; Linux native backend is still unavailable.
set -euo pipefail
cd /workspace/GeoAI/apps/desktop
npm run tauri -- build --debug --ci --bundles deb --config '{"bundle":{"active":true,"targets":["deb"],"shortDescription":"GeoAI desktop foundation preview","longDescription":"Development preview of the GeoAI desktop shell. Native Linux backend execution is not available in this build.","icon":["icons/icon.png"],"resources":{"icons/LICENSE_APACHE-2.0":"third-party/tauri-icon/LICENSE_APACHE-2.0","icons/README.md":"third-party/tauri-icon/README.md"}}}' -- --locked
