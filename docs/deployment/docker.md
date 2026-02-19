# Docker 개발 가이드

## 이미지 빌드

### 백엔드 (CPU)

```bash
docker build -t saegim-backend \
  -f saegim-backend/Dockerfile \
  saegim-backend/
```

- 베이스: `python:3.13-slim`
- uv로 의존성 설치 (lock 파일 기반)
- 비루트 사용자 `appuser` (UID 1000)

### 백엔드 (GPU - source)

```bash
docker build -t saegim-backend-gpu \
  -f saegim-backend/Dockerfile.source \
  saegim-backend/
```

- 베이스: `nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.04`
- 개발용 (빌드 도구 포함)

### 백엔드 (GPU - package)

```bash
docker build -t saegim-backend-gpu \
  -f saegim-backend/Dockerfile.package \
  saegim-backend/
```

- 멀티 스테이지 빌드 (builder → runtime)
- wheel 패키징으로 런타임 이미지 최적화

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
| `postgres` | `postgres:16` | 5432 | default |
| `backend` | `Dockerfile` (CPU) | 5000 | default |
| `backend-gpu` | `Dockerfile.source` (GPU) | 5000 | gpu |
| `frontend` | `saegim-frontend` | 3000→80 | default |

### 네트워크

모든 서비스는 `saegim-net` 브릿지 네트워크에 연결됩니다.
서비스 간 통신은 서비스 이름으로 접근합니다 (예: `postgres:5432`, `backend:5000`).

### 볼륨

| 볼륨 | 경로 | 설명 |
| ------ | ------ | ------ |
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL 영구 데이터 |
| `./storage` | `/workspace/storage` | PDF 원본 및 페이지 이미지 |

### 의존성 순서

```text
postgres (healthy) → backend (healthy) → frontend
```

- `postgres`: `pg_isready` healthcheck 통과 후 backend 시작
- `backend`: `/api/v1/health` healthcheck 통과 후 frontend 시작

## GPU 프로파일

### 사전 요구사항

- NVIDIA GPU 드라이버
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### 실행

```bash
# GPU 모드 시작
docker compose --profile gpu up -d

# GPU 모드에서는 backend 대신 backend-gpu가 5000 포트 사용
docker compose --profile gpu ps
```

### 확인

```bash
# GPU 인식 확인
docker compose --profile gpu exec backend-gpu nvidia-smi
```

## 환경 변수

### 백엔드

| 변수 | 기본값 | 설명 |
| ------ | -------- | ------ |
| `DATABASE_URL` | `postgresql://labeling:labeling@localhost:15432/labeling` | DB 연결 URL |
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

## 헬스체크

| 서비스 | 엔드포인트 | 간격 |
| -------- | ----------- | ------ |
| PostgreSQL | `pg_isready -U labeling -d labeling` | 5초 |
| Backend | `curl http://localhost:15000/api/v1/health` | 10초 |
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
docker compose logs -f

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
docker compose up -d
```

마이그레이션 SQL은 PostgreSQL 컨테이너 초기화 시 자동 실행됩니다
(`/docker-entrypoint-initdb.d/001_init.sql`).
