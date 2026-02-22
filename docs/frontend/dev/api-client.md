# API Client

## 설정

백엔드 URL은 환경 변수로 설정한다:

```bash
# .env
VITE_API_URL=http://localhost:5000
```

설정하지 않으면 기본값 `http://localhost:8000`을 사용한다.

## 클라이언트 (`src/lib/api/client.ts`)

### `api` 객체

| 메서드 | 시그니처 | 설명 |
| -------- | ---------- | ------ |
| `api.get<T>` | `(path: string) => Promise<T>` | GET 요청, JSON 응답 파싱 |
| `api.post<T>` | `(path: string, body?: unknown) => Promise<T>` | POST 요청, JSON body |
| `api.put<T>` | `(path: string, body?: unknown) => Promise<T>` | PUT 요청, JSON body |
| `api.delete<T>` | `(path: string) => Promise<T>` | DELETE 요청 |
| `api.upload` | `(path: string, formData: FormData) => Promise<Response>` | FormData 업로드 (PDF 등) |

### 에러 클래스

- **`ApiError`**: HTTP 응답 에러 (status >= 400). `status`, `statusText`, `body` 포함.
- **`NetworkError`**: 네트워크 연결 실패 (fetch 예외). 백엔드 미실행 시 발생.

```typescript
try {
  const project = await getProject(id)
} catch (e) {
  if (e instanceof NetworkError) {
    // 백엔드 연결 불가
  } else if (e instanceof ApiError) {
    // HTTP 에러 (404, 500 등)
  }
}
```

## API 엔드포인트

### Projects (`src/lib/api/projects.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `listProjects()` | GET | `/api/v1/projects` | 프로젝트 목록 |
| `getProject(id)` | GET | `/api/v1/projects/:id` | 프로젝트 상세 |
| `createProject(data)` | POST | `/api/v1/projects` | 프로젝트 생성 |
| `deleteProject(id)` | DELETE | `/api/v1/projects/:id` | 프로젝트 삭제 |
| `getOcrConfig(projectId)` | GET | `/api/v1/projects/:id/ocr-config` | OCR 엔진 설정 조회 (engine_type) |
| `updateOcrConfig(projectId, data)` | PUT | `/api/v1/projects/:id/ocr-config` | OCR 엔진 설정 수정 (engine_type) |
| `testOcrConnection(projectId, data)` | POST | `/api/v1/projects/:id/ocr-config/test` | OCR 엔진 연결 테스트 |

### Documents (`src/lib/api/documents.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `listDocuments(projectId)` | GET | `/api/v1/projects/:id/documents` | 문서 목록 |
| `uploadDocument(projectId, file)` | POST | `/api/v1/projects/:id/documents` | PDF 업로드 (FormData) |
| `getDocumentStatus(docId)` | GET | `/api/v1/documents/:id/status` | 처리 상태 조회 |
| `deleteDocument(docId)` | DELETE | `/api/v1/documents/:id` | 문서 삭제 |
| `listPages(docId)` | GET | `/api/v1/documents/:id/pages` | 페이지 목록 |

### Pages (`src/lib/api/pages.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `getPage(pageId)` | GET | `/api/v1/pages/:id` | 페이지 데이터 + 어노테이션 |
| `savePage(pageId, data)` | PUT | `/api/v1/pages/:id` | 어노테이션 전체 저장 |
| `savePageAttributes(pageId, data)` | PUT | `/api/v1/pages/:id/attributes` | 페이지 속성 저장 |
| `acceptExtraction(pageId)` | POST | `/api/v1/pages/:id/accept-extraction` | 자동 추출 수락 |
| `extractElementText(pageId, poly)` | POST | `/api/v1/pages/:id/extract-text` | 영역 OCR 요청 (현재 백엔드 미구현 가능) |

### Elements (`src/lib/api/elements.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `createElement(pageId, data)` | POST | `/api/v1/pages/:id/elements` | 요소 생성 |
| `updateElement(elementId, data)` | PUT | `/api/v1/elements/:id` | 요소 수정 (현재 백엔드 미구현) |
| `deleteElement(elementId)` | DELETE | `/api/v1/elements/:id` | 요소 삭제 (현재 백엔드 미구현) |

### Relations (`src/lib/api/relations.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `createRelation(pageId, data)` | POST | `/api/v1/pages/:id/relations` | 관계 생성 (현재 백엔드 미구현) |
| `deleteRelation(relationId)` | DELETE | `/api/v1/relations/:id` | 관계 삭제 (현재 백엔드 미구현) |

## 주요 타입 (`src/lib/api/types.ts`)

### Response 타입

```typescript
interface PageResponse {
  id: string
  document_id: string
  page_no: number
  width: number
  height: number
  image_url: string
  pdf_url: string                   // PDF.js 벡터 렌더링용 URL
  annotation_data: AnnotationData   // OmniDocBench JSON
  auto_extracted_data: AnnotationData | null
  status: 'pending' | 'in_progress' | 'submitted' | 'reviewed'
  project_id?: string               // 브레드크럼용
  project_name?: string
  document_filename?: string
}
```

### Request 타입

```typescript
interface SavePageRequest {
  annotation_data: AnnotationData
}

interface CreateElementRequest {
  category_type: string
  poly: readonly number[]
  text?: string
}

interface UpdateElementRequest {
  category_type?: string
  poly?: readonly number[]
  text?: string
  latex?: string
  html?: string
  attribute?: Record<string, string | boolean>
  ignore?: boolean
  order?: number
}
```

## 현재 저장 전략

현재 MVP는 "전체 저장" 방식을 사용한다:

1. `annotationStore`에서 `annotationData` 전체를 관리
2. 저장 시 `savePage()`로 `annotation_data` 전체를 PUT
3. 개별 element/relation API는 향후 실시간 저장에 사용 예정
