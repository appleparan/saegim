# 데이터베이스

## 개요

saegim은 PostgreSQL을 사용하며, asyncpg로 raw SQL을 직접 실행합니다.
ORM 없이 순수 SQL과 JSONB를 활용합니다.

## 왜 PostgreSQL인가

이 프로젝트는 "웹앱 + 2~5명 동시 접속"이므로 SQLite는 적합하지 않다.

| 요구사항 | SQLite | PostgreSQL |
| --------- | -------- | ------------ |
| 다수 사용자 동시 쓰기 | 단일 Writer lock → 충돌 | 동시 쓰기 안전 |
| JSON 내부 필드 검색/인덱싱 | TEXT 저장, 느린 검색 | JSONB 인덱스, 빠른 쿼리 |
| JSON 부분 업데이트 | 통째로 교체 | jsonb_set()으로 부분 수정 |
| 설치 복잡도 | 파일 하나 | Docker Compose로 1줄 실행 |

레이블링 작업은 자동 저장이 수시로 발생하므로 동시 쓰기 안전성이 필수적이다.

## Page 단위 JSONB 저장 전략

레이블링 데이터 저장 방식에 두 가지 선택지가 있다:

- **전략 A (정규화)**: layout_elements, span_elements, relations 테이블을 별도로 둠
  → JOIN이 복잡하고, OmniDocBench JSON 변환 로직이 필요
- **전략 B (Page 단위 JSONB)**: 페이지 테이블에 annotation_data JSONB 컬럼 하나로 통째 저장
  → OmniDocBench JSON 구조를 그대로 넣고 꺼냄

**전략 B를 채택한다.** 이유:

1. OmniDocBench JSON ↔ DB 간 변환 로직이 거의 없다 (넣고 꺼내면 그대로 Export 포맷)
2. 스키마 확장 시 마이그레이션이 단순하다 (JSON 필드 추가는 DB 마이그레이션 불필요)
3. PostgreSQL JSONB는 내부 필드 인덱싱이 가능하여 "table 카테고리만 찾기" 같은 쿼리도 지원
4. 수천 페이지, 페이지당 10~50KB 수준이면 전체 합쳐도 수십~수백 MB

## 데이터 저장 위치 분리

| 저장 대상 | 위치 | 이유 |
| ----------- | ------ | ------ |
| PDF 원본 | 파일시스템 `./storage/pdfs/` | 바이너리, 수정 안 함 |
| 페이지 이미지 | 파일시스템 `./storage/images/` | 용량 큼, 읽기만 함 |
| 레이블링 JSON | PostgreSQL JSONB (`pages.annotation_data`) | 동시 편집 안전, 쿼리/인덱싱 가능 |
| 자동 추출 원본 | PostgreSQL JSONB (`pages.auto_extracted_data`) | 비교/복원용 보관 |
| 문서 분석 메타데이터 | PostgreSQL JSONB (`documents.analysis_data`) | AI 추출 결과 + 사람 검수 |
| 프로젝트/문서/유저 메타 | PostgreSQL 일반 컬럼 | 관계형 데이터 |
| 최종 내보내기 파일 | 파일시스템 (생성 후 다운로드) | OmniDocBench JSON + 이미지 패키지 |

## ER 다이어그램

```mermaid
erDiagram
    projects ||--o{ documents : has
    documents ||--o{ pages : has
    users ||--o{ pages : "assigned_to"
    pages ||--o{ task_history : has
    users ||--o{ task_history : has

    projects {
        uuid id PK
        varchar name
        text description
        varchar project_type "element_annotation | vqa | ocrag"
        jsonb ocr_config "OCR 엔진 설정 (engine_type)"
        timestamptz created_at
    }

    documents {
        uuid id PK
        uuid project_id FK
        varchar filename
        varchar pdf_path
        int total_pages
        varchar status
        jsonb analysis_data "AI 문서 분석 메타데이터"
        timestamptz created_at
    }

    pages {
        uuid id PK
        uuid document_id FK
        int page_no
        int width
        int height
        varchar image_path
        jsonb annotation_data
        jsonb auto_extracted_data
        varchar status
        uuid assigned_to FK
        timestamptz locked_at
        timestamptz updated_at
    }

    users {
        uuid id PK
        varchar name
        varchar email
        varchar role
        timestamptz created_at
    }

    task_history {
        uuid id PK
        uuid page_id FK
        uuid user_id FK
        varchar action
        jsonb snapshot
        timestamptz created_at
    }
```

