# Architecture

## System Structure

```mermaid
graph TB
    subgraph Client
        FE[Frontend - SvelteKit]
    end

    subgraph Backend
        AUTH[Auth Middleware]
        API[FastAPI Routes]
        SVC[Services]
        REPO[Repositories]
    end

    subgraph Storage
        PG[(PostgreSQL)]
        FS[File System]
    end

    FE -->|HTTP/REST + JWT| AUTH
    AUTH --> API
    API --> SVC
    SVC --> REPO
    REPO -->|asyncpg raw SQL| PG
    SVC -->|PDF/Image| FS
```

## Layered Architecture

The saegim backend follows a 3-tier architecture:

### Routes (API Router)

Receives HTTP requests, calls the appropriate service, and returns responses.

```text
src/saegim/api/
├── deps.py         # Auth/authz dependency (get_current_user, require_admin, require_project_member)
└── routes/
    ├── health.py       # GET /api/v1/health, /health/ready
    ├── auth.py         # Registration, login, token refresh, logout, credentials change
    ├── admin.py        # User/project/system stats management (admin only)
    ├── projects.py     # Project CRUD, OCR engine instance CRUD, default engine configuration
    ├── documents.py    # Document upload/view/delete/re-extract
    ├── pages.py        # Page labeling, reading order, relation CRUD, force accept, per-element text extraction
    ├── users.py        # User management
    └── export.py       # OmniDocBench JSON export
```

- Uses FastAPI's `APIRouter`
- Request/response validation with Pydantic schemas
- All endpoints use the `/api/v1` prefix
- Protected endpoints verify JWT via `get_current_user` dependency

### Authentication/Authorization (deps.py)

Auth-related FastAPI Depends are defined in `api/deps.py`:

- `get_current_user`: Decodes JWT from Bearer token, extracts user_id/role
- `require_admin`: Verifies `role == 'admin'` (403 Forbidden)
- `require_project_member`: Checks project membership or admin status
- `create_access_token` / `create_refresh_token`: JWT/refresh token generation
- `rotate_refresh_token`: Token rotation (revoke previous token + issue new token)
- `validate_refresh_token`: Grace period-based theft detection

### Services (Business Logic)

Handles core business logic.

```text
src/saegim/services/
├── engines/                       # OCR Engine Strategy Pattern
│   ├── base.py                    # BaseOCREngine ABC (extract_page, test_connection)
│   ├── factory.py                 # build_engine_by_id(ocr_config, engine_id) factory (multi-instance)
│   ├── pdfminer_engine.py          # PdfminerEngine (GPU-free fallback)
│   ├── commercial_api_engine.py   # CommercialApiEngine (Gemini/vLLM full-page)
│   ├── vllm_engine.py             # VllmEngine (DocIR Adapter pattern, resolve_adapter() auto-detection)
│   └── split_pipeline_engine.py   # SplitPipelineEngine (layout detection + external OCR, layout_provider selection)
├── docir.py                       # DocIR intermediate representation (PageIR, ElementIR, Geometry, RecognitionResult)
├── adapters/                      # Model-specific Adapters (raw → DocIR conversion)
│   ├── base.py                    # ModelAdapter Protocol (build_messages, parse_response)
│   ├── resolver.py                # resolve_adapter(model_name) — auto-select Adapter by model name
│   ├── chandra.py                 # ChandraAdapter (Chandra, olmOCR, etc. — STRUCTURED_OCR_PROMPT family)
│   ├── lightonocr.py              # LightOnOcrAdapter (LightOnOCR, 0-1000 normalized coordinates)
│   └── paddleocr_vl.py            # PaddleOcrVlAdapter (PaddleOCR-VL, task prompt-based)
├── exporters/                     # DocIR → final output conversion
│   └── omnidocbench.py            # export_page(PageIR) → OmniDocBench dict
├── document_service.py            # PDF upload → image conversion → extraction branching (pdfminer/asyncio), re-extraction (re_extract)
├── extraction_service.py          # pdfminer.six fallback extraction (text_block + figure)
├── layout_types.py                # LayoutRegion dataclass, LayoutDetector Protocol
├── docling_layout_service.py      # DoclingLayoutDetector (ibm-granite/granite-docling-258M)
├── pp_doclayout_service.py        # PPDocLayoutV3Detector (PaddlePaddle/PP-DocLayoutV3_safetensors)
├── ocr_pipeline.py                # 2-stage pipeline orchestrator (OcrPipeline, TextOcrProvider)
├── ocr_provider.py                # Prompt constants, bbox_to_poly(), build_omnidocbench_page()
├── gemini_ocr_service.py          # GeminiOcrProvider, GeminiTextOcrProvider
├── vllm_ocr_service.py            # VllmOcrProvider, VllmTextOcrProvider
├── ocr_connection_test.py         # check_gemini/vllm/docling_connection()
├── labeling_service.py            # Annotation CRUD, element add/delete, auto-extraction accept/force-accept, reading order update, relation CRUD
├── attribute_classifier.py        # Page/table/text/formula attribute auto-classification
└── export_service.py              # OmniDocBench JSON assembly
```

