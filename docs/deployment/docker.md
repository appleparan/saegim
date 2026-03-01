# Docker 개발 가이드

## 이미지 빌드

### 백엔드

백엔드는 단일 멀티스테이지 Dockerfile로 CPU/GPU 모두 지원합니다.
빌드 ARG로 모드를 전환합니다.

#### CPU 모드 (기본)

```bash
# 프로덕션 이미지
docker build -t saegim-backend saegim-backend/

# 개발 이미지 (dev 의존성 포함)
docker build -t saegim-backend-dev --target development saegim-backend/
```

#### GPU 모드

```bash
# 프로덕션 GPU 이미지 (CUDA 13.0)
docker build -t saegim-backend-gpu \
  --build-arg BUILDER_IMAGE=nvidia/cuda:13.0.2-cudnn-devel-ubuntu24.04 \
  --build-arg RUNTIME_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
  --build-arg TORCH_EXTRA=cu130 \
  saegim-backend/

# 개발 GPU 이미지
docker build -t saegim-backend-gpu-dev \
  --target development \
  --build-arg BUILDER_IMAGE=nvidia/cuda:13.0.2-cudnn-devel-ubuntu24.04 \
  --build-arg TORCH_EXTRA=cu130 \
  saegim-backend/
```

#### 빌드 ARG 설명

| ARG | 기본값 | 설명 |
| ------ | -------- | ------ |
| `BUILDER_IMAGE` | `ubuntu:noble` | 빌더 스테이지 베이스 이미지 |
| `RUNTIME_IMAGE` | `ubuntu:noble` | 프로덕션 런타임 베이스 이미지 |
| `TORCH_EXTRA` | `cpu` | PyTorch extra (`cpu`, `cu126`, `cu128`, `cu130`) |

#### 빌드 타겟 (Multi-stage)

| 타겟 | 용도 | 설명 |
| ------ | ------ | ------ |
| `builder` | 중간 | 빌드 도구 + uv sync (프로덕션 deps) |
| `development` | 개발 | builder 기반, 전체 소스 + dev 의존성 |
| `production` | 운영 | 최소 런타임, builder에서 venv 복사 |

### 프론트엔드

```bash
docker build -t saegim-frontend \
  --build-arg VITE_API_URL=http://localhost:15000 \
  saegim-frontend/
```

- Stage 1: `oven/bun` → Vite 빌드
- Stage 2: `nginx:alpine` → 정적 파일 서빙
- `VITE_API_URL`은 **빌드 시점**에 결정됨 (런타임 변경 불가)

## 서비스 구성

### docker-compose 서비스

| 서비스 | 이미지 | 포트 | 프로파일 |
| -------- | -------- | ------ | ---------- |
| `postgres` | `postgres:18.2-trixie` | 15432→5432 | 기본 |
| `backend` | `Dockerfile` (CPU/GPU) | 15000→5000 | 기본 |
| `frontend` | `saegim-frontend` | 13000→80 | 기본 |
| `ppstructure` | PaddlePaddle | 18811 | `gpu` |
| `vllm` | `vllm-openai:v0.15.1` | 18000→8000 | `gpu` |

백엔드 이미지의 CPU/GPU 전환은 `BUILDER_IMAGE`, `RUNTIME_IMAGE`, `TORCH_EXTRA` 환경변수로 제어합니다.
GPU 서비스(vLLM, ppstructure)는 `--profile gpu`으로 활성화합니다.

### 네트워크

모든 서비스는 `saegim-net` 브릿지 네트워크에 연결됩니다.
서비스 간 통신은 서비스 이름으로 접근합니다 (예: `postgres:5432`, `backend:5000`).

### 볼륨

| 볼륨 | 경로 | 설명 |
| ------ | ------ | ------ |
| `postgres_data` | `/var/lib/postgresql` | PostgreSQL 영구 데이터 |
| `./storage` | `/workspace/storage` | PDF 원본 및 페이지 이미지 |
| `vllm_cache` | `/root/.cache/huggingface` | HuggingFace 모델 캐시 (GPU 모드) |

### 의존성 순서

```text
postgres (healthy) → backend (healthy) → frontend
```

- `postgres`: `pg_isready` healthcheck 통과 후 backend 시작
- `backend`: `/api/v1/health` healthcheck 통과 후 frontend 시작