## 테이블 상세

### projects

프로젝트 단위로 문서를 관리합니다.

| 컬럼 | 타입 | 기본값 | 설명 |
| ------ | ------ | -------- | ------ |
| `id` | UUID PK | `uuid_generate_v4()` | 프로젝트 ID |
| `name` | VARCHAR(255) | - | 프로젝트 이름 |
| `description` | TEXT | `''` | 프로젝트 설명 |
| `project_type` | VARCHAR(30) | `'element_annotation'` | 프로젝트 유형: `element_annotation`, `vqa`, `ocrag` |
| `ocr_config` | JSONB | `NULL` | OCR 엔진 설정 (engine_type + 타입별 세부 설정) |
| `created_at` | TIMESTAMPTZ | `NOW()` | 생성 시각 |

### documents

PDF 문서 정보를 저장합니다.

| 컬럼 | 타입 | 기본값 | 설명 |
| ------ | ------ | -------- | ------ |
| `id` | UUID PK | `uuid_generate_v4()` | 문서 ID |
| `project_id` | UUID FK | - | 소속 프로젝트 |
| `filename` | VARCHAR(512) | - | 원본 파일명 |
| `pdf_path` | VARCHAR(1024) | - | PDF 저장 경로 |
| `total_pages` | INT | `0` | 총 페이지 수 |
| `status` | VARCHAR(20) | `'uploading'` | 문서 상태 |
| `analysis_data` | JSONB | `'{}'` | AI 문서 분석 메타데이터 (Overview, Core Idea, Key Figures, Limitations) |
| `created_at` | TIMESTAMPTZ | `NOW()` | 생성 시각 |

**status 값:**

| 값 | 설명 |
| ---- | ------ |
| `uploading` | 업로드 중 |
| `processing` | 이미지 변환 중 |
| `extracting` | OCR 추출 중 (asyncio 백그라운드) |
| `ready` | 변환/추출 완료, 레이블링 가능 |
| `error` | 변환 실패 |
| `extraction_failed` | OCR 추출 실패 |

**인덱스:**

- `idx_documents_project_id` - `project_id` (프로젝트별 조회)

### pages

페이지별 어노테이션 데이터를 저장합니다. 핵심 테이블입니다.

| 컬럼 | 타입 | 기본값 | 설명 |
| ------ | ------ | -------- | ------ |
| `id` | UUID PK | `uuid_generate_v4()` | 페이지 ID |
| `document_id` | UUID FK | - | 소속 문서 |
| `page_no` | INT | - | 페이지 번호 (1부터) |
| `width` | INT | `0` | 이미지 너비 (px) |
| `height` | INT | `0` | 이미지 높이 (px) |
| `image_path` | VARCHAR(1024) | `''` | 이미지 경로 |
| `annotation_data` | JSONB | `'{}'` | OmniDocBench 어노테이션 |
| `auto_extracted_data` | JSONB | `NULL` | 자동 추출 결과 |
| `status` | VARCHAR(20) | `'pending'` | 레이블링 상태 |
| `assigned_to` | UUID FK | `NULL` | 할당된 사용자 |
| `locked_at` | TIMESTAMPTZ | `NULL` | 잠금 시각 |
| `updated_at` | TIMESTAMPTZ | `NOW()` | 최종 수정 시각 |

**status 값:**

| 값 | 설명 |
| ---- | ------ |
| `pending` | 미할당/미시작 |
| `in_progress` | 레이블링 진행 중 |
| `submitted` | 제출 완료 |
| `reviewed` | 검토 완료 |