- Calls repositories for data access
- Handles file system I/O (PDF storage, image conversion)
- Handles JSON string/dict parsing for JSONB data

### Repositories (Data Access)

Executes raw SQL against PostgreSQL using asyncpg.

```text
src/saegim/repositories/
├── project_repo.py         # INSERT/SELECT projects
├── document_repo.py        # INSERT/SELECT/UPDATE documents
├── page_repo.py            # JSONB operations (jsonb_set, jsonb_agg), relation CRUD (add_relation, delete_relation)
├── user_repo.py            # User CRUD, password hash management, login_id/email uniqueness checks
├── refresh_token_repo.py   # Refresh token CRUD, family-based rotation, theft detection
└── admin_repo.py           # System stats, project stats (admin only)
```

- All functions take `asyncpg.Pool` as the first argument
- SQL parameters use `$1`, `$2`, etc. positional binding
- Returns `asyncpg.Record` objects

## Data Flow

### PDF Upload Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant DS as DocumentService
    participant DR as DocumentRepo
    participant PR as PageRepo
    participant PDF as pypdfium2
    participant EX as ExtractionService
    participant BG as asyncio Task

    C->>R: POST /projects/{id}/documents (PDF file)
    R->>DS: upload_and_convert(pool, project_id, file)
    DS->>DS: Save PDF file (storage/pdfs/)
    DS->>DR: create(pool, project_id, filename, ...)
    DR-->>DS: document record
    DS->>PDF: pdfium.PdfDocument(pdf_path)
    loop Each page
        DS->>PDF: page.render(scale=2.0)
        DS->>DS: Save image (storage/images/)
        DS->>PR: create(pool, document_id, page_no, ...)
    end

    alt default_engine_id == null (pdfminer fallback)
        DS->>EX: extract_page_elements(pdf_path, page_no, scale=2.0)
        Note over EX: pdfminer.six synchronous extraction (text_block + figure)
        DS->>DR: update_status(pool, id, 'ready')
    else default_engine_id != null (asyncio background)
        DS->>DR: update_status(pool, id, 'extracting')
        DS->>BG: asyncio.create_task(_run_ocr_extraction_background(...))
        Note over BG: build_engine_by_id() → to_thread(extract_page())<br/>Update auto_extracted_data per page
        BG->>DR: update_status(pool, id, 'ready' or 'extraction_failed')
    end

    DS-->>R: {id, filename, total_pages, status}
    R-->>C: 201 Created
```

### Annotation Save Flow

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

### Export Flow

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
    Note over ES: Extract page_attribute from annotation_data<br/>Assemble page_info block
    ES-->>R: {project_name, total_pages, data: [...]}
    R-->>C: 200 OK (OmniDocBench JSON)
```

### Auto-Extraction Accept Flow

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

### Document Re-Extraction Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant DS as DocumentService
    participant DR as DocumentRepo
    participant PR as PageRepo
    participant BG as asyncio Task

    C->>R: POST /documents/{id}/re-extract
    R->>DS: re_extract(pool, document_id)
    DS->>DR: get_by_id(pool, document_id)
    DR-->>DS: document record
    DS->>PR: list_for_extraction(pool, document_id)
    PR-->>DS: page records (id, page_no, width, height, image_path)

    alt default_engine_id == null (pdfminer fallback)
        DS->>DS: pdfminer.six synchronous re-extraction
        loop Each page
            DS->>PR: update_auto_extracted_data(pool, page_id, data)
        end
        DS->>DR: update_status(pool, id, 'ready')
    else default_engine_id != null
        DS->>DR: update_status(pool, id, 'extracting')
        DS->>BG: asyncio.create_task(_run_ocr_extraction_background(...))
        Note over BG: Same background extraction logic as upload
    end

    DS-->>R: {id, status}
    R-->>C: 200 OK (DocumentStatusResponse)
