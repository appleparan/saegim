# API Endpoints

All endpoints use the `/api/v1` prefix.

**Authentication**: All endpoints except Health and Auth require
an `Authorization: Bearer <access_token>` header.
Admin endpoints additionally require the `admin` role.

## Health

### `GET /api/v1/health`

Check server status.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "message": "Service is running",
  "version": "0.1.0"
}
```

### `GET /api/v1/health/ready`

Check service readiness (including DB connection).

**Response:** `200 OK`

```json
{
  "status": "ready",
  "message": "All systems operational",
  "version": "0.1.0"
}
```

---

## Auth

Authentication-related endpoints. All are unauthenticated (except credentials update).

### `GET /api/v1/auth/check-login-id`

Check login ID availability.

**Query Parameters:**

| Parameter | Type | Description |
| -------- | ---- | ---- |
| `login_id` | string | Login ID to check |

**Response:** `200 OK`

```json
{ "available": true }
```

### `POST /api/v1/auth/register`

Register a new user. The first user is automatically assigned the `admin` role.

**Request Body:**

```json
{
  "name": "김철수",
  "login_id": "chulsoo",
  "email": "chulsoo@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

Set-Cookie: `refresh_token` (HttpOnly, Secure, SameSite=Lax)

### `POST /api/v1/auth/login`

Log in.

**Request Body:**

```json
{
  "login_id": "chulsoo",
  "password": "securepassword123"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

Set-Cookie: `refresh_token` (HttpOnly, Secure, SameSite=Lax)

**Errors:**

| Code | Description |
| ---- | ---- |
| `401` | Invalid login ID or password |
| `403` | Deactivated account |

### `POST /api/v1/auth/refresh`

Issue a new access token using a refresh token. Token rotation is applied.

**Request:** Uses `refresh_token` from Cookie

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

Set-Cookie: new `refresh_token`

**Errors:**

| Code | Description |
| ---- | ---- |
| `401` | Invalid or expired refresh token |

### `POST /api/v1/auth/logout`

Revoke the current refresh token family.

**Request:** Uses `refresh_token` from Cookie

**Response:** `204 No Content`

### `PATCH /api/v1/auth/me/credentials`

Change login ID, email, or password. **Authentication required.**

**Request Body:**

```json
{
  "login_id": "new_login_id",
  "email": "new@example.com",
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

All fields are optional. `current_password` is required when providing `new_password`.
All sessions are invalidated on change (refresh token hard delete).

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

Set-Cookie: new `refresh_token` (all existing sessions invalidated)

---

## Admin

Admin-only endpoints. Requires the `admin` role.

### `GET /api/v1/admin/users`

Retrieve the full user list.

**Response:** `200 OK`

```json
[
  {
    "id": "880e8400-...",
    "name": "김철수",
    "login_id": "chulsoo",
    "email": "chulsoo@example.com",
    "role": "annotator",
    "is_active": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
]
```

### `PATCH /api/v1/admin/users/{user_id}`

Change user role or deactivate.

**Request Body:**

```json
{
  "role": "reviewer",
  "is_active": false
}
```

All fields are optional.

**Response:** `200 OK`

### `GET /api/v1/admin/projects`

Full project list (with statistics).

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-...",
    "name": "한국어 논문 벤치마크",
    "description": "...",
    "created_at": "2025-01-15T10:30:00Z",
    "member_count": 3,
    "total_pages": 120,
    "completed_pages": 45,
    "submitted_pages": 10
  }
]
```

### `GET /api/v1/admin/stats`

System-wide statistics.

**Response:** `200 OK`

```json
{
  "total_users": 10,
  "active_users": 8,
  "total_projects": 5,
  "total_pages": 500,
  "completed_pages": 200,
  "submitted_pages": 50,
  "completion_rate": 40.0
}
```

---

## Projects

### `POST /api/v1/projects`

Create a project.

**Request Body:**

```json
{
  "name": "한국어 논문 벤치마크",
  "description": "2024년 한국어 학술 논문 레이블링 프로젝트"
}
```

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "한국어 논문 벤치마크",
  "description": "2024년 한국어 학술 논문 레이블링 프로젝트",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### `GET /api/v1/projects`

List projects.

**Response:** `200 OK`

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

Get project details.

**Response:** `200 OK` | `404 Not Found`

### `DELETE /api/v1/projects/{project_id}`

Delete a project. Related documents, pages, and images are also deleted.

**Response:** `204 No Content` | `404 Not Found`

### `GET /api/v1/projects/{project_id}/ocr-config`

Retrieve the project's OCR engine configuration. Returns an empty engines dict if no engines are registered.

**Response:** `200 OK`

```json
{
  "default_engine_id": "gemini-flash",
  "engines": {
    "gemini-flash": {
      "engine_type": "commercial_api",
      "name": "Gemini Flash",
      "config": { "provider": "gemini", "api_key": "...", "model": "gemini-3-flash-preview", "prompt": "" }
    },
    "vllm-chandra": {
      "engine_type": "vllm",
      "name": "vLLM Chandra",
      "config": { "host": "gpu-server", "port": 8000, "model": "datalab-to/chandra" }
    }
  },
  "env_gemini_api_key": "AIza..."
}
```

### `POST /api/v1/projects/{project_id}/ocr-config/engines`

Register a new engine instance. Multiple instances of the same engine type can be registered.

**Request Body:**

vLLM engine example:

```json
{
  "engine_type": "vllm",
  "name": "vLLM olmOCR",
  "config": { "host": "gpu-server-2", "port": 8000, "model": "allenai/olmOCR-2-7B-1025-FP8" }
}
```

Split Pipeline engine example (PP-DocLayoutV3 + vLLM):

```json
{
  "engine_type": "split_pipeline",
  "name": "PP-DocLayoutV3 + vLLM",
  "config": {
    "layout_provider": "pp_doclayout",
    "ocr_provider": "vllm",
    "ocr_host": "gpu-server-1",
    "ocr_port": 8000,
    "ocr_model": "allenai/olmOCR-2-7B-1025-FP8"
  }
}
```

!!! note "`layout_provider` options"
    The `layout_provider` for the `split_pipeline` engine supports `"docling"` (default) or
    `"pp_doclayout"` (PP-DocLayoutV3).

**Response:** `201 Created` (updated OcrConfigResponse) | `409 Conflict` (engine_id collision)

### `PUT /api/v1/projects/{project_id}/ocr-config/engines/{engine_id}`

Modify the name or configuration of an existing engine instance.

**Request Body:**

```json
{
  "name": "vLLM Chandra (updated)",
  "config": { "host": "new-server", "port": 8000, "model": "datalab-to/chandra" }
}
```

**Response:** `200 OK` | `404 Not Found`

### `DELETE /api/v1/projects/{project_id}/ocr-config/engines/{engine_id}`

Delete an engine instance. If the deleted engine was the default engine, `default_engine_id` is reset to null.

**Response:** `200 OK` (updated OcrConfigResponse) | `404 Not Found`

### `PUT /api/v1/projects/{project_id}/ocr-config/default-engine`

Set the default engine for full-page OCR. If null, falls back to pdfminer.

**Request Body:**

```json
{ "engine_id": "gemini-flash" }
```

**Response:** `200 OK` | `404 Not Found`

### `POST /api/v1/projects/{project_id}/ocr-config/test`

Test connection to a specific engine instance.

**Request Body:**

```json
{ "engine_id": "vllm-chandra" }
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Connected to vLLM (datalab-to/chandra)"
}
```

### `GET /api/v1/projects/{project_id}/available-engines`

List engines available for per-element text extraction.
Returns all registered engines (pdfminer is excluded as it does not support region-level extraction).

**Response:** `200 OK`

```json
{
  "engines": [
    { "engine_id": "gemini-flash", "engine_type": "commercial_api", "name": "Gemini Flash" },
    { "engine_id": "vllm-chandra", "engine_type": "vllm", "name": "vLLM Chandra" }
  ]
}
```

---

## Documents

### `GET /api/v1/projects/{project_id}/documents`

List documents in a project.

**Response:** `200 OK`

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "filename": "paper.pdf",
    "total_pages": 12,
    "status": "ready",
    "created_at": "2025-01-15T10:35:00Z"
  }
]
```

