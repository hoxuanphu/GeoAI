#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
    docker --host=unix:///var/run/docker.sock build --platform linux/amd64 --progress plain \
    --secret "id=system_ca,src=${SSL_CERT_FILE:-/etc/ssl/certs/ca-certificates.crt}" \
    --build-arg "BUILDER_UID=$(id -u)" --build-arg "BUILDER_GID=$(id -g)" \
    -t "${GEOAI_UBUNTU_IMAGE:-geoai-ubuntu-build:22.04}" "$repo_root/tools/ubuntu-build"
