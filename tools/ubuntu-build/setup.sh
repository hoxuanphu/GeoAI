#!/usr/bin/env bash
# Run inside the Ubuntu builder using run.sh.
set -euo pipefail
cd /workspace/GeoAI
if [[ ! -x /state/python/bin/python ]]; then
    uv venv --python /usr/local/bin/python3.12 /state/python
fi
uv pip install --python /state/python/bin/python -e '.[api,test,db]'
/state/python/bin/python -m ensurepip
/state/python/bin/python -m pip check
cd apps/desktop
npm ci
npm run tauri -- --version
cargo fetch --manifest-path src-tauri/Cargo.toml
