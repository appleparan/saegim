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
| `api.delete<T>` | `(path: string, body?: unknown) => Promise<T>` | DELETE 요청 (body 지원) |
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
| `getOcrConfig(projectId)` | GET | `/api/v1/projects/:id/ocr-config` | OCR 엔진 설정 조회 (다중 인스턴스) |
| `addEngine(projectId, data)` | POST | `/api/v1/projects/:id/ocr-config/engines` | 엔진 인스턴스 등록 |
| `updateEngine(projectId, engineId, data)` | PUT | `/api/v1/projects/:id/ocr-config/engines/:eid` | 엔진 인스턴스 수정 |
| `deleteEngine(projectId, engineId)` | DELETE | `/api/v1/projects/:id/ocr-config/engines/:eid` | 엔진 인스턴스 삭제 |
| `setDefaultEngine(projectId, data)` | PUT | `/api/v1/projects/:id/ocr-config/default-engine` | 기본 엔진 설정 |
| `testEngineConnection(projectId, data)` | POST | `/api/v1/projects/:id/ocr-config/test` | 엔진 연결 테스트 (engine_id 지정) |
| `getAvailableEngines(projectId)` | GET | `/api/v1/projects/:id/available-engines` | 요소별 OCR 사용 가능 엔진 목록 |
| `getProjectProgress(projectId)` | GET | `/api/v1/projects/:id/progress` | 프로젝트 진행 현황 |
| `listProjectMembers(projectId)` | GET | `/api/v1/projects/:id/members` | 멤버 목록 |
| `addProjectMember(projectId, data)` | POST | `/api/v1/projects/:id/members` | 멤버 초대 |
| `updateProjectMemberRole(projectId, userId, data)` | PATCH | `/api/v1/projects/:id/members/:uid` | 멤버 역할 변경 |
| `removeProjectMember(projectId, userId)` | DELETE | `/api/v1/projects/:id/members/:uid` | 멤버 제거 |
| `exportProjectZip(projectId)` | GET | `/api/v1/projects/:id/export/zip` | 프로젝트 ZIP 내보내기 (blob 다운로드) |

### Documents (`src/lib/api/documents.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `listDocuments(projectId)` | GET | `/api/v1/projects/:id/documents` | 문서 목록 |
| `uploadDocument(projectId, file)` | POST | `/api/v1/projects/:id/documents` | PDF 업로드 (FormData) |
| `getDocumentStatus(docId)` | GET | `/api/v1/documents/:id/status` | 처리 상태 조회 |
| `reExtractDocument(docId)` | POST | `/api/v1/documents/:id/re-extract` | 현재 OCR 엔진으로 전체 재추출 |
| `deleteDocument(docId)` | DELETE | `/api/v1/documents/:id` | 문서 삭제 |
| `listPages(docId)` | GET | `/api/v1/documents/:id/pages` | 페이지 목록 |
| `exportDocumentZip(projectId, docId)` | GET | `/api/v1/projects/:pid/documents/:did/export/zip` | 문서 ZIP 내보내기 (blob 다운로드) |

### Pages (`src/lib/api/pages.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `getPage(pageId)` | GET | `/api/v1/pages/:id` | 페이지 데이터 + 어노테이션 |
| `savePage(pageId, data)` | PUT | `/api/v1/pages/:id` | 어노테이션 전체 저장 |
| `savePageAttributes(pageId, data)` | PUT | `/api/v1/pages/:id/attributes` | 페이지 속성 저장 |
| `acceptExtraction(pageId)` | POST | `/api/v1/pages/:id/accept-extraction` | 자동 추출 수락 |
| `forceAcceptExtraction(pageId)` | POST | `/api/v1/pages/:id/force-accept-extraction` | 자동 추출 강제 수락 (기존 주석 덮어쓰기) |
| `extractElementText(pageId, poly)` | POST | `/api/v1/pages/:id/extract-text` | 영역 OCR 요청 |
| `updateReadingOrder(pageId, orderMap)` | PUT | `/api/v1/pages/:id/reading-order` | 읽기 순서 업데이트 |

### Elements (`src/lib/api/elements.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `createElement(pageId, data)` | POST | `/api/v1/pages/:id/elements` | 요소 생성 |
| ~~`updateElement(elementId, data)`~~ | PUT | `/api/v1/elements/:id` | 데드 코드 (백엔드 경로 없음, 전체 저장으로 대체) |
| ~~`deleteElement(elementId)`~~ | DELETE | `/api/v1/elements/:id` | 데드 코드 (백엔드: `DELETE /pages/:pid/elements/:anno_id`) |

> **참고**: 요소 삭제는 백엔드에서 `DELETE /api/v1/pages/{page_id}/elements/{anno_id}`로
> 구현되어 있으나, 프론트엔드는 `savePage()`로 전체 저장하는 방식을 사용합니다.

### Relations (`src/lib/api/relations.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `createRelation(pageId, data)` | POST | `/api/v1/pages/:id/relations` | 관계 생성 |
| `deleteRelation(pageId, sourceAnnoId, targetAnnoId)` | DELETE | `/api/v1/pages/:id/relations` | 관계 삭제 (body에 source/target 포함) |

### Auth (`src/lib/api/auth.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `checkLoginId(loginId)` | GET | `/api/v1/auth/check-login-id` | 로그인 ID 중복 확인 |
| `register(data)` | POST | `/api/v1/auth/register` | 회원가입 |
| `login(data)` | POST | `/api/v1/auth/login` | 로그인 |
| `refreshToken()` | POST | `/api/v1/auth/refresh` | 토큰 갱신 |
| `logout()` | POST | `/api/v1/auth/logout` | 로그아웃 |
| `updateCredentials(data)` | PATCH | `/api/v1/auth/me/credentials` | 자격 증명 변경 |

### Admin (`src/lib/api/admin.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `listUsers()` | GET | `/api/v1/admin/users` | 전체 유저 목록 |
| `updateUser(userId, data)` | PATCH | `/api/v1/admin/users/:id` | 유저 역할/활성 상태 변경 |
| `listAdminProjects()` | GET | `/api/v1/admin/projects` | 전체 프로젝트 (통계 포함) |
| `getAdminStats()` | GET | `/api/v1/admin/stats` | 시스템 전체 통계 |

### Tasks (`src/lib/api/tasks.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `getMyTasks()` | GET | `/api/v1/users/me/tasks` | 내 할당 작업 목록 |
| `getReviewQueue(projectId)` | GET | `/api/v1/projects/:id/review-queue` | 검수 대기 큐 |

### Users (`src/lib/api/users.ts`)

| 함수 | HTTP | 경로 | 설명 |
| ------ | ------ | ------ | ------ |
| `listUsers()` | GET | `/api/v1/users` | 사용자 목록 (레거시) |

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