**인덱스:**

- `idx_pages_document_id` - `document_id` (문서별 조회)
- `idx_pages_status` - `status` (상태별 필터링)
- `idx_pages_assigned_to` - `assigned_to` (사용자별 할당 조회)
- `idx_pages_annotation` - `annotation_data` GIN (JSONB 검색)

### users

사용자 정보를 저장합니다.

| 컬럼 | 타입 | 기본값 | 설명 |
| ------ | ------ | -------- | ------ |
| `id` | UUID PK | `uuid_generate_v4()` | 사용자 ID |
| `name` | VARCHAR(255) | - | 이름 |
| `email` | VARCHAR(255) UNIQUE | - | 이메일 |
| `role` | VARCHAR(20) | `'annotator'` | 역할 |
| `created_at` | TIMESTAMPTZ | `NOW()` | 생성 시각 |

**role 값:** `admin`, `annotator`, `reviewer`

### task_history

작업 이력을 추적합니다.

| 컬럼 | 타입 | 기본값 | 설명 |
| ------ | ------ | -------- | ------ |
| `id` | UUID PK | `uuid_generate_v4()` | 이력 ID |
| `page_id` | UUID FK | - | 대상 페이지 |
| `user_id` | UUID FK | - | 작업 사용자 |
| `action` | VARCHAR(20) | - | 작업 유형 |
| `snapshot` | JSONB | `NULL` | 시점 스냅샷 |
| `created_at` | TIMESTAMPTZ | `NOW()` | 발생 시각 |

**action 값:** `assigned`, `started`, `saved`, `submitted`, `approved`, `rejected`

## annotation_data JSONB 구조

`pages.annotation_data` 컬럼 안에 들어가는 JSON이 곧 OmniDocBench의 한 페이지 데이터다.
Export 시 이 컬럼을 모아서 배열로 만들면 바로 최종 JSON이 된다.

```jsonc
{
  "layout_dets": [
    {
      "category_type": "text_block",
      "poly": [x1,y1, x2,y2, x3,y3, x4,y4],
      "ignore": false, "order": 0, "anno_id": 0,
      "text": "...", "latex": "...", "html": "...",
      "attribute": { /* 카테고리별 속성 */ },
      "line_with_spans": [ /* Span-level 하위 요소 */ ]
    }
  ],
  "page_attribute": {
    "data_source": "academic_literature", "language": "ko",
    "layout": "double_column",
    "watermark": false, "fuzzy_scan": false, "colorful_background": false
  },
  "extra": {
    "relation": [{ "source_anno_id": 3, "target_anno_id": 4, "relation_type": "parent_son" }]
  }
}
```

타입 정의: [saegim-frontend/src/lib/types/omnidocbench.ts](../../saegim-frontend/src/lib/types/omnidocbench.ts)

스키마 상세: [데이터 스키마](../../architecture/data-schema.md)

## Export 로직

구현: `saegim-backend/src/saegim/services/export_service.py`

annotation_data를 OmniDocBench 구조로 저장했기 때문에,
Export는 사실상 **DB에서 꺼내서 page_info를 붙이는 것**이 전부다.

## JSONB 연산

### annotation_data 전체 업데이트

```sql
UPDATE pages
SET annotation_data = $1::jsonb, updated_at = NOW()
WHERE id = $2
```

### page_attribute 부분 업데이트

`jsonb_set`으로 `annotation_data` 내부의 `page_attribute`만 교체합니다:

```sql
UPDATE pages
SET annotation_data = jsonb_set(
    COALESCE(annotation_data, '{}'::jsonb),
    '{page_attribute}',
    $1::jsonb
), updated_at = NOW()
WHERE id = $2
```

### layout_dets에 요소 추가

기존 배열에 새 요소를 `||` 연산자로 append합니다:

```sql
UPDATE pages
SET annotation_data = jsonb_set(
    COALESCE(annotation_data, '{"layout_dets": []}'::jsonb),
    '{layout_dets}',
    COALESCE(annotation_data->'layout_dets', '[]'::jsonb) || $1::jsonb
), updated_at = NOW()
WHERE id = $2
```

