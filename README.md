# saegim (새김)

한국어 문서 VLM 벤치마크를 위한 Human-in-the-Loop 레이블링 플랫폼.

PDF 문서를 업로드하면 페이지별 이미지로 변환하고,
웹 기반 에디터에서 레이아웃 요소의 바운딩 박스·카테고리·속성을 레이블링하여
[OmniDocBench](https://github.com/opendatalab/OmniDocBench) 표준 JSON으로 내보내는 도구입니다.

## 주요 기능

- **PDF 업로드 및 변환**: PDF를 페이지별 고해상도 PNG로 자동 변환
- **다중 인스턴스 OCR 엔진**: 프로젝트별 엔진 등록·관리 (Gemini API, vLLM, Docling+OCR)
- **텍스트/이미지 자동 추출**: OCR 엔진으로 레이아웃+텍스트 추출, 수락 시 어노테이션에 반영
- **자동 속성 분류**: 페이지/테이블/텍스트/수식 속성 자동 분류
- **캔버스 에디터**: 바운딩 박스 생성·편집·삭제, 줌/패닝, 키보드 단축키
- **읽기 순서 에디터**: 드래그앤드롭 재정렬 + 캔버스 오버레이 (`O` 단축키)
- **관계 도구**: 요소 간 관계 CRUD + SVG 화살표 시각화
- **OmniDocBench 레이블링**: 15종 Block-level + 4종 Span-level 카테고리, 페이지/요소 속성 편집
- **인증/인가**: JWT 기반 인증, 시스템 역할 (admin/annotator/reviewer)
- **관리자 대시보드**: 유저/프로젝트/시스템 통계 관리
- **프로젝트 관리**: 프로젝트 → 문서 → 페이지 계층 구조
- **JSON Export**: OmniDocBench 표준 포맷으로 내보내기

## 시작하기

### Docker Compose (권장)

Docker만 설치되어 있으면 별도 환경 설정 없이 실행할 수 있습니다.

#### 사전 요구사항

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)

#### 환경 변수 설정

```bash
cp .env.example .env
# 필요 시 .env 파일을 수정합니다
```

#### CPU 모드 (기본)

```bash
# 빌드 + 실행
make up
# 또는: docker compose up -d --build

# 중지
make down
```

#### GPU 모드

NVIDIA GPU + [NVIDIA Container Toolkit][nvidia-toolkit]이 필요합니다.

[nvidia-toolkit]: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

```bash
# GPU 빌드 + 실행 (vLLM 포함)
make up-gpu
# 또는: docker compose --env-file .env --env-file .env.gpu --profile gpu up -d --build

# 중지
make down-gpu
```

> `.env.gpu`에서 CUDA 버전과 PyTorch extra를 변경할 수 있습니다 (기본: CUDA 13.0, cu130).

#### 접속

| URL | 설명 |
| --- | ---- |
| <http://localhost:13000> | 프론트엔드 |
| <http://localhost:15000/docs> | Swagger UI |
| <http://localhost:15000/redoc> | ReDoc |

> 포트는 `.env`에서 `FE_PORT`, `API_PORT`, `PG_PORT`로 변경할 수 있습니다.

#### 로그 및 관리

```bash
# 로그 확인
make logs
# 또는: docker compose logs -f

# 특정 서비스 로그
docker compose logs -f backend

# 볼륨 포함 삭제 (DB 데이터 초기화)
docker compose down -v
```

---

### 로컬 개발 환경

#### 로컬 사전 요구사항

- Python 3.13+ & [uv](https://docs.astral.sh/uv/)
- [Bun](https://bun.sh/)
- PostgreSQL 15+

#### 데이터베이스 설정

```bash
sudo -u postgres psql
CREATE USER labeling WITH PASSWORD 'labeling';
CREATE DATABASE labeling OWNER labeling;
\q
```

#### 백엔드

```bash
cd saegim-backend
uv python install 3.14
uv python pin 3.14
uv sync --group dev --group docs --extra cpu    # CPU only
# uv sync --group dev --group docs --extra cu128  # CUDA 12.8

# 마이그레이션
psql -U labeling -d labeling -f migrations/001_init.sql

# .env 파일 생성
cat <<EOF > .env
DATABASE_URL=postgresql://labeling:labeling@localhost:5432/labeling
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=your-secret-key-change-in-production
EOF

# 서버 실행
uv run uvicorn saegim.app:app --reload --host 0.0.0.0 --port 5000
```

#### 프론트엔드

```bash
cd saegim-frontend
bun install

# .env 파일 생성
echo "VITE_API_URL=http://localhost:5000" > .env

# 개발 서버 실행
bun run dev
```

#### 로컬 접속

| URL | 설명 |
| --- | ---- |
| <http://localhost:5173> | 프론트엔드 |
| <http://localhost:5000/docs> | Swagger UI (DEBUG=true) |
| <http://localhost:5000/redoc> | ReDoc (DEBUG=true) |

## 개발

```bash
# 백엔드
uv run ruff format                  # 포맷팅
uv run ruff check --fix             # 린트
uv run ty check                     # 타입 체크
uv run pytest --cov                 # 테스트 + 커버리지

# 프론트엔드
bun run check                       # 타입 체크
bun run test                        # 테스트
bun run build                       # 프로덕션 빌드
```

## 상세 문서

| 문서 | 설명 |
| ---- | ---- |
| [아키텍처 개요](docs/architecture/README.md) | 시스템 구조, 기술 스택, 인증 |
| [백엔드 아키텍처](docs/backend/architecture/architecture.md) | 레이어드 아키텍처, 데이터 흐름 |
| [프론트엔드 아키텍처](docs/frontend/architecture/architecture.md) | 컴포넌트 구조, 상태 관리 |
| [API 가이드](docs/backend/guide/api.md) | REST API 엔드포인트 |
| [추출 파이프라인](docs/architecture/extraction-pipeline.md) | OCR 엔진 아키텍처 |
| [데이터 스키마](docs/architecture/data-schema.md) | DB 구조, OmniDocBench 포맷 |
| [멀티유저 협업](docs/architecture/multi-user-collaboration.md) | 인증, 역할, 태스크 워크플로우 |
| [배포 가이드](docs/deployment/quickstart.md) | Docker, Kubernetes |
| [플래닝 가이드](AGENTS.md) | 프로젝트 비전, 로드맵 |

## 라이선스

Apache-2.0 License