### `POST /api/v1/projects/{project_id}/documents`

Upload a PDF document. The uploaded PDF is automatically converted to per-page images,
and text/image blocks are extracted using pdfminer.six and stored in `auto_extracted_data`.

**Request:** `multipart/form-data`

| Field | Type | Description |
| ------ | ------ | ------ |
| `file` | `UploadFile` | PDF file (only application/pdf allowed) |

**Response:** `201 Created`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "filename": "paper.pdf",
  "total_pages": 12,
  "status": "ready"
}
```

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Project not found |
| `400` | Not a PDF file |

### `GET /api/v1/documents/{document_id}`

Get document details.

**Response:** `200 OK`

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

### `DELETE /api/v1/documents/{document_id}`

Delete a document. Related pages and images are also deleted.

**Response:** `204 No Content` | `404 Not Found`

### `GET /api/v1/documents/{document_id}/status`

Get document processing status and progress.

**Response:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "extracting",
  "total_pages": 12,
  "processed_pages": 5
}
```

### `POST /api/v1/documents/{document_id}/re-extract`

Re-extract all pages of the document using the current project's OCR engine.
Existing `annotation_data` is preserved; only `auto_extracted_data` is updated.
The pdfminer engine is processed synchronously, while other engines run as asynchronous background tasks.