### layout_dets에서 요소 삭제

`jsonb_agg`와 `jsonb_array_elements`로 `anno_id`가 일치하지 않는 요소만 필터링합니다:

```sql
UPDATE pages
SET annotation_data = jsonb_set(
    annotation_data,
    '{layout_dets}',
    (
        SELECT COALESCE(jsonb_agg(elem), '[]'::jsonb)
        FROM jsonb_array_elements(annotation_data->'layout_dets') AS elem
        WHERE (elem->>'anno_id')::int != $1
    )
), updated_at = NOW()
WHERE id = $2
```

### auto_extracted_data 수락 (annotation_data로 복사)

`auto_extracted_data`를 `annotation_data`로 복사합니다.
기존 annotation이 비어있을 때만 동작합니다:

```sql
UPDATE pages
SET annotation_data = auto_extracted_data, updated_at = NOW()
WHERE id = $1
  AND auto_extracted_data IS NOT NULL
  AND (
    annotation_data IS NULL
    OR annotation_data = '{}'::jsonb
    OR NOT (annotation_data ? 'layout_dets')
    OR jsonb_array_length(COALESCE(annotation_data->'layout_dets', '[]'::jsonb)) = 0
  )
RETURNING ...
```

이미 `annotation_data.layout_dets`에 요소가 있으면 업데이트하지 않고 `NULL`을 반환합니다
(API에서 409 Conflict로 처리).

## analysis_data JSONB 구조 (Phase 4a)

`documents.analysis_data`에 저장되는 문서 분석 메타데이터입니다.
외부 AI(VLM/LLM)가 자동 추출하고 사람이 검수합니다.

```json
{
  "overview": {
    "title": "논문 제목",
    "authors": ["저자 1", "저자 2"],
    "venue": "학회/저널",
    "summary": "1~2문장 요약",
    "tags": ["keyword1", "keyword2"]
  },
  "core_idea": {
    "problem": "해결하려는 문제",
    "approach": "접근 방법",
    "novelty": "핵심 기여/차별점",
    "key_equations": [
      {"page": 3, "anno_id": 7, "description": "수식 설명"}
    ]
  },
  "key_figures": [
    {
      "page": 2,
      "anno_id": 3,
      "label": "Figure 1",
      "why_important": "이 그림이 중요한 이유",
      "rank": 1
    }
  ],
  "limitations": {
    "stated": ["논문에서 명시한 한계"],
    "implicit": ["암시적 한계"],
    "future_work": ["향후 연구 방향"]
  },
  "_meta": {
    "model": "claude-sonnet-4-5-20250929",
    "extracted_at": "2026-02-15T10:00:00Z",
    "reviewed": false,
    "reviewed_by": null
  }
}
```

`key_figures`의 `page` + `anno_id`가 해당 문서 pages의 `annotation_data.layout_dets[]`를
참조하여 document-level과 page-level을 연결합니다.

### analysis_data 업데이트

```sql
-- 전체 업데이트
UPDATE documents
SET analysis_data = $1::jsonb
WHERE id = $2

-- 특정 섹션만 업데이트 (예: key_figures)
UPDATE documents
SET analysis_data = jsonb_set(
    COALESCE(analysis_data, '{}'::jsonb),
    '{key_figures}',
    $1::jsonb
)
WHERE id = $2
```

## 마이그레이션

SQL 파일 기반으로 수동 관리합니다:

```text
migrations/
└── 001_init.sql  # 전체 스키마 (projects, users, documents, pages, task_history)
```

실행 방법:

```bash
# psql로 직접 실행
psql -U labeling -d labeling -f migrations/001_init.sql
```

프로그래밍 방식 실행 (`database.run_migrations`):

```python
from saegim.core.database import run_migrations

await run_migrations(pool, migrations_dir='migrations')
```

이 함수는 `migrations/` 디렉토리의 `.sql` 파일을 이름순으로 정렬하여 순차 실행합니다.
