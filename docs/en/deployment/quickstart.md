# Quick Start

This guide explains how to run the entire saegim stack (PostgreSQL + Backend + Frontend) at once using Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/install/) v2+

## Running

### 1. Set Environment Variables

```bash
cp .env.example .env
```

Modify the `.env` file as needed:

| Variable | Default | Description |
| ------ | -------- | ------ |
| `DB_PASSWORD` | `labeling` | PostgreSQL password |
| `VITE_API_URL` | `http://localhost:15000` | Backend API URL called by the frontend |
| `API_PORT` | `15000` | Backend host port |
| `FE_PORT` | `13000` | Frontend host port |
| `PG_PORT` | `15432` | PostgreSQL host port |

### 2. Run in CPU Mode (Default)

```bash
make up
# or: docker compose up -d --build
```

Startup order: PostgreSQL -> Backend (after healthcheck passes) -> Frontend

### 3. Run in GPU Mode

To use GPU services (vLLM) in an environment with an NVIDIA GPU:

```bash
make up-gpu
# or: docker compose --env-file .env --env-file .env.gpu --profile gpu up -d --build
```

!!! note
    In GPU mode, the backend is built with a CUDA 13.0 image,
    and the vLLM service runs additionally.
    [NVIDIA Container Toolkit][nvidia-toolkit] must be installed.

[nvidia-toolkit]: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

You can change GPU build settings in `.env.gpu`:

| Variable | Default | Description |
| ------ | -------- | ------ |
| `BASE_IMAGE` | `nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04` | Base image (shared across both stages) |
| `TORCH_EXTRA` | `cu130` | PyTorch CUDA version (`cpu`, `cu126`, `cu128`, `cu130`) |

## Verifying Access

| URL | Description |
| ----- | ------ |
| <http://localhost:13000> | Frontend (Web UI) |
| <http://localhost:15000/api/v1/health> | Backend healthcheck |
| <http://localhost:15000/docs> | Swagger UI (when `DEBUG=true`) |
| `localhost:15432` | PostgreSQL (external access) |

### Healthcheck

```bash
# Check backend status
curl http://localhost:15000/api/v1/health

# Check service status
make ps
# or: docker compose ps -a
```

## Stopping and Cleanup

```bash
# Stop CPU mode (preserve data)
make down

# Stop GPU mode (preserve data)
make down-gpu

# Stop services + delete data (including PostgreSQL data)
make down-all

# Stop GPU mode + delete data
make down-all-gpu
```

## Troubleshooting

### Port Conflicts

If the default ports are already in use, change them in the `.env` file:

```bash
API_PORT=25000
FE_PORT=23000
PG_PORT=25432
```

### Backend Startup Failure

```bash
# Check logs
docker compose logs backend

# Check PostgreSQL status
docker compose logs postgres
```

### Rebuilding Images

To update images after code changes:

```bash
make up
# or: docker compose up -d --build
```

## Makefile Command Summary

| Command | Description |
| ------ | ------ |
| `make up` | Build + run in CPU mode |
| `make down` | Stop CPU mode (preserve data) |
| `make down-all` | Stop CPU mode + delete data |
| `make up-gpu` | Build + run in GPU mode |
| `make down-gpu` | Stop GPU mode (preserve data) |
| `make down-all-gpu` | Stop GPU mode + delete data |
| `make build` | Build CPU images only |
| `make build-gpu` | Build GPU images only |
| `make logs` | Stream logs |
| `make ps` | Check service status |

## Next Steps

- [Docker Development Guide](docker.md) - Image builds, GPU profile details
- [Kubernetes Deployment Guide](kubernetes.md) - Cluster deployment
