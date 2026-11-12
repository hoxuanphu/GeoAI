#!/usr/bin/env bash
# Run through run.sh; preserve each command's status, including known baseline failures.
set -uo pipefail
cd /workspace/GeoAI || exit 1
output="$(mktemp -d /state/verify-XXXXXXXX)" || exit 1
printf 'Evidence directory: %s\n' "$output"
failed=0
check() {
    local name="$1" status
    shift
    "$@" >"$output/$name.log" 2>&1
    status=$?
    printf '%s exit=%s\n' "$name" "$status" | tee -a "$output/status.txt"
    tail -5 "$output/$name.log"
    if [[ $status -ne 0 ]]; then failed=1; fi
}
check preflight bash tools/ubuntu-build/preflight.sh
for suite in contracts integration architecture catalog storage jobs; do
    check "$suite" /state/python/bin/python -m unittest discover -s "tests/$suite" -v
done
check schemas /state/python/bin/python tools/export_contract_schemas.py --check
check api-client /state/python/bin/python tools/export_api_client.py --check
check pip /state/python/bin/python -m pip check
check frontend-tests npm --prefix apps/desktop test
check frontend-build npm --prefix apps/desktop run build
check display xvfb-run -a dbus-run-session -- bash -c 'test -n "$DISPLAY" && test -n "$DBUS_SESSION_BUS_ADDRESS"'
check native-link bash -c 'cc tools/ubuntu-build/native-deps-smoke.c -o /state/native-deps-smoke $(pkg-config --cflags --libs webkit2gtk-4.1) && xvfb-run -a dbus-run-session -- /state/native-deps-smoke'
check cargo-check cargo check --locked --manifest-path apps/desktop/src-tauri/Cargo.toml
exit "$failed"
