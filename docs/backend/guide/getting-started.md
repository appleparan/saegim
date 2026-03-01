# 시작하기

## 사전 요구사항

- Python 3.13+
- PostgreSQL 15+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저

## 설치

### 1. uv 설치

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 프로젝트 클론 및 설정

```bash
git clone https://github.com/appleparan/saegim
cd saegim/saegim-backend

# Python 설치 및 고정
uv python install 3.14
uv python pin 3.14

# 의존성 설치 (개발 + 문서, CPU only)
uv sync --group dev --group docs --extra cpu

# GPU 사용 시 CUDA 버전에 맞는 extra 선택
uv sync --group dev --group docs --extra cu128   # CUDA 12.8
uv sync --group dev --group docs --extra cu126   # CUDA 12.6
uv sync --group dev --group docs --extra cu130   # CUDA 13.0
```

> **참고:** `--extra` 플래그로 PyTorch 설치 변형을 선택합니다.
> Docling 등 OCR 엔진이 PyTorch를 필요로 하므로 반드시 하나를 선택해야 합니다.
>
> | Extra | 설명 | GPU 필요 |
> | ----- | ---- | -------- |
> | `cpu` | CPU 전용 (경량) | X |
> | `cu126` | CUDA 12.6 | O |
> | `cu128` | CUDA 12.8 | O |
> | `cu130` | CUDA 13.0 | O |

### 3. PostgreSQL 설정

데이터베이스와 사용자를 생성합니다:

```bash
# PostgreSQL에 접속
sudo -u postgres psql

# 데이터베이스 생성
CREATE USER labeling WITH PASSWORD 'labeling';
CREATE DATABASE labeling OWNER labeling;
\q
```

### 4. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다:

```bash
# .env
DATABASE_URL=postgresql://labeling:labeling@localhost:5432/labeling
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=true
LOG_LEVEL=DEBUG
STORAGE_PATH=./storage
```

### 5. 마이그레이션 실행

```bash
# psql로 직접 실행
psql -U labeling -d labeling -f migrations/001_init.sql
```

### 6. 서버 실행

```bash
uv run uvicorn saegim.app:app --reload --host 0.0.0.0 --port 5000
```

서버가 실행되면 다음 주소에서 확인할 수 있습니다:

- API: `http://localhost:5000/api/v1/health`
- Swagger UI: `http://localhost:5000/docs` (DEBUG=true일 때)
- ReDoc: `http://localhost:5000/redoc` (DEBUG=true일 때)

## 설치 확인

```bash
# 헬스체크
curl http://localhost:5000/api/v1/health

# 응답 예시
# {"status": "healthy"}
```

## 테스트

```bash
# 전체 테스트 실행
uv run pytest

# 커버리지 포함
uv run pytest --cov

# 특정 테스트 파일
uv run pytest tests/api/test_projects.py -v
uv run pytest tests/services/test_labeling_service.py -v
```

## 개발 도구

```bash
# 코드 포맷팅
uv run ruff format

# 린트 검사
uv run ruff check

# 타입 검사
uv run ty check

# 문서 로컬 서버
uv run mkdocs serve
```

## Docker (선택사항)

```bash
# CPU 이미지 빌드 (프로덕션)
docker build -t saegim-backend .

# CPU 이미지 빌드 (개발, dev 의존성 포함)
docker build -t saegim-backend-dev --target development .

# GPU 이미지 빌드 (CUDA 13.0)
docker build -t saegim-backend-gpu \
  --build-arg BASE_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
  --build-arg TORCH_EXTRA=cu130 .

# 실행
docker run -p 5000:5000 \
  -e DATABASE_URL=postgresql://labeling:labeling@host.docker.internal:5432/labeling \
  saegim-backend
```

## 다음 단계

- [아키텍처](../architecture/architecture.md) - 시스템 구조 이해
- [API 엔드포인트](api.md) - API 사용법
- [데이터베이스](../architecture/database.md) - 스키마 구조
- [개발 가이드](../dev/development.md) - 기여 방법
