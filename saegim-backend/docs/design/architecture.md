# 아키텍처

## 시스템 구조

```mermaid
graph TB
    subgraph Client
        FE[Frontend - SvelteKit]
    end

    subgraph Backend
        API[FastAPI Routes]
        SVC[Services]
        REPO[Repositories]
    end

    subgraph Storage
        PG[(PostgreSQL)]
        FS[File System]
    end

    FE -->|HTTP/REST| API
    API --> SVC
    SVC --> REPO
    REPO -->|asyncpg raw SQL| PG
    SVC -->|PDF/Image| FS
```

## 레이어드 아키텍처

saegim 백엔드는 3계층 구조를 따릅니다:

### Routes (API 라우터)

HTTP 요청을 받아 적절한 서비스를 호출하고 응답을 반환합니다.

```text
src/saegim/api/routes/
├── health.py       # GET /api/v1/health
├── projects.py     # 프로젝트 CRUD (project_type, OCR 설정 포함)
├── documents.py    # 문서 업로드/조회
├── pages.py        # 페이지 레이블링
├── users.py        # 사용자 관리
├── analysis.py     # Phase 4a: 문서 분석 메타데이터 CRUD
└── export.py       # 데이터 내보내기 (OmniDocBench / VQA / OCRAG)
```

- FastAPI의 `APIRouter`를 사용
- Pydantic 스키마로 요청/응답 검증
- 모든 엔드포인트는 `/api/v1` 접두사

### Services (비즈니스 로직)

핵심 비즈니스 로직을 처리합니다.

```text
src/saegim/services/
├── document_service.py       # PDF 업로드 → 이미지 변환 → 추출 분기 (PyMuPDF/Celery)
├── extraction_service.py     # PyMuPDF 폴백 추출 (text_block + figure)
├── ppstructure_service.py    # PP-StructureV3 HTTP 클라이언트 (PpstructureClient, LayoutRegion)
├── ocr_pipeline.py           # 2단계 파이프라인 오케스트레이터 (OcrPipeline, build_ocr_pipeline)
├── ocr_provider.py           # TextOcrProvider Protocol + 팩토리 (get_text_ocr_provider)
├── gemini_ocr_service.py     # GeminiTextOcrProvider (크롭 이미지 → 텍스트)
├── vllm_ocr_service.py       # VllmTextOcrProvider (OlmOCR via vLLM)
├── ocr_connection_test.py    # PP-StructureV3 + OCR 프로바이더 연결 테스트
├── labeling_service.py       # 어노테이션 CRUD, 요소 추가/삭제, 자동 추출 수락
├── analysis_service.py       # Phase 4a: AI 문서 분석 (Overview, Core Idea, Key Figures, Limitations)
└── export_service.py         # OmniDocBench JSON 조합 (Strategy 패턴으로 VQA/OCRAG Export 확장)
```

- Repository를 호출하여 데이터 접근
- 파일 시스템 I/O 처리 (PDF 저장, 이미지 변환)
- JSONB 데이터의 JSON string/dict 파싱 처리

### Repositories (데이터 접근)

asyncpg를 사용하여 PostgreSQL에 raw SQL을 실행합니다.

```text
src/saegim/repositories/
├── project_repo.py    # INSERT/SELECT projects
├── document_repo.py   # INSERT/SELECT/UPDATE documents
├── page_repo.py       # JSONB 연산 (jsonb_set, jsonb_agg)
└── user_repo.py       # INSERT/SELECT users
```

- 모든 함수는 `asyncpg.Pool`을 첫 번째 인자로 받음
- SQL 파라미터는 `$1`, `$2` 등 positional binding 사용
- `asyncpg.Record` 객체 반환

## 데이터 흐름

### PDF 업로드 플로우

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant DS as DocumentService
    participant DR as DocumentRepo
    participant PR as PageRepo
    participant PDF as PyMuPDF
    participant EX as ExtractionService

    C->>R: POST /projects/{id}/documents (PDF file)
    R->>DS: upload_and_convert(pool, project_id, file)
    DS->>DS: PDF 파일 저장 (storage/pdfs/)
    DS->>DR: create(pool, project_id, filename, ...)
    DR-->>DS: document record
    DS->>PDF: fitz.open(pdf_path)
    loop 각 페이지
        DS->>PDF: page.get_pixmap(matrix=2x)
        DS->>DS: 이미지 저장 (storage/images/)
        DS->>EX: extract_page_elements(page, scale=2.0)
        Note over EX: get_text("dict") → 텍스트/이미지 블록 추출<br/>좌표 × 2.0 스케일링
        EX-->>DS: auto_extracted_data (OmniDocBench 형식)
        DS->>PR: create(pool, document_id, page_no, ..., auto_extracted_data)
    end
    DS->>DR: update_status(pool, id, 'ready')
    DS-->>R: {id, filename, total_pages, status}
    R-->>C: 201 Created
```

### 어노테이션 저장 플로우

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant LS as LabelingService
    participant PR as PageRepo

    C->>R: PUT /pages/{id} (annotation_data)
    R->>LS: save_annotation(pool, page_id, data)
    LS->>PR: update_annotation(pool, page_id, data)
    Note over PR: UPDATE pages SET annotation_data = $1::jsonb
    PR-->>LS: updated record
    LS-->>R: page data dict
    R-->>C: 200 OK
```

### 내보내기 플로우

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant ES as ExportService
    participant PjR as ProjectRepo
    participant PR as PageRepo

    C->>R: POST /projects/{id}/export
    R->>ES: export_project(pool, project_id)
    ES->>PjR: get_by_id(pool, project_id)
    ES->>PR: get_all_by_project(pool, project_id)
    Note over ES: annotation_data에서 page_attribute 추출<br/>page_info 블록 조합
    ES-->>R: {project_name, total_pages, data: [...]}
    R-->>C: 200 OK (OmniDocBench JSON)
```

### 자동 추출 수락 플로우

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant LS as LabelingService
    participant PR as PageRepo

    C->>R: POST /pages/{id}/accept-extraction
    R->>LS: accept_auto_extraction(pool, page_id)
    LS->>PR: accept_auto_extracted(pool, page_id)
    Note over PR: SET annotation_data = auto_extracted_data<br/>WHERE annotation empty AND auto_extracted NOT NULL
    PR-->>LS: updated record (or None)
    LS-->>R: page data dict (or None → 409)
    R-->>C: 200 OK / 409 Conflict
```

## 커넥션 풀 관리

asyncpg 커넥션 풀은 FastAPI lifespan으로 관리됩니다:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = app.state.settings
    await create_pool(
        settings.database_url,
        min_size=settings.db_pool_min_size,  # 기본값: 2
        max_size=settings.db_pool_max_size,  # 기본값: 10
    )
    yield
    await close_pool()
```

- 앱 시작 시 풀 생성, 종료 시 풀 해제
- `get_pool()` 함수로 모듈 레벨 풀 접근
- Repository 함수는 풀을 인자로 받아 커넥션 획득

## 정적 파일 서빙

페이지 이미지는 FastAPI `StaticFiles`로 제공됩니다:

```text
/storage/images/{document_id}_p{page_no}.png
```

`storage/images/` 디렉토리가 `/storage/images` 경로로 마운트됩니다.
