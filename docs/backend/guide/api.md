# API 엔드포인트

모든 엔드포인트는 `/api/v1` 접두사를 사용합니다.

**인증**: Health와 Auth 엔드포인트를 제외한 모든 엔드포인트는
`Authorization: Bearer <access_token>` 헤더가 필요합니다.
Admin 엔드포인트는 추가로 `admin` 역할이 필요합니다.

## Health

### `GET /api/v1/health`

서버 상태 확인.

**응답:** `200 OK`

```json
{
  "status": "healthy",
  "message": "Service is running",
  "version": "0.1.0"
}
```

### `GET /api/v1/health/ready`

서비스 준비 상태 확인 (DB 연결 포함).

**응답:** `200 OK`

```json
{
  "status": "ready",
  "message": "All systems operational",
  "version": "0.1.0"
}
```

---

## Auth

인증 관련 엔드포인트. 모두 인증 불필요 (credentials update 제외).

### `GET /api/v1/auth/check-login-id`

로그인 ID 사용 가능 여부 확인.

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
| -------- | ---- | ---- |
| `login_id` | string | 확인할 로그인 ID |

**응답:** `200 OK`

```json
{ "available": true }
```

### `POST /api/v1/auth/register`

회원가입. 최초 유저는 자동으로 `admin` 역할이 부여됩니다.

**요청 Body:**

```json
{
  "name": "김철수",
  "login_id": "chulsoo",
  "email": "chulsoo@example.com",
  "password": "securepassword123"
}
```

**응답:** `201 Created`

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

Set-Cookie: `refresh_token` (HttpOnly, Secure, SameSite=Lax)

### `POST /api/v1/auth/login`

로그인.

**요청 Body:**

```json
{
  "login_id": "chulsoo",
  "password": "securepassword123"
}
```

**응답:** `200 OK`

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

Set-Cookie: `refresh_token` (HttpOnly, Secure, SameSite=Lax)

**오류:**

| 코드 | 설명 |
| ---- | ---- |
| `401` | 잘못된 로그인 ID 또는 비밀번호 |
| `403` | 비활성화된 계정 |

### `POST /api/v1/auth/refresh`

Refresh token으로 새 access token 발급. Token rotation 적용.

**요청:** Cookie에 포함된 `refresh_token` 사용

**응답:** `200 OK`

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

Set-Cookie: 새로운 `refresh_token`

**오류:**

| 코드 | 설명 |
| ---- | ---- |
| `401` | 유효하지 않거나 만료된 refresh token |

### `POST /api/v1/auth/logout`

현재 refresh token family 폐기.

**요청:** Cookie에 포함된 `refresh_token` 사용

**응답:** `204 No Content`

### `PATCH /api/v1/auth/me/credentials`

로그인 ID, 이메일, 비밀번호 변경. **인증 필요.**

**요청 Body:**

```json
{
  "login_id": "new_login_id",
  "email": "new@example.com",
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

모든 필드는 선택적. `new_password` 제공 시 `current_password` 필수.
변경 시 모든 세션이 무효화됩니다 (refresh token hard delete).

**응답:** `200 OK`

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

Set-Cookie: 새로운 `refresh_token` (기존 세션 전체 무효화)

---

## Admin

관리자 전용 엔드포인트. `admin` 역할 필요.

### `GET /api/v1/admin/users`

전체 유저 목록 조회.

**응답:** `200 OK`

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

유저 역할 변경 또는 비활성화.

**요청 Body:**

```json
{
  "role": "reviewer",
  "is_active": false
}
```

모든 필드는 선택적.

**응답:** `200 OK`

### `GET /api/v1/admin/projects`

전체 프로젝트 목록 (통계 포함).

**응답:** `200 OK`

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

시스템 전체 통계.

**응답:** `200 OK`

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

### `DELETE /api/v1/projects/{project_id}`

프로젝트 삭제. 관련 문서, 페이지, 이미지도 함께 삭제됩니다.

**응답:** `204 No Content` | `404 Not Found`

### `GET /api/v1/projects/{project_id}/ocr-config`

프로젝트의 OCR 엔진 설정 조회. 등록된 엔진이 없으면 빈 engines dict 반환.

**응답:** `200 OK`

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

새 엔진 인스턴스 등록. 같은 엔진 타입을 여러 개 등록할 수 있습니다.

**요청 Body:**

vLLM 엔진 예시:

```json
{
  "engine_type": "vllm",
  "name": "vLLM olmOCR",
  "config": { "host": "gpu-server-2", "port": 8000, "model": "allenai/olmOCR-2-7B-1025-FP8" }
}
```

Split Pipeline 엔진 예시 (PP-DocLayoutV3 + vLLM):

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

!!! note "`layout_provider` 옵션"
    `split_pipeline` 엔진의 `layout_provider`는 `"docling"` (기본값) 또는
    `"pp_doclayout"` (PP-DocLayoutV3)을 지원합니다.

**응답:** `201 Created` (updated OcrConfigResponse) | `409 Conflict` (engine_id 충돌)

### `PUT /api/v1/projects/{project_id}/ocr-config/engines/{engine_id}`

기존 엔진 인스턴스의 이름이나 설정을 수정합니다.

**요청 Body:**

```json
{
  "name": "vLLM Chandra (updated)",
  "config": { "host": "new-server", "port": 8000, "model": "datalab-to/chandra" }
}
```

**응답:** `200 OK` | `404 Not Found`

### `DELETE /api/v1/projects/{project_id}/ocr-config/engines/{engine_id}`

엔진 인스턴스 삭제. 삭제된 엔진이 기본 엔진이면 `default_engine_id`가 null로 초기화됩니다.

**응답:** `200 OK` (updated OcrConfigResponse) | `404 Not Found`

### `PUT /api/v1/projects/{project_id}/ocr-config/default-engine`

전체 페이지 OCR에 사용할 기본 엔진 설정. null이면 pdfminer 폴백.

**요청 Body:**

```json
{ "engine_id": "gemini-flash" }
```

**응답:** `200 OK` | `404 Not Found`

### `POST /api/v1/projects/{project_id}/ocr-config/test`

특정 엔진 인스턴스의 연결 테스트.

**요청 Body:**

```json
{ "engine_id": "vllm-chandra" }
```

**응답:** `200 OK`

```json
{
  "success": true,
  "message": "Connected to vLLM (datalab-to/chandra)"
}
```

### `GET /api/v1/projects/{project_id}/available-engines`

요소별 텍스트 추출에 사용할 수 있는 엔진 목록 조회.
등록된 모든 엔진을 반환합니다 (pdfminer는 region-level 추출 미지원으로 제외).

**응답:** `200 OK`

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

프로젝트의 문서 목록 조회.

**응답:** `200 OK`

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

PDF 문서 업로드. 업로드된 PDF는 자동으로 페이지별 이미지로 변환되고,
pdfminer.six로 텍스트/이미지 블록을 추출하여 `auto_extracted_data`에 저장합니다.

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

### `DELETE /api/v1/documents/{document_id}`

문서 삭제. 관련 페이지와 이미지도 함께 삭제됩니다.

**응답:** `204 No Content` | `404 Not Found`

### `GET /api/v1/documents/{document_id}/status`

문서 처리 상태와 진행률 조회.

**응답:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "extracting",
  "total_pages": 12,
  "processed_pages": 5
}
```

