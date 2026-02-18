# API 엔드포인트

모든 엔드포인트는 `/api/v1` 접두사를 사용합니다.

## Health

### `GET /api/v1/health`

서버 상태 확인.

**응답:**

```json
{"status": "healthy"}
```

### `GET /api/v1/health/ready`

서비스 준비 상태 확인.

**응답:**

```json
{"status": "ready"}
```

---

## Projects

### `POST /api/v1/projects`

프로젝트 생성.

**요청 Body:**

```json
{
  "name": "한국어 논문 벤치마크",
  "description": "2024년 한국어 학술 논문 레이블링 프로젝트"
}
```

**응답:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "한국어 논문 벤치마크",
  "description": "2024년 한국어 학술 논문 레이블링 프로젝트",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### `GET /api/v1/projects`

프로젝트 목록 조회.

**응답:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "한국어 논문 벤치마크",
    "description": "...",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### `GET /api/v1/projects/{project_id}`

프로젝트 상세 조회.

**응답:** `200 OK` | `404 Not Found`

### `GET /api/v1/projects/{project_id}/ocr-config`

프로젝트의 OCR 설정 조회. 미설정 시 기본값 `{"layout_provider": "pymupdf"}` 반환.

**응답:** `200 OK`

```json
{
  "layout_provider": "ppstructure",
  "ocr_provider": "gemini",
  "ppstructure": { "host": "localhost", "port": 18811 },
  "gemini": { "api_key": "...", "model": "gemini-2.0-flash" }
}
```

### `PUT /api/v1/projects/{project_id}/ocr-config`

프로젝트 OCR 설정 업데이트 (2단계 파이프라인).

- `layout_provider: ppstructure` → `ocr_provider` + `ppstructure` config 필수
- `ocr_provider: gemini` → `gemini` config 필수
- `ocr_provider: olmocr` → `vllm` config 필수
- `layout_provider: pymupdf` → 추가 설정 불필요

**요청 Body:**

```json
{
  "layout_provider": "ppstructure",
  "ocr_provider": "olmocr",
  "ppstructure": { "host": "gpu-server", "port": 18811 },
  "vllm": { "host": "gpu-server", "port": 8000, "model": "allenai/olmOCR-2-7B-1025" }
}
```

**응답:** `200 OK` | `422 Unprocessable Entity`

### `POST /api/v1/projects/{project_id}/ocr-config/test`

OCR 파이프라인 연결 테스트. PP-StructureV3 서버 + OCR 프로바이더 연결 확인.

**요청 Body:** `PUT /ocr-config`과 동일한 형식.

**응답:** `200 OK`

```json
{
  "success": true,
  "message": "Connected to PP-StructureV3 at localhost:18811 | Connected to Gemini (Gemini 2.0 Flash)"
}
```

---

## Documents

### `POST /api/v1/projects/{project_id}/documents`

PDF 문서 업로드. 업로드된 PDF는 자동으로 페이지별 이미지로 변환되고,
PyMuPDF로 텍스트/이미지 블록을 추출하여 `auto_extracted_data`에 저장합니다.

**요청:** `multipart/form-data`

| 필드 | 타입 | 설명 |
| ------ | ------ | ------ |
| `file` | `UploadFile` | PDF 파일 (application/pdf만 허용) |

**응답:** `201 Created`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "filename": "paper.pdf",
  "total_pages": 12,
  "status": "ready"
}
```

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 프로젝트를 찾을 수 없음 |
| `400` | PDF 파일이 아님 |

### `GET /api/v1/documents/{document_id}`

문서 상세 조회.

**응답:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "paper.pdf",
  "pdf_path": "/storage/pdfs/...",
  "total_pages": 12,
  "status": "ready",
  "created_at": "2025-01-15T10:35:00Z"
}
```

### `GET /api/v1/documents/{document_id}/pages`

문서의 페이지 목록 조회 (어노테이션 데이터 미포함, 경량).

**응답:** `200 OK`

```json
[
  {
    "id": "770e8400-...",
    "page_no": 1,
    "width": 1200,
    "height": 1600,
    "status": "pending",
    "assigned_to": null,
    "updated_at": "2025-01-15T10:35:00Z"
  }
]
```

---

## Pages (레이블링)

### `GET /api/v1/pages/{page_id}`

페이지 데이터 로드 (어노테이션 데이터 포함).

**응답:** `200 OK`

