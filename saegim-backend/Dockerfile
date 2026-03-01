# Unified Dockerfile for saegim-backend
# Supports CPU (default) and GPU via build args
#
# Usage:
#   Dev  CPU:  docker build --target development .
#   Dev  GPU:  docker build --target development \
#                --build-arg BUILDER_IMAGE=nvidia/cuda:13.0.2-cudnn-devel-ubuntu24.04 \
#                --build-arg TORCH_EXTRA=cu130 .
#   Prod CPU:  docker build .
#   Prod GPU:  docker build \
#                --build-arg BUILDER_IMAGE=nvidia/cuda:13.0.2-cudnn-devel-ubuntu24.04 \
#                --build-arg RUNTIME_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
#                --build-arg TORCH_EXTRA=cu130 .

ARG BUILDER_IMAGE=ubuntu:noble
ARG RUNTIME_IMAGE=ubuntu:noble


# =============================================================================
# Builder stage - install dependencies and build project
# =============================================================================
FROM ${BUILDER_IMAGE} AS builder

ARG TORCH_EXTRA=cpu

# Install curl first (needed by uv installer)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

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

# Install build tools for native extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libgdbm-dev \
    libdb5.3-dev \
    libbz2-dev \
    libexpat1-dev \
    liblzma-dev \
    tk-dev \
    libffi-dev \
    libgdbm-compat-dev \
    libxmlsec1-dev \
    xz-utils \
    cmake \
    gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python via uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv python install 3.13 --compile-bytecode

WORKDIR /workspace

# Copy source code
COPY . /workspace

# Sync production dependencies into /app/.venv
# uv sync resolves all dependencies together, preventing allocator/TBB clashes
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --locked --no-dev --no-editable --extra ${TORCH_EXTRA}


# =============================================================================
# Development stage - full source with dev dependencies
# =============================================================================
FROM builder AS development

ARG TORCH_EXTRA=cpu

# Re-sync with dev dependencies into /workspace/.venv
ENV UV_PROJECT_ENVIRONMENT=/workspace/.venv
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --locked --extra ${TORCH_EXTRA}

# Set venv on PATH (no uv run needed at runtime)
ENV VIRTUAL_ENV=/workspace/.venv \
    PATH="/workspace/.venv/bin:$PATH"

# Install gosu and locales for entrypoint
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gosu \
    locales && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user (UID 10001 to avoid conflicts with host users)
RUN groupadd --gid 10001 appuser && \
    useradd -u 10001 -g 10001 -G appuser -m -s /bin/bash appuser && \
    chown -R appuser:appuser /workspace

# Copy entrypoint script (runs as root, drops to appuser via gosu)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Verify installation
RUN python -c "import sys; print(f'Python version: {sys.version}')"

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "scripts/start_server.py"]


# =============================================================================
# Production stage - minimal runtime with pre-built venv
# =============================================================================
FROM ${RUNTIME_IMAGE} AS production

# Use venv Python directly (no uv needed at runtime)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies only (no build headers)
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

# Copy Python interpreter from builder (same path ensures venv pyvenv.cfg works)
COPY --from=builder /opt/python /opt/python

# Copy pre-built venv from builder (all deps resolved together)
COPY --from=builder /app/.venv /app/.venv

WORKDIR /app

# Create directories and copy deployment files
RUN mkdir -p /app/scripts /app/storage
COPY scripts/start_server.py /app/scripts/start_server.py

# Create non-root user (UID 10001 to avoid conflicts with host users)
RUN groupadd --gid 10001 appuser && \
    useradd -u 10001 -g 10001 -G appuser -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /app/storage

# Copy entrypoint script (runs as root, drops to appuser via gosu)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Verify venv installation
RUN python -c "import sys; print(f'Python version: {sys.version}')"

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "scripts/start_server.py"]
