# saegim (새김)

한국어 문서 VLM 벤치마크를 위한 Human-in-the-Loop 레이블링 플랫폼.

PDF 문서를 업로드하면 페이지별 이미지로 변환하고,
웹 기반 에디터에서 레이아웃 요소의 바운딩 박스·카테고리·속성을 레이블링하여
[OmniDocBench](https://github.com/opendatalab/OmniDocBench) 표준 JSON으로 내보내는 도구입니다.

## Key Features

### 프로젝트 설정 & PDF 업로드

프로젝트를 생성하고, OCR 엔진을 설정한 뒤, PDF를 업로드하면 페이지별 이미지로 자동 변환합니다.

[Project-setup.webm](https://github.com/user-attachments/assets/891dc0a9-59cf-4269-8c7e-2e28ff8c4367)

### 레이블 에디터

AI OCR로 자동 추출된 레이아웃 요소를 검토하고, 바운딩 박스 그리기·요소 인덱스 오버레이·읽기 순서 편집 등 다양한 도구로 레이블링합니다.

[Label-editor-extraction-annotation-overlays.webm](https://github.com/user-attachments/assets/8661bf0c-e967-411c-b876-9bda47650532)

### 프로젝트 개요 & 내보내기

작업 현황 대시보드에서 진행률을 확인하고, OmniDocBench 표준 JSON으로 내보냅니다.

[Project-overview-dashboard-and-export.webm](https://github.com/user-attachments/assets/9699686f-0f6e-4d80-82cd-ec53f0203da6)

## 상세 기능

- **PDF 변환** — PDF를 페이지별 고해상도 PNG로 자동 변환
- **다중 OCR 엔진** — 프로젝트별 엔진 등록·관리 (Gemini API, vLLM, Docling+OCR, pdfminer)
- **자동 속성 분류** — 페이지/테이블/텍스트/수식 속성 자동 분류
- **캔버스 에디터** — 바운딩 박스 생성·편집·삭제, 줌/패닝, 키보드 단축키
- **읽기 순서 에디터** — 드래그앤드롭 재정렬 + 캔버스 오버레이
- **관계 도구** — 요소 간 관계 CRUD + SVG 화살표 시각화
- **OmniDocBench 레이블링** — 15종 Block-level + 4종 Span-level 카테고리
- **인증/인가** — JWT 기반 인증, 시스템 역할 (admin/annotator/reviewer)
- **관리자 대시보드** — 유저/프로젝트/시스템 통계 관리
- **JSON Export** — OmniDocBench 표준 포맷으로 내보내기

## Quickstart

### Docker Compose (권장)

Docker만 설치되어 있으면 3단계로 바로 시작할 수 있습니다.

```bash
# 1. 환경 변수 설정
cp .env.example .env

# 2. 빌드 + 실행
make up
# 또는: docker compose up -d --build

# 3. 브라우저에서 접속
#    프론트엔드: http://localhost:13000
#    API 문서:   http://localhost:15000/docs
```

GPU 모드가 필요하다면 NVIDIA Container Toolkit 설치 후:

```bash
make up-gpu
```

### 로컬 개발 환경

```bash
# 백엔드
cd saegim-backend
uv sync --group dev --group docs --extra cpu    # CPU (또는 --extra cu128)
uv run uvicorn saegim.app:app --reload --host 0.0.0.0 --port 5000

# 프론트엔드
cd saegim-frontend
bun install && bun run dev
```

로컬 접속: 프론트엔드 `http://localhost:5173` / API 문서 `http://localhost:5000/docs`

> 데이터베이스 설정, 마이그레이션 등 상세 가이드는 [백엔드 시작하기](docs/backend/guide/getting-started.md)를 참고하세요.

## Documentation

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

Apache-2.0 License
