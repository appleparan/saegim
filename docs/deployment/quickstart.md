# 빠른 시작

Docker Compose를 사용해 saegim 전체 스택(PostgreSQL + 백엔드 + 프론트엔드)을 한 번에 실행하는 방법입니다.

## 사전 요구사항

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/install/) v2+

## 실행

### 1. 환경 변수 설정

```bash
cp .env.example .env
```

필요에 따라 `.env` 파일을 수정합니다:

| 변수 | 기본값 | 설명 |
| ------ | -------- | ------ |
| `DB_PASSWORD` | `labeling` | PostgreSQL 비밀번호 |
| `VITE_API_URL` | `http://localhost:15000` | 프론트엔드가 호출할 백엔드 API 주소 |
| `API_PORT` | `15000` | 백엔드 호스트 포트 |
| `FE_PORT` | `13000` | 프론트엔드 호스트 포트 |
| `PG_PORT` | `15432` | PostgreSQL 호스트 포트 |

### 2. 전체 실행 (CPU 모드)

```bash
docker compose up -d
```

시작 순서: PostgreSQL → Backend (healthcheck 통과 후) → Frontend

### 3. 전체 실행 (GPU 모드)

NVIDIA GPU가 있는 환경에서 GPU 가속 백엔드를 사용하려면:

```bash
docker compose --profile gpu up -d
```

!!! note
    GPU 모드에서는 `backend` 대신 `backend-gpu` 서비스가 실행됩니다.
    [NVIDIA Container Toolkit][nvidia-toolkit]이 설치되어 있어야 합니다.

[nvidia-toolkit]: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

## 접속 확인

| URL | 설명 |
| ----- | ------ |
| <http://localhost:13000> | 프론트엔드 (웹 UI) |
| <http://localhost:15000/api/v1/health> | 백엔드 헬스체크 |
| <http://localhost:15000/docs> | Swagger UI (`DEBUG=true` 시) |
| `localhost:15432` | PostgreSQL (외부 접속) |

### 헬스체크

```bash
# 백엔드 상태 확인
curl http://localhost:15000/api/v1/health

# 서비스 상태 확인
docker compose ps
```

## 중지 및 정리

```bash
# 서비스 중지
docker compose down

# 서비스 중지 + 데이터 삭제 (PostgreSQL 데이터 포함)
docker compose down -v
```

## 문제 해결

### 포트 충돌

기본 포트가 이미 사용 중이면 `.env` 파일에서 포트를 변경합니다:

```bash
API_PORT=25000
FE_PORT=23000
PG_PORT=25432
```

### Backend 시작 실패

```bash
# 로그 확인
docker compose logs backend

# PostgreSQL 상태 확인
docker compose logs postgres
```

### 이미지 재빌드

코드 변경 후 이미지를 갱신하려면:

```bash
docker compose up -d --build
```

## 다음 단계

- [Docker 개발 가이드](docker.md) - 이미지 빌드, GPU 프로파일 상세
- [Kubernetes 배포 가이드](kubernetes.md) - 클러스터 배포