### `POST /api/v1/documents/{document_id}/re-extract`

현재 프로젝트의 OCR 엔진으로 문서의 모든 페이지를 재추출합니다.
기존 `annotation_data`는 유지되고, `auto_extracted_data`만 갱신됩니다.
pdfminer 엔진은 동기 처리되며, 그 외 엔진은 비동기 백그라운드 태스크로 실행됩니다.

**응답:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "extracting",
  "total_pages": 12,
  "processed_pages": 0
}
```

!!! note "상태 변화"
    pdfminer 엔진의 경우 동기 처리 후 `status: "ready"`로 반환됩니다.
    그 외 엔진은 `status: "extracting"`으로 반환되며, 추출 완료 후 `ready`로 변경됩니다.
    진행률은 `GET /documents/{id}/status`로 폴링할 수 있습니다.

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 문서를 찾을 수 없음 |
| `409` | 이미 추출 진행 중 |

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

### `POST /api/v1/pages/{page_id}/force-accept-extraction`

자동 추출 결과(`auto_extracted_data`)를 `annotation_data`로 강제 복사합니다.
기존 `accept-extraction`과 달리, `annotation_data`에 이미 요소가 존재해도 덮어씁니다.
재추출 후 새로운 OCR 결과로 기존 주석을 대체할 때 사용합니다.

**응답:** `200 OK` - 업데이트된 페이지 데이터

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `409` | `auto_extracted_data`가 없음 |

### `POST /api/v1/pages/{page_id}/extract-text`

지정 영역의 텍스트를 OCR 엔진으로 추출합니다.
`engine_id`를 지정하면 해당 엔진 인스턴스로 추출하고, 생략하면 프로젝트 기본 엔진을 사용합니다.

**요청 Body:**

```json
{
  "poly": [100, 200, 500, 200, 500, 400, 100, 400],
  "category_type": "text_block",
  "engine_id": "vllm-chandra"
}
```

| 필드 | 타입 | 필수 | 설명 |
| ------ | ------ | ------ | ------ |
| `poly` | `list[float]` | O | 8개 좌표 (4 꼭짓점) |
| `category_type` | string | X | 카테고리 타입 (기본값: `text_block`) |
| `engine_id` | string | X | 엔진 인스턴스 ID 오버라이드 (생략 시 프로젝트 기본 엔진) |

**응답:** `200 OK`

```json
{
  "text": "추출된 텍스트 내용"
}
```

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 페이지를 찾을 수 없음 |
| `502` | OCR 프로바이더 오류 |
| `503` | OCR 프로바이더 미설정 |

### `PUT /api/v1/pages/{page_id}/reading-order`

읽기 순서 업데이트. `anno_id` → `order` 매핑으로 요소 순서를 변경합니다.

**요청 Body:**

```json
{
  "order_map": {
    "0": 2,
    "1": 0,
    "2": 1
  }
}
```

| 필드 | 타입 | 설명 |
| ------ | ------ | ------ |
| `order_map` | `dict[string, int]` | anno_id(문자열) → order(정수) 매핑. 중복 order 값 및 음수 값 불허 |

**응답:** `200 OK` - 업데이트된 페이지 데이터

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 페이지를 찾을 수 없거나, order_map에 존재하지 않는 anno_id 포함 |
| `422` | 중복된 order 값 또는 음수 값 |

### `POST /api/v1/pages/{page_id}/relations`

요소 간 관계 추가. JSONB `extra.relation[]`에 저장됩니다.

**요청 Body:**

```json
{
  "source_anno_id": 3,
  "target_anno_id": 4,
  "relation_type": "figure_caption"
}
```

| 필드 | 타입 | 필수 | 설명 |
| ------ | ------ | ------ | ------ |
| `source_anno_id` | int (≥0) | O | 출발 요소 anno_id |
| `target_anno_id` | int (≥0) | O | 도착 요소 anno_id |
| `relation_type` | string | X | 관계 유형 (기본값: `parent_son`) |

**관계 유형:**

| 값 | 설명 |
| ------ | ------ |
| `parent_son` | 부모-자식 관계 |
| `figure_caption` | 그림-캡션 |
| `table_caption` | 표-캡션 |
| `table_footnote` | 표-각주 |
| `equation_caption` | 수식-캡션 |
| `code_caption` | 코드-캡션 |

**응답:** `201 Created` - 업데이트된 페이지 데이터

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 페이지를 찾을 수 없음 |
| `409` | 자기 참조, 중복 관계, 존재하지 않는 요소 |

### `DELETE /api/v1/pages/{page_id}/relations`

요소 간 관계 삭제.

**요청 Body:**

```json
{
  "source_anno_id": 3,
  "target_anno_id": 4
}
```

**응답:** `200 OK` - 업데이트된 페이지 데이터

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 페이지를 찾을 수 없음 |

---

## Users

> **참고**: 사용자 등록은 `POST /api/v1/auth/register`를 사용하세요. 아래 엔드포인트는 레거시이며, 향후 제거될 수 있습니다.

### `POST /api/v1/users`

사용자 생성 (레거시).

**응답:** `201 Created`

### `GET /api/v1/users`

사용자 목록 조회.

**응답:** `200 OK`

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

### `GET /api/v1/projects/{project_id}/export/zip`

프로젝트의 모든 페이지를 OmniDocBench 호환 ZIP 아카이브로 내보내기.

ZIP 구조:

```text
{project_name}_{datetime}.zip
├── annos.json
└── images/
    └── {document_name}/
        ├── page_001.png
        ├── page_002.png
        └── ...
