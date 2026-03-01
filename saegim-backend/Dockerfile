# Unified Dockerfile for saegim-backend
# Supports CPU (default) and GPU via build args
#
# Usage:
#   Dev  CPU:  docker build --target development .
#   Dev  GPU:  docker build --target development \
#                --build-arg BASE_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
#                --build-arg TORCH_EXTRA=cu130 .
#   Prod CPU:  docker build .
#   Prod GPU:  docker build \
#                --build-arg BASE_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
#                --build-arg TORCH_EXTRA=cu130 .

ARG BASE_IMAGE=ubuntu:noble


# =============================================================================
# Development stage - full source with dev dependencies
# =============================================================================
FROM ${BASE_IMAGE} AS development

ARG TORCH_EXTRA=cpu

# Install system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    wget \
    gosu \
    locales && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true \
    TZ=Asia/Seoul \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    SHELL=/bin/bash \
    MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install Python via uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv python install 3.13 --compile-bytecode

WORKDIR /workspace
COPY . /workspace

# Sync all dependencies (including dev)
ENV UV_PROJECT_ENVIRONMENT=/workspace/.venv
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --locked --extra ${TORCH_EXTRA}

ENV VIRTUAL_ENV=/workspace/.venv \
    PATH="/workspace/.venv/bin:$PATH"

# Create non-root user (UID 10001 to avoid conflicts with host users)
RUN groupadd --gid 10001 appuser && \
    useradd -u 10001 -g 10001 -G appuser -m -s /bin/bash appuser && \
    chown -R appuser:appuser /workspace

# Copy entrypoint script (runs as root, drops to appuser via gosu)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

RUN python -c "import sys; print(f'Python version: {sys.version}')"

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "scripts/start_server.py"]


# =============================================================================
# Production stage - wheel install, no source code
# =============================================================================
FROM ${BASE_IMAGE} AS production

ARG TORCH_EXTRA=cpu

# Install runtime packages only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gosu \
    locales \
    libgomp1 \
    libzstd1 && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    rm -rf /var/lib/apt/lists/*

# Install uv (used for sync, can be removed after)
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install Python via uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv python install 3.13 --compile-bytecode

# Copy source, build wheel + install deps, then remove source
COPY . /tmp/src
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN --mount=type=cache,target=/tmp/uv-cache \
    cd /tmp/src && \
    uv sync --locked --no-dev --no-editable --extra ${TORCH_EXTRA} && \
    rm -rf /tmp/src

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy deployment files
RUN mkdir -p /app/scripts /app/storage
COPY scripts/start_server.py /app/scripts/start_server.py
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user (UID 10001 to avoid conflicts with host users)
# Only chown storage (write-needed); venv and scripts are read-only at runtime
RUN groupadd --gid 10001 appuser && \
    useradd -u 10001 -g 10001 -G appuser -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app/storage

RUN python -c "import sys; print(f'Python version: {sys.version}')"

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "scripts/start_server.py"]