**Response:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "extracting",
  "total_pages": 12,
  "processed_pages": 0
}
```

!!! note "Status transitions"
    For the pdfminer engine, `status: "ready"` is returned after synchronous processing.
    For other engines, `status: "extracting"` is returned, and changes to `ready` after extraction completes.
    Progress can be polled via `GET /documents/{id}/status`.

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Document not found |
| `409` | Extraction already in progress |

### `GET /api/v1/documents/{document_id}/pages`

List pages of a document (without annotation data, lightweight).

**Response:** `200 OK`

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

## Pages (Labeling)

### `GET /api/v1/pages/{page_id}`

Load page data (including annotation data).

**Response:** `200 OK`

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

Save full annotation data.

**Request Body:**

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

**Response:** `200 OK` - Updated page data

### `PUT /api/v1/pages/{page_id}/attributes`

Save page attributes only (partial update of `annotation_data.page_attribute` using `jsonb_set`).

**Request Body:**

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

**Response:** `200 OK` - Updated page data

### `POST /api/v1/pages/{page_id}/elements`

Add a new layout element. `anno_id` and `order` are automatically assigned by the server.

**Request Body:**

```json
{
  "category_type": "text_block",
  "poly": [100, 200, 500, 200, 500, 400, 100, 400],
  "text": "본문 텍스트 내용"
}
```

!!! note "poly field"
    `poly` must contain exactly 8 numbers (x,y coordinates of 4 vertices).
    Returns `422 Unprocessable Entity` if not exactly 8.

**Response:** `201 Created` - Updated page data

### `DELETE /api/v1/pages/{page_id}/elements/{anno_id}`

Delete a layout element by `anno_id`.

**Response:** `200 OK` | `404 Not Found`

### `POST /api/v1/pages/{page_id}/accept-extraction`

Copy auto-extraction results (`auto_extracted_data`) to `annotation_data`.
Only works when `annotation_data` is empty and `auto_extracted_data` exists.

**Response:** `200 OK` - Updated page data

**Errors:**

| Code | Description |
| ------ | ------ |
| `409` | `auto_extracted_data` is missing, or `annotation_data` already has elements |

### `POST /api/v1/pages/{page_id}/force-accept-extraction`

Force-copy auto-extraction results (`auto_extracted_data`) to `annotation_data`.
Unlike `accept-extraction`, this overwrites even if `annotation_data` already has elements.
Used to replace existing annotations with new OCR results after re-extraction.

**Response:** `200 OK` - Updated page data

**Errors:**

| Code | Description |
| ------ | ------ |
| `409` | `auto_extracted_data` is missing |

### `POST /api/v1/pages/{page_id}/extract-text`

Extract text from a specified region using an OCR engine.
If `engine_id` is specified, that engine instance is used; otherwise, the project's default engine is used.

**Request Body:**

```json
{
  "poly": [100, 200, 500, 200, 500, 400, 100, 400],
  "category_type": "text_block",
  "engine_id": "vllm-chandra"
}
```

| Field | Type | Required | Description |
| ------ | ------ | ------ | ------ |
| `poly` | `list[float]` | Yes | 8 coordinates (4 vertices) |
| `category_type` | string | No | Category type (default: `text_block`) |
| `engine_id` | string | No | Engine instance ID override (uses project default if omitted) |

**Response:** `200 OK`

```json
{
  "text": "추출된 텍스트 내용"
}
```

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Page not found |
| `502` | OCR provider error |
| `503` | OCR provider not configured |

### `PUT /api/v1/pages/{page_id}/reading-order`

Update reading order. Changes element order via `anno_id` to `order` mapping.

**Request Body:**

```json
{
  "order_map": {
    "0": 2,
    "1": 0,
    "2": 1
  }
}
```

| Field | Type | Description |
| ------ | ------ | ------ |
| `order_map` | `dict[string, int]` | anno_id (string) to order (integer) mapping. Duplicate order values and negative values are not allowed |

**Response:** `200 OK` - Updated page data

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Page not found, or order_map contains non-existent anno_id |
| `422` | Duplicate order values or negative values |

### `POST /api/v1/pages/{page_id}/relations`

Add a relation between elements. Stored in JSONB `extra.relation[]`.

**Request Body:**

```json
{
  "source_anno_id": 3,
  "target_anno_id": 4,
  "relation_type": "figure_caption"
}
```

| Field | Type | Required | Description |
| ------ | ------ | ------ | ------ |
| `source_anno_id` | int (>=0) | Yes | Source element anno_id |
| `target_anno_id` | int (>=0) | Yes | Target element anno_id |
| `relation_type` | string | No | Relation type (default: `parent_son`) |

**Relation types:**

| Value | Description |
| ------ | ------ |
| `parent_son` | Parent-child relationship |
| `figure_caption` | Figure-caption |
| `table_caption` | Table-caption |
| `table_footnote` | Table-footnote |
| `equation_caption` | Equation-caption |
| `code_caption` | Code-caption |

**Response:** `201 Created` - Updated page data

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Page not found |
| `409` | Self-reference, duplicate relation, or non-existent element |

### `DELETE /api/v1/pages/{page_id}/relations`

Delete a relation between elements.

**Request Body:**

```json
{
  "source_anno_id": 3,
  "target_anno_id": 4
}
```

**Response:** `200 OK` - Updated page data

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Page not found |

---

## Users

### `GET /api/v1/users`

List users (authentication required).

**Authentication:** Bearer Token required

**Response:** `200 OK`

---

## Export

### `POST /api/v1/projects/{project_id}/export`

Export all pages of a project in OmniDocBench JSON format.

**Response:** `200 OK`

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

!!! info "Export format"
    During export, `annotation_data.page_attribute` is moved to `page_info.page_attribute`.
    This follows the OmniDocBench standard format.

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Project not found |

### `GET /api/v1/projects/{project_id}/export/zip`

Export all pages of a project as an OmniDocBench-compatible ZIP archive.

ZIP structure:

```text
{project_name}_{datetime}.zip
├── annos.json
└── images/
    └── {document_name}/
        ├── page_001.png
        ├── page_002.png
        └── ...