```

**응답:** `200 OK` (application/zip)

- `Content-Disposition: attachment; filename="{project_name}_{YYYYMMdd_HHmmss}.zip"`

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 프로젝트를 찾을 수 없음 |

### `GET /api/v1/projects/{project_id}/documents/{document_id}/export/zip`

단일 문서를 OmniDocBench 호환 ZIP 아카이브로 내보내기.

**응답:** `200 OK` (application/zip)

- `Content-Disposition: attachment; filename="{document_name}_{YYYYMMdd_HHmmss}.zip"`

**오류:**

| 코드 | 설명 |
| ------ | ------ |
| `404` | 문서를 찾을 수 없거나 프로젝트에 속하지 않음 |

---

## 프로젝트 진행 현황 API

### `GET /api/v1/projects/{project_id}/progress`

프로젝트의 전체 진행 현황 조회. 상태별 페이지 수, 문서별 진행률, 멤버별 활동을 포함합니다.

**인증**: 프로젝트 멤버 (member / admin)

**응답:** `200 OK`

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

**오류:**

| 코드 | 설명 |
| ---- | ---- |
| `401` | 인증되지 않음 |
| `403` | 프로젝트 멤버가 아님 |

---

## 프로젝트 멤버 관리 API

| Method | Path | 인증 | 설명 |
| ------ | ---- | ---- | ---- |
| `GET` | `/api/v1/projects/{id}/members` | member | 멤버 목록 |
| `POST` | `/api/v1/projects/{id}/members` | owner/admin | 멤버 초대 |
| `PATCH` | `/api/v1/projects/{id}/members/{user_id}` | owner/admin | 멤버 역할 변경 |
| `DELETE` | `/api/v1/projects/{id}/members/{user_id}` | owner/admin | 멤버 제거 |

## 태스크 워크플로우 API

| Method | Path | 인증 | 설명 |
| ------ | ---- | ---- | ---- |
| `POST` | `/api/v1/pages/{id}/assign` | owner/admin | 페이지 할당 |
| `POST` | `/api/v1/pages/{id}/submit` | assigned user | 검수 제출 |
| `POST` | `/api/v1/pages/{id}/review` | reviewer/admin | 승인/반려 |
| `GET` | `/api/v1/users/me/tasks` | 인증 필요 | 내 할당 작업 목록 |
| `GET` | `/api/v1/projects/{id}/review-queue` | member | 검수 대기 큐 |