```

### Force Accept Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant LS as LabelingService
    participant PR as PageRepo

    C->>R: POST /pages/{id}/force-accept-extraction
    R->>LS: force_accept_auto_extraction(pool, page_id)
    LS->>PR: force_accept_auto_extracted(pool, page_id)
    Note over PR: SET annotation_data = auto_extracted_data<br/>WHERE auto_extracted NOT NULL (ignores existing annotation)
    PR-->>LS: updated record (or None)
    LS-->>R: page data dict (or None → 409)
    R-->>C: 200 OK / 409 Conflict
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Auth Router
    participant D as deps.py
    participant UR as UserRepo
    participant TR as RefreshTokenRepo

    C->>R: POST /auth/login (login_id, password)
    R->>UR: get_by_login_id(pool, login_id)
    UR-->>R: user record (with password_hash)
    R->>R: verify_password(password, hash)
    R->>D: create_access_token(user_id, role)
    R->>D: create_refresh_token(pool, user_id)
    D->>TR: create(pool, user_id, token_hash, family_id)
    R-->>C: {access_token} + Set-Cookie: refresh_token (HttpOnly)
```

```mermaid
sequenceDiagram
    participant C as Client
    participant API as Protected Route
    participant D as deps.py

    C->>API: GET /api/v1/projects (Authorization: Bearer <token>)
    API->>D: get_current_user (Depends)
    D->>D: jwt.decode(token, SECRET_KEY)
    D-->>API: UserResponse(id, role)
    API-->>C: 200 OK (projects list)
```

## Connection Pool Management

The asyncpg connection pool is managed via FastAPI lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = app.state.settings
    await create_pool(
        settings.database_url,
        min_size=settings.db_pool_min_size,  # default: 2
        max_size=settings.db_pool_max_size,  # default: 10
    )
    yield
    await close_pool()
```

- Pool is created at app startup and released at shutdown
- Module-level pool access via `get_pool()` function
- Repository functions receive the pool as an argument to acquire connections

## Static File Serving

Page images are served via FastAPI `StaticFiles`:

```text
/storage/images/{document_id}_p{page_no}.png
```

The `storage/images/` directory is mounted at the `/storage/images` path.

## Core Component Design

### A. PDF Ingestion Service

- Converts PDF pages to high-resolution images (200 DPI or higher)
- Stores the original PDF and converted images
- Auto-generates page_info (page_no, height, width, image_path)

### B. Auto-Extraction Pipeline

- Layout Detection: Extracts bounding box + category_type for block/span elements on each page
- OCR Engine: Fills the text field of text blocks
- Table Recognizer: Generates html/latex fields for table elements
- Formula Recognizer: Generates latex fields for formula elements
- Attribute Classifier: Auto-classifies page/block attributes
- Reading Order Estimator: Auto-assigns order fields
- All extraction results are saved as "draft JSON" and passed to the human review stage

Details: [Extraction Pipeline](../../architecture/extraction-pipeline.md)

### C. Labeling Web Interface (Core)

- **3-layer Hybrid Viewer** (HybridViewer):
  - Layer 1: PDF.js `<canvas>` vector rendering (fallback: `<img>` raster image)
  - Layer 2: Konva.js canvas (image block bbox + selected element)
  - Layer 3: DOM TextOverlay (text blocks -- image fallback mode only)
- **Icon-based compact toolbar**: Select(1)/Draw(2)/Pan(3) + zoom percentage display
- Side panel: Edit category, attribute, text/latex/html of the selected element
- PageNavigator: Navigate pages in multi-page documents with `Q`/`E` keys or arrows
- ExtractionPreview: Display OCR extraction status + accept/dismiss results

Details: [Labeling Workflow](../../architecture/labeling-workflow.md)

### D. Quality Assurance Module

- Auto-validation rules (bbox within image bounds, required attribute checks, etc.)
- Cross-validation: 2+ people independently label the same page, then review discrepancies
- Progress dashboard

### E. Export Service

- Serialization to OmniDocBench JSON format
- Packaging with image files
- Optionally exports in a format compatible with KO-VLM-Benchmark evaluation scripts
