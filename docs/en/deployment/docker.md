# Docker Development Guide

## Image Builds

### Backend

The backend supports both CPU and GPU with a single multi-stage Dockerfile.
Switch modes using build ARGs.

#### CPU Mode (Default)

```bash
# Production image
docker build -t saegim-backend saegim-backend/

# Development image (includes dev dependencies)
docker build -t saegim-backend-dev --target development saegim-backend/
```

#### GPU Mode

```bash
# Production GPU image (CUDA 13.0)
docker build -t saegim-backend-gpu \
  --build-arg BASE_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
  --build-arg TORCH_EXTRA=cu130 \
  saegim-backend/

# Development GPU image
docker build -t saegim-backend-gpu-dev \
  --target development \
  --build-arg BASE_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
  --build-arg TORCH_EXTRA=cu130 \
  saegim-backend/
```

#### Build ARG Reference

| ARG | Default | Description |
| ------ | -------- | ------ |
| `BASE_IMAGE` | `ubuntu:noble` | Base image (shared across both stages) |
| `TORCH_EXTRA` | `cpu` | PyTorch extra (`cpu`, `cu126`, `cu128`, `cu130`) |

#### Build Targets (Multi-stage)

| Target | Purpose | Description |
| ------ | ------ | ------ |
| `development` | Development | Full source + dev dependencies |
| `production` | Production | Minimal runtime, production deps only |

### Frontend

```bash
docker build -t saegim-frontend \
  --build-arg VITE_API_URL=http://localhost:15000 \
  saegim-frontend/
```

- Stage 1: `oven/bun` -> Vite build
- Stage 2: `nginx:alpine` -> Static file serving
- `VITE_API_URL` is determined at **build time** (cannot be changed at runtime)

## Service Configuration

### docker-compose Services

| Service | Image | Port | Profile |
| -------- | -------- | ------ | ---------- |
| `postgres` | `postgres:18.2-trixie` | 15432->5432 | Default |
| `backend` | `Dockerfile` (CPU/GPU) | 15000->5000 | Default |
| `frontend` | `saegim-frontend` | 13000->80 | Default |
| `vllm` | `vllm-openai:v0.15.1` | 18000->8000 | `gpu` |

CPU/GPU switching for the backend image is controlled by the `BASE_IMAGE` and `TORCH_EXTRA` environment variables.
The GPU service (vLLM) is activated with `--profile gpu`.

### Network

All services are connected to the `saegim-net` bridge network.
Inter-service communication uses service names (e.g., `postgres:5432`, `backend:5000`).

### Volumes

| Volume | Path | Description |
| ------ | ------ | ------ |
| `postgres_data` | `/var/lib/postgresql` | PostgreSQL persistent data |
| `./storage` | `/workspace/storage` | PDF originals and page images |
| `vllm_cache` | `/root/.cache/huggingface` | HuggingFace model cache (GPU mode) |

### Dependency Order

```mermaid
graph LR
    PG["postgres (healthy)"] --> BE["backend (healthy)"] --> FE["frontend"]
```

- `postgres`: Backend starts after `pg_isready` healthcheck passes
- `backend`: Frontend starts after `/api/v1/health` healthcheck passes

## CPU/GPU Switching

### CPU Mode

```bash
make up
# or: docker compose up -d --build
```

### GPU Mode

```bash
make up-gpu
# or: docker compose --env-file .env --env-file .env.gpu --profile gpu up -d --build
```

In GPU mode:

1. Backend is built with a CUDA base image (`nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04`)
2. PyTorch is installed with `--extra cu130`
3. vLLM service runs additionally

### `.env.gpu` File

```bash
# GPU build settings
BASE_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04
TORCH_EXTRA=cu130
```

Modify this file to use a different CUDA version.

### GPU Prerequisites

- NVIDIA GPU driver
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### GPU Verification

```bash
# Verify GPU recognition
docker compose --profile gpu exec backend nvidia-smi
```

## Environment Variables

### Backend

| Variable | Default | Description |
| ------ | -------- | ------ |
| `DATABASE_URL` | `postgresql://labeling:labeling@postgres:5432/labeling` | DB connection URL |
| `API_HOST` | `0.0.0.0` | Bind host |
| `API_PORT` | `5000` | API port |
| `DEBUG` | `false` | Debug mode (enables Swagger UI) |
| `LOG_LEVEL` | `INFO` | Log level |
| `CORS_ORIGINS` | `["http://localhost:13000", "http://localhost:5173"]` | Allowed CORS origins |
| `STORAGE_PATH` | `./storage` | File storage path |
| `DB_POOL_MIN_SIZE` | `2` | Minimum DB connections |
| `DB_POOL_MAX_SIZE` | `10` | Maximum DB connections |
| `MAX_WORKERS` | `1` | Uvicorn worker count |
| `SECRET_KEY` | (randomly generated) | JWT signing key (must be fixed in production) |
| `REFRESH_COOKIE_SECURE` | `true` | Refresh cookie Secure flag (set to `false` for HTTP environments) |

### Frontend Environment Variables

| Variable | Default | Description |
| ------ | -------- | ------ |
| `VITE_API_URL` | `http://localhost:15000` | Backend API URL (build time) |

### vLLM Settings (GPU Mode)

| Variable | Default | Description |
| ------ | -------- | ------ |
| `VLLM_MODEL` | `prithivMLmods/chandra-FP8-Latest` | vLLM model |
| `VLLM_GPU_UTIL` | `0.9` | GPU memory utilization |
| `VLLM_MAX_SEQS` | `4` | Maximum concurrent sequences |
| `VLLM_MAX_MODEL_LEN` | `32768` | Maximum model length |
| `VLLM_MAX_BATCHED_TOKENS` | `65536` | Maximum batched tokens |
| `HF_CACHE_DIR` | `vllm_cache` (Docker volume) | HuggingFace cache path |

## Healthchecks

| Service | Endpoint | Interval |
| -------- | ----------- | ------ |
| PostgreSQL | `pg_isready -U labeling -d labeling` | 5s |
| Backend | `curl http://localhost:5000/api/v1/health` | 10s |
| vLLM | `curl http://localhost:8000/health` | 30s |
| Frontend | nginx default (port 80) | - |

## Development Tips

### Rebuilding After Code Changes

```bash
# Rebuild a specific service only
docker compose up -d --build backend

# Full rebuild (ignore cache)
docker compose build --no-cache
```

### Checking Logs

```bash
# All logs
make logs

# Specific service
docker compose logs -f backend

# Last 100 lines only
docker compose logs --tail=100 backend
```

### Direct Database Access

```bash
docker compose exec postgres psql -U labeling -d labeling
```

### Re-running Migrations

```bash
# Reset PostgreSQL data and restart
make down-all
make up
```

Migration SQL is automatically executed during PostgreSQL container initialization
(`/docker-entrypoint-initdb.d/001_init.sql`).
