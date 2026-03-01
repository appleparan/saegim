# saegim (새김)

한국어 문서 VLM 벤치마크를 위한 Human-in-the-Loop 레이블링 플랫폼.

PDF 문서를 업로드하면 페이지별 이미지로 변환하고,
웹 기반 에디터에서 레이아웃 요소의 바운딩 박스·카테고리·속성을 레이블링하여
[OmniDocBench](https://github.com/opendatalab/OmniDocBench) 표준 JSON으로 내보내는 도구입니다.

## 아키텍처

```mermaid
graph TB
    subgraph Frontend ["Svelte 5 (:5173)"]
        FE["PDF.js + Konva.js<br/>Runes 상태관리<br/>3-Layer 에디터"]
    end

    subgraph Backend ["FastAPI (:5000)"]
        API["PDF 변환, CRUD<br/>Engine Factory<br/>Repository 패턴"]
        BG["asyncio<br/>background"]
    end

    subgraph DB ["PostgreSQL"]
        PG["JSONB"]
    end

    subgraph OCR ["OCR 엔진 (4종)"]
        GEMINI["Gemini API"]
        VLLM["vLLM (Chandra)"]
        DOCLING_OCR["Docling + OCR"]
        PDFMINER["pdfminer"]
    end

    FE <-->|"REST/JSON"| API
    API <-->|"asyncpg/SQL"| PG
    API --> BG
    BG --> GEMINI
    BG --> VLLM
    BG --> DOCLING_OCR
    BG --> PDFMINER
```

## 기술 스택

| 계층 | 기술 |
| ---- | ---- |
| **프론트엔드** | Svelte 5 (Runes), TypeScript, Vite 7, shadcn-svelte + Tailwind CSS 4, PDF.js, Konva.js, 다크모드 (mode-watcher) |
| **백엔드** | Python 3.13+, FastAPI, asyncpg (raw SQL), Pydantic |
| **데이터베이스** | PostgreSQL 15+ (JSONB) |
| **PDF 처리** | pypdfium2 (2x 해상도 렌더링) + pdfminer.six (텍스트/이미지 자동 추출) |
| **OCR 엔진** | 4종 Strategy 패턴 (`BaseOCREngine` ABC) |
| | - `pdfminer`: pdfminer.six 폴백 (GPU 불필요, 동기) |
| | - `commercial_api`: Gemini API / vLLM (full-page VLM) |
| | - `vllm`: vLLM 서버 (Chandra 등) |
| | - `split_pipeline`: Docling 레이아웃 + Gemini/vLLM OCR |
| **비동기 태스크** | asyncio 백그라운드 태스크 |
| **패키지 관리** | Backend: uv / Frontend: Bun |
| **E2E 테스트** | Vitest + Docker Compose (기본 + GPU 프로파일) |

## 주요 기능

- **PDF 업로드 및 변환**: PDF를 페이지별 고해상도 PNG로 자동 변환
- **4종 OCR 엔진**: `engine_type` 기반 프로젝트별 엔진 선택
- **텍스트/이미지 자동 추출**: OCR 엔진으로 레이아웃+텍스트 추출, 수락 시 어노테이션에 반영
- **자동 속성 분류**: 페이지/테이블/텍스트/수식 속성 자동 분류
- **캔버스 에디터**: 바운딩 박스 생성·편집·삭제, 줌/패닝, 키보드 단축키
- **읽기 순서 에디터**: 드래그앤드롭 재정렬 + 캔버스 오버레이 (`O` 단축키)
- **관계 도구**: 요소 간 관계 CRUD + SVG 화살표 시각화
- **OmniDocBench 레이블링**: 15종 Block-level + 4종 Span-level 카테고리, 페이지/요소 속성 편집
- **프로젝트 관리**: 프로젝트 → 문서 → 페이지 계층 구조
- **사용자 역할**: admin, annotator, reviewer
- **JSON Export**: OmniDocBench 표준 포맷으로 내보내기
- **E2E 테스트**: Vitest 기반 자동화 (기본 + GPU 프로파일)

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

## 프로젝트 구조

```text
saegim/
├── saegim-backend/
│   ├── src/saegim/
│   │   ├── app.py                  # FastAPI 앱 팩토리
│   │   ├── api/routes/             # REST 엔드포인트
│   │   ├── schemas/                # Pydantic 모델 (EngineType, OcrConfig 등)
│   │   ├── services/
│   │   │   ├── engines/            # OCR 엔진 Strategy 패턴 (4종)
│   │   │   │   ├── base.py         # BaseOCREngine ABC
│   │   │   │   ├── factory.py      # build_engine() 팩토리
│   │   │   │   ├── pdfminer_engine.py
│   │   │   │   ├── commercial_api_engine.py
│   │   │   │   ├── vllm_engine.py
│   │   │   │   └── split_pipeline_engine.py
│   │   │   ├── labeling_service.py        # 저장, 읽기 순서, 관계 CRUD
│   │   │   ├── attribute_classifier.py    # 페이지/요소 속성 자동 분류
│   │   │   ├── layout_types.py            # LayoutRegion, LayoutDetector Protocol
│   │   │   ├── docling_layout_service.py  # Docling 레이아웃 감지
│   │   │   ├── gemini_ocr_service.py      # Gemini VLM 프로바이더
│   │   │   ├── vllm_ocr_service.py        # vLLM 프로바이더 (Chandra 등)
│   │   │   └── ocr_pipeline.py            # 2단계 파이프라인 오케스트레이터
│   │   ├── repositories/           # 데이터 접근 (raw SQL)
│   │   └── core/                   # DB 커넥션 풀
│   ├── migrations/                 # SQL 마이그레이션
│   ├── tests/                      # pytest 테스트
│   └── docs/                       # MkDocs 문서
├── saegim-frontend/
│   ├── src/
│   │   ├── routes/                 # SvelteKit 라우트 페이지
│   │   └── lib/
│   │       ├── types/              # OmniDocBench 타입 정의
│   │       ├── api/                # HTTP 클라이언트
│   │       ├── stores/             # Svelte 5 Runes 스토어
│   │       ├── components/         # UI: ui/ (shadcn-svelte), canvas/, panels/, layout/, settings/
│   │       └── utils/              # 유틸리티 함수
│   └── tests/                      # Vitest 테스트
├── e2e/                            # E2E 테스트 (Vitest + Docker Compose)
│   ├── docker-compose.e2e.yml      # 기본 + GPU 프로파일
│   ├── tests/                      # 기본 테스트
│   └── tests/gpu/                  # GPU 전용 테스트 (vLLM)
├── docker-compose.yml              # 개발/배포용 (--profile gpu으로 GPU 서비스 활성화)
├── Makefile                        # make up / make up-gpu 편의 명령
├── .env.gpu                        # GPU 빌드 설정 (CUDA 13.0)
├── k8s/
│   ├── base/                       # Kustomize 공통 매니페스트
│   └── overlays/
│       ├── cpu/                    # CPU 전용 배포
│       └── gpu/                    # GPU 배포 (vLLM 포함)
└── AGENTS.md                       # 플래닝 가이드
```

## API 엔드포인트

| Method | Path | 설명 |
| ------ | ---- | ---- |
| `POST` | `/api/v1/projects` | 프로젝트 생성 |
| `GET` | `/api/v1/projects` | 프로젝트 목록 |
| `POST` | `/api/v1/projects/:id/documents` | PDF 업로드 |
| `GET` | `/api/v1/pages/:id` | 페이지 + 어노테이션 조회 |
| `PUT` | `/api/v1/pages/:id` | 어노테이션 저장 |
| `PUT` | `/api/v1/pages/:id/attributes` | 페이지 속성 저장 |
| `POST` | `/api/v1/pages/:id/elements` | 레이아웃 요소 추가 |
| `DELETE` | `/api/v1/pages/:id/elements/:anno_id` | 요소 삭제 |
| `PUT` | `/api/v1/pages/:id/reading-order` | 읽기 순서 업데이트 |
| `POST` | `/api/v1/pages/:id/relations` | 관계 추가 |
| `DELETE` | `/api/v1/pages/:id/relations` | 관계 삭제 |
| `POST` | `/api/v1/pages/:id/accept-extraction` | 자동 추출 결과 수락 |
| `GET` | `/api/v1/projects/:id/ocr-config` | OCR 설정 조회 |
| `PUT` | `/api/v1/projects/:id/ocr-config` | OCR 설정 수정 |
| `POST` | `/api/v1/projects/:id/ocr-config/test` | OCR 연결 테스트 |
| `POST` | `/api/v1/projects/:id/export` | OmniDocBench JSON 내보내기 |

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

## 라이선스

MIT