```

**Response:** `200 OK` (application/zip)

- `Content-Disposition: attachment; filename="{project_name}_{YYYYMMdd_HHmmss}.zip"`

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Project not found |

### `GET /api/v1/projects/{project_id}/documents/{document_id}/export/zip`

Export a single document as an OmniDocBench-compatible ZIP archive.

**Response:** `200 OK` (application/zip)

- `Content-Disposition: attachment; filename="{document_name}_{YYYYMMdd_HHmmss}.zip"`

**Errors:**

| Code | Description |
| ------ | ------ |
| `404` | Document not found or does not belong to the project |

---

## Project Progress API

### `GET /api/v1/projects/{project_id}/progress`

Retrieve overall project progress. Includes page counts by status, per-document progress, and per-member activity.

**Authentication**: Project member (member / admin)

**Response:** `200 OK`

```json
{
  "total_pages": 120,
  "completion_rate": 37.5,
  "status_breakdown": {
    "pending": 30,
    "in_progress": 20,
    "submitted": 25,
    "reviewed": 45
  },
  "documents": [
    {
      "document_id": "660e8400-...",
      "filename": "paper.pdf",
      "total_pages": 12,
      "status_counts": {
        "pending": 3,
        "in_progress": 2,
        "submitted": 3,
        "reviewed": 4
      },
      "completion_rate": 33.33
    }
  ],
  "members": [
    {
      "user_id": "880e8400-...",
      "user_name": "김철수",
      "role": "annotator",
      "assigned_pages": 10,
      "in_progress_pages": 3,
      "submitted_pages": 4,
      "reviewed_pages": 3
    }
  ]
}
```

**Errors:**

| Code | Description |
| ---- | ---- |
| `401` | Not authenticated |
| `403` | Not a project member |

---

## Project Member Management API

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ---- |
| `GET` | `/api/v1/projects/{id}/members` | member | List members |
| `POST` | `/api/v1/projects/{id}/members` | owner/admin | Invite member |
| `PATCH` | `/api/v1/projects/{id}/members/{user_id}` | owner/admin | Change member role |
| `DELETE` | `/api/v1/projects/{id}/members/{user_id}` | owner/admin | Remove member |

## Task Workflow API

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ---- |
| `POST` | `/api/v1/pages/{id}/assign` | owner/admin | Assign page |
| `POST` | `/api/v1/pages/{id}/submit` | assigned user | Submit for review |
| `POST` | `/api/v1/pages/{id}/review` | reviewer/admin | Approve/reject |
| `GET` | `/api/v1/users/me/tasks` | authenticated | My assigned tasks |
| `GET` | `/api/v1/projects/{id}/review-queue` | member | Review queue |
