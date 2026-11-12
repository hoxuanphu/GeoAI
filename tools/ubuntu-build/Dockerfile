# Build environment only; this image is not the application runtime or installer.
FROM node:24-bullseye-slim@sha256:f7818cba7c85740e6f9dd31553636131d01e9992fb7d112b9b0893afd884d1d6 AS node
FROM rust:slim-bookworm@sha256:f2c004e3d2d8b547e8cf7ffbc29205385f4e71d23e53e4e383065db5e9f822cd AS rust
FROM ubuntu:22.04@sha256:076e7bf82319619f28dd0aa9c02ab34b055ad37100395b4f49a2ffba04fb5e11
ARG DEBIAN_FRONTEND=noninteractive
ARG BUILDER_UID=1000
ARG BUILDER_GID=1000
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git build-essential pkg-config clang file binutils \
    python3 python3-pip python3-venv libwebkit2gtk-4.1-dev libgtk-3-dev \
    libssl-dev librsvg2-dev libxdo-dev patchelf xdg-utils desktop-file-utils \
    dbus-x11 xvfb xauth && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
COPY --from=rust /usr/local/rustup /opt/rustup
COPY --from=rust /usr/local/cargo/bin /usr/local/bin
ENV RUSTUP_HOME=/opt/rustup
RUN --mount=type=secret,id=system_ca,required=true \
    PIP_CERT=/run/secrets/system_ca python3 -m pip install --no-cache-dir uv==0.13.7
RUN --mount=type=secret,id=system_ca,required=true \
    SSL_CERT_FILE=/run/secrets/system_ca uv python install --install-dir /opt/python 3.12.16 && \
    UV_PYTHON_INSTALL_DIR=/opt/python uv python find --managed-python 3.12.16 > /tmp/python-path && \
    ln -s "$(cat /tmp/python-path)" /usr/local/bin/python3.12 && rm /tmp/python-path
RUN groupadd -g "$BUILDER_GID" builder && \
    useradd -m -u "$BUILDER_UID" -g "$BUILDER_GID" -s /bin/bash builder
USER builder
ENV UV_PYTHON_INSTALL_DIR=/opt/python
WORKDIR /workspace/GeoAI
CMD ["bash"]
