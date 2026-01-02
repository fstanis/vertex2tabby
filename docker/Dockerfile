FROM ubuntu:22.04 AS build

# Rust toolchain version
ARG RUST_TOOLCHAIN=stable

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    pkg-config \
    libssl-dev \
    protobuf-compiler \
    git \
    cmake \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# setup rust.
RUN curl https://sh.rustup.rs -sSf | bash -s -- --default-toolchain ${RUST_TOOLCHAIN} -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /root/workspace

RUN git clone --depth 1 "https://github.com/TabbyML/tabby" .

RUN mkdir -p /opt/tabby/bin
RUN mkdir -p /opt/tabby/lib
RUN mkdir -p target

RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/root/workspace/target \
    cargo build --no-default-features --features prod --release --package tabby && \
    cp target/release/tabby /opt/tabby/bin/

FROM ubuntu:22.04 AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    curl \
    openssh-client \
    ca-certificates \
    libssl3 \
    libgomp1 \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://pixi.sh/install.sh | sh

# Disable safe directory in docker
# Context: https://github.com/git/git/commit/8959555cee7ec045958f9b6dd62e541affb7e7d9
RUN git config --system --add safe.directory "*"

# Automatic platform ARGs in the global scope
# https://docs.docker.com/engine/reference/builder/#automatic-platform-args-in-the-global-scope
ARG TARGETARCH

RUN git clone --depth 1 "https://github.com/fstanis/vertex2tabby" /opt/vertex2tabby && \
    cd /opt/vertex2tabby && \
    "$HOME/.pixi/bin/pixi" install

COPY entrypoint.sh /opt/

COPY config.toml /opt/

COPY --from=build /opt/tabby /opt/tabby

ENV PATH="$PATH:/opt/tabby/bin"
ENV TABBY_ROOT=/data

CMD ["/opt/entrypoint.sh"]
