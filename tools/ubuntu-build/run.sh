#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
state_dir="${GEOAI_UBUNTU_STATE_DIR:-$repo_root/.venv-ubuntu-env}"
image="${GEOAI_UBUNTU_IMAGE:-geoai-ubuntu-build:22.04}"
mkdir -p "$state_dir" "$state_dir/node_modules" "$state_dir/cargo" "$state_dir/target"
ca_bundle="${SSL_CERT_FILE:-/etc/ssl/certs/ca-certificates.crt}"
args=(--init --user "$(id -u):$(id -g)" --workdir /workspace/GeoAI
    --mount "type=bind,src=$repo_root,dst=/workspace/GeoAI"
    --mount "type=bind,src=$state_dir,dst=/state"
    --mount "type=bind,src=$state_dir/node_modules,dst=/workspace/GeoAI/apps/desktop/node_modules"
    --mount "type=bind,src=$ca_bundle,dst=/run/geoai-ca.pem,readonly"
    -e CARGO_HOME=/state/cargo -e CARGO_TARGET_DIR=/state/target
    -e "CARGO_BUILD_JOBS=${CARGO_BUILD_JOBS:-2}"
    -e CARGO_HTTP_CAINFO=/run/geoai-ca.pem -e SSL_CERT_FILE=/run/geoai-ca.pem
    -e PIP_CERT=/run/geoai-ca.pem -e NODE_EXTRA_CA_CERTS=/run/geoai-ca.pem
    -e npm_config_cache=/state/npm-cache -e UV_CACHE_DIR=/state/uv-cache
    -e PYTHONPATH=/workspace/GeoAI/backend)
for proxy_var in HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy; do
    if [[ -v $proxy_var ]]; then args+=(-e "$proxy_var"); fi
done
docker_cmd=(env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH
    docker --host=unix:///var/run/docker.sock)
key="$(printf '%s' "$repo_root:$state_dir" | sha256sum | cut -c1-12)"
container="geoai-ubuntu-22-$(id -u)-$key"
image_id="$("${docker_cmd[@]}" image inspect --format '{{.Id}}' "$image")"
existing_image="$("${docker_cmd[@]}" container inspect --format '{{.Image}}' "$container" 2>/dev/null || true)"
if [[ -n $existing_image && $existing_image != "$image_id" ]]; then
    printf 'Builder image changed. After finishing active work, remove container %s and run again.\n' "$container" >&2
    exit 1
fi
if [[ -z $existing_image ]]; then
    "${docker_cmd[@]}" run -d --name "$container" "${args[@]}" "$image" sleep infinity >/dev/null
elif [[ $("${docker_cmd[@]}" inspect --format '{{.State.Running}}' "$container") != true ]]; then
    "${docker_cmd[@]}" start "$container" >/dev/null
fi
exec_args=(-i -e VIRTUAL_ENV=/state/python
    -e PATH=/state/python/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    --user "$(id -u):$(id -g)" --workdir /workspace/GeoAI)
if [[ -t 0 && -t 1 ]]; then exec_args+=(-t); fi
if [[ $# -eq 0 ]]; then set -- bash; fi
exec "${docker_cmd[@]}" exec "${exec_args[@]}" "$container" "$@"