## CPU/GPU 전환

### CPU 모드

```bash
make up
# 또는: docker compose up -d --build
```

### GPU 모드

```bash
make up-gpu
# 또는: docker compose --env-file .env --env-file .env.gpu --profile gpu up -d --build
```

GPU 모드에서는:

1. 백엔드가 CUDA 베이스 이미지로 빌드됨 (`nvidia/cuda:13.0.2-cudnn-*`)
2. PyTorch가 `--extra cu130`으로 설치됨
3. vLLM과 PP-StructureV3 서비스가 추가 실행됨

### `.env.gpu` 파일

```bash
# GPU build settings
BUILDER_IMAGE=nvidia/cuda:13.0.2-cudnn-devel-ubuntu24.04
RUNTIME_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04
TORCH_EXTRA=cu130
```

다른 CUDA 버전을 사용하려면 이 파일을 수정합니다.

### GPU 사전 요구사항

- NVIDIA GPU 드라이버
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### GPU 확인

```bash
# GPU 인식 확인
docker compose --profile gpu exec backend nvidia-smi
```

## 환경 변수

### 백엔드

| 변수 | 기본값 | 설명 |
| ------ | -------- | ------ |
| `DATABASE_URL` | `postgresql://labeling:labeling@postgres:5432/labeling` | DB 연결 URL |
| `API_HOST` | `0.0.0.0` | 바인드 호스트 |
| `API_PORT` | `5000` | API 포트 |
| `DEBUG` | `false` | 디버그 모드 (Swagger UI 활성화) |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `CORS_ORIGINS` | `["http://localhost:13000", "http://localhost:5173"]` | 허용 CORS 오리진 |
| `STORAGE_PATH` | `./storage` | 파일 저장 경로 |
| `DB_POOL_MIN_SIZE` | `2` | 최소 DB 커넥션 |
| `DB_POOL_MAX_SIZE` | `10` | 최대 DB 커넥션 |
| `MAX_WORKERS` | `1` | Uvicorn 워커 수 |

### 프론트엔드 환경변수

| 변수 | 기본값 | 설명 |
| ------ | -------- | ------ |
| `VITE_API_URL` | `http://localhost:15000` | 백엔드 API URL (빌드 시점) |

### vLLM 설정 (GPU 모드)

| 변수 | 기본값 | 설명 |
| ------ | -------- | ------ |
| `VLLM_MODEL` | `richarddavison/chandra-fp8` | vLLM 모델 |
| `VLLM_GPU_UTIL` | `0.9` | GPU 메모리 사용률 |
| `VLLM_MAX_SEQS` | `4` | 최대 동시 시퀀스 |
| `VLLM_MAX_MODEL_LEN` | `32768` | 최대 모델 길이 |
| `VLLM_MAX_BATCHED_TOKENS` | `65536` | 최대 배치 토큰 |
| `HF_CACHE_DIR` | `vllm_cache` (Docker 볼륨) | HuggingFace 캐시 경로 |

## 헬스체크

| 서비스 | 엔드포인트 | 간격 |
| -------- | ----------- | ------ |
| PostgreSQL | `pg_isready -U labeling -d labeling` | 5초 |
| Backend | `curl http://localhost:5000/api/v1/health` | 10초 |
| vLLM | `curl http://localhost:8000/health` | 30초 |
| PP-StructureV3 | `curl http://localhost:18811/health` | 10초 |
| Frontend | nginx 기본 (포트 80) | - |

## 개발 팁

### 코드 변경 후 재빌드

```bash
# 특정 서비스만 재빌드
docker compose up -d --build backend

# 전체 재빌드 (캐시 무시)
docker compose build --no-cache
```

### 로그 확인

```bash
# 전체 로그
make logs

# 특정 서비스
docker compose logs -f backend

# 최근 100줄만
docker compose logs --tail=100 backend
```

### 데이터베이스 직접 접속

```bash
docker compose exec postgres psql -U labeling -d labeling
```

### 마이그레이션 재실행

```bash
# PostgreSQL 데이터 초기화 후 재시작
docker compose down -v
make up
```

마이그레이션 SQL은 PostgreSQL 컨테이너 초기화 시 자동 실행됩니다
(`/docker-entrypoint-initdb.d/001_init.sql`).