```json
{
  "id": "770e8400-...",
  "document_id": "660e8400-...",
  "page_no": 1,
  "width": 1200,
  "height": 1600,
  "image_path": "/storage/images/..._p1.png",
  "annotation_data": {
    "layout_dets": [...],
    "page_attribute": {...},
    "extra": {"relation": []}
  },
  "auto_extracted_data": null,
  "status": "pending",
  "assigned_to": null,
  "updated_at": "2025-01-15T10:35:00Z"
}
```

### `PUT /api/v1/pages/{page_id}`

어노테이션 데이터 전체 저장.

**요청 Body:**

```json
{
  "annotation_data": {
    "layout_dets": [
      {
        "category_type": "title",
        "poly": [100, 50, 500, 50, 500, 100, 100, 100],
        "text": "논문 제목",
        "anno_id": 0,
        "order": 0
      }
    ],
    "page_attribute": {
      "language": "ko",
      "layout": "single_column"
    },
    "extra": {"relation": []}
  }
}
```

**응답:** `200 OK` - 업데이트된 페이지 데이터

### `PUT /api/v1/pages/{page_id}/attributes`

페이지 속성만 저장 (`annotation_data.page_attribute`를 `jsonb_set`으로 부분 업데이트).

**요청 Body:**

```json
{
  "page_attribute": {
    "data_source": "academic_literature",
    "language": "ko",
    "layout": "single_column",
    "watermark": false,
    "fuzzy_scan": false,
    "colorful_background": false
  }
}
```

**응답:** `200 OK` - 업데이트된 페이지 데이터

### `POST /api/v1/pages/{page_id}/elements`

새 레이아웃 요소 추가. `anno_id`와 `order`는 서버에서 자동 할당됩니다.

**요청 Body:**

```json
{
  "category_type": "text_block",
  "poly": [100, 200, 500, 200, 500, 400, 100, 400],
  "text": "본문 텍스트 내용"
}
```

!!! note "poly 필드"
    `poly`는 정확히 8개의 숫자(4개 꼭짓점의 x,y 좌표)를 포함해야 합니다.
    8개가 아닌 경우 `422 Unprocessable Entity`를 반환합니다.

**응답:** `201 Created` - 업데이트된 페이지 데이터

### `DELETE /api/v1/pages/{page_id}/elements/{anno_id}`

`anno_id`로 레이아웃 요소 삭제.

**응답:** `200 OK` | `404 Not Found`

### `POST /api/v1/pages/{page_id}/accept-extraction`

자동 추출 결과(`auto_extracted_data`)를 `annotation_data`로 복사합니다.
`annotation_data`가 비어있고 `auto_extracted_data`가 존재할 때만 동작합니다.

**응답:** `200 OK` - 업데이트된 페이지 데이터

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `409` | `auto_extracted_data`가 없거나, `annotation_data`에 이미 요소가 존재함 |

---

## Users

### `POST /api/v1/users`

사용자 생성.

**요청 Body:**

```json
{
  "name": "김철수",
  "email": "chulsoo@example.com",
  "role": "annotator"
}
```

| 필드 | 타입 | 필수 | 설명 |
| ------ | ------ | ------ | ------ |
| `name` | string | O | 사용자 이름 |
| `email` | EmailStr | O | 이메일 (고유) |
| `role` | string | X | `admin`, `annotator`, `reviewer` (기본값: `annotator`) |

**응답:** `201 Created`

### `GET /api/v1/users`

사용자 목록 조회.

**응답:** `200 OK`

```json
[
  {
    "id": "880e8400-...",
    "name": "김철수",
    "email": "chulsoo@example.com",
    "role": "annotator",
    "created_at": "2025-01-15T10:00:00Z"
  }
]
```

---

## Export

### `POST /api/v1/projects/{project_id}/export`

프로젝트의 모든 페이지를 OmniDocBench JSON 포맷으로 내보내기.

**응답:** `200 OK`

```json
{
  "project_name": "한국어 논문 벤치마크",
  "total_pages": 24,
  "data": [
    {
      "layout_dets": [...],
      "extra": {"relation": []},
      "page_info": {
        "page_no": 1,
        "height": 1600,
        "width": 1200,
        "image_path": "/storage/images/..._p1.png",
        "page_attribute": {
          "data_source": "academic_literature",
          "language": "ko",
          "layout": "single_column"
        }
      }
    }
  ]
}
```

!!! info "내보내기 포맷"
    내보내기 시 `annotation_data.page_attribute`는 `page_info.page_attribute`로 이동합니다.
    이는 OmniDocBench 표준 포맷을 따르기 위함입니다.

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 프로젝트를 찾을 수 없음 |
