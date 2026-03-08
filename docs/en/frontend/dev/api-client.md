# API Client

## Configuration

The backend URL is configured via an environment variable:

```bash
# .env
VITE_API_URL=http://localhost:5000
```

If not set, the default value `http://localhost:8000` is used.

## Client (`src/lib/api/client.ts`)

### `api` Object

| Method | Signature | Description |
| -------- | ---------- | ------ |
| `api.get<T>` | `(path: string) => Promise<T>` | GET request, parses JSON response |
| `api.post<T>` | `(path: string, body?: unknown) => Promise<T>` | POST request, JSON body |
| `api.put<T>` | `(path: string, body?: unknown) => Promise<T>` | PUT request, JSON body |
| `api.delete<T>` | `(path: string, body?: unknown) => Promise<T>` | DELETE request (body supported) |
| `api.upload` | `(path: string, formData: FormData) => Promise<Response>` | FormData upload (PDF, etc.) |

### Error Classes

- **`ApiError`**: HTTP response error (status >= 400). Includes `status`, `statusText`, `body`.
- **`NetworkError`**: Network connection failure (fetch exception). Occurs when the backend is not running.

```typescript
try {
  const project = await getProject(id)
} catch (e) {
  if (e instanceof NetworkError) {
    // Cannot connect to backend
  } else if (e instanceof ApiError) {
    // HTTP error (404, 500, etc.)
  }
}
```

## API Endpoints

### Projects (`src/lib/api/projects.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `listProjects()` | GET | `/api/v1/projects` | List projects |
| `getProject(id)` | GET | `/api/v1/projects/:id` | Get project details |
| `createProject(data)` | POST | `/api/v1/projects` | Create project |
| `deleteProject(id)` | DELETE | `/api/v1/projects/:id` | Delete project |
| `getOcrConfig(projectId)` | GET | `/api/v1/projects/:id/ocr-config` | Get OCR engine configuration (multiple instances) |
| `addEngine(projectId, data)` | POST | `/api/v1/projects/:id/ocr-config/engines` | Register engine instance |
| `updateEngine(projectId, engineId, data)` | PUT | `/api/v1/projects/:id/ocr-config/engines/:eid` | Update engine instance |
| `deleteEngine(projectId, engineId)` | DELETE | `/api/v1/projects/:id/ocr-config/engines/:eid` | Delete engine instance |
| `setDefaultEngine(projectId, data)` | PUT | `/api/v1/projects/:id/ocr-config/default-engine` | Set default engine |
| `testEngineConnection(projectId, data)` | POST | `/api/v1/projects/:id/ocr-config/test` | Test engine connection (specify engine_id) |
| `getAvailableEngines(projectId)` | GET | `/api/v1/projects/:id/available-engines` | List available OCR engines per element |
| `getProjectProgress(projectId)` | GET | `/api/v1/projects/:id/progress` | Get project progress |
| `listProjectMembers(projectId)` | GET | `/api/v1/projects/:id/members` | List members |
| `addProjectMember(projectId, data)` | POST | `/api/v1/projects/:id/members` | Invite member |
| `updateProjectMemberRole(projectId, userId, data)` | PATCH | `/api/v1/projects/:id/members/:uid` | Change member role |
| `removeProjectMember(projectId, userId)` | DELETE | `/api/v1/projects/:id/members/:uid` | Remove member |
| `exportProjectZip(projectId)` | GET | `/api/v1/projects/:id/export/zip` | Export project as ZIP (blob download) |

### Documents (`src/lib/api/documents.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `listDocuments(projectId)` | GET | `/api/v1/projects/:id/documents` | List documents |
| `uploadDocument(projectId, file)` | POST | `/api/v1/projects/:id/documents` | Upload PDF (FormData) |
| `getDocumentStatus(docId)` | GET | `/api/v1/documents/:id/status` | Get processing status |
| `reExtractDocument(docId)` | POST | `/api/v1/documents/:id/re-extract` | Re-extract entire document with current OCR engine |
| `deleteDocument(docId)` | DELETE | `/api/v1/documents/:id` | Delete document |
| `listPages(docId)` | GET | `/api/v1/documents/:id/pages` | List pages |
| `exportDocumentZip(projectId, docId)` | GET | `/api/v1/projects/:pid/documents/:did/export/zip` | Export document as ZIP (blob download) |

### Pages (`src/lib/api/pages.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `getPage(pageId)` | GET | `/api/v1/pages/:id` | Get page data + annotations |
| `savePage(pageId, data)` | PUT | `/api/v1/pages/:id` | Save full annotations |
| `savePageAttributes(pageId, data)` | PUT | `/api/v1/pages/:id/attributes` | Save page attributes |
| `acceptExtraction(pageId)` | POST | `/api/v1/pages/:id/accept-extraction` | Accept auto-extraction |
| `forceAcceptExtraction(pageId)` | POST | `/api/v1/pages/:id/force-accept-extraction` | Force accept auto-extraction (overwrite existing annotations) |
| `extractElementText(pageId, poly)` | POST | `/api/v1/pages/:id/extract-text` | Request OCR for a region |
| `updateReadingOrder(pageId, orderMap)` | PUT | `/api/v1/pages/:id/reading-order` | Update reading order |

### Elements (`src/lib/api/elements.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `createElement(pageId, data)` | POST | `/api/v1/pages/:id/elements` | Create element |

> **Note**: Element modification/deletion uses the full save approach via `savePage()`.

### Relations (`src/lib/api/relations.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `createRelation(pageId, data)` | POST | `/api/v1/pages/:id/relations` | Create relation |
| `deleteRelation(pageId, sourceAnnoId, targetAnnoId)` | DELETE | `/api/v1/pages/:id/relations` | Delete relation (source/target included in body) |

### Auth (`src/lib/api/auth.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `checkLoginId(loginId)` | GET | `/api/v1/auth/check-login-id` | Check login ID availability |
| `register(data)` | POST | `/api/v1/auth/register` | Sign up |
| `login(data)` | POST | `/api/v1/auth/login` | Sign in |
| `refreshToken()` | POST | `/api/v1/auth/refresh` | Refresh token |
| `logout()` | POST | `/api/v1/auth/logout` | Sign out |
| `updateCredentials(data)` | PATCH | `/api/v1/auth/me/credentials` | Update credentials |

### Admin (`src/lib/api/admin.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `listUsers()` | GET | `/api/v1/admin/users` | List all users |
| `updateUser(userId, data)` | PATCH | `/api/v1/admin/users/:id` | Update user role/active status |
| `listAdminProjects()` | GET | `/api/v1/admin/projects` | List all projects (with stats) |
| `getAdminStats()` | GET | `/api/v1/admin/stats` | Get system-wide statistics |

### Tasks (`src/lib/api/tasks.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `getMyTasks()` | GET | `/api/v1/users/me/tasks` | List my assigned tasks |
| `getReviewQueue(projectId)` | GET | `/api/v1/projects/:id/review-queue` | Get review queue |

### Users (`src/lib/api/users.ts`)

| Function | HTTP | Path | Description |
| ------ | ------ | ------ | ------ |
| `listUsers()` | GET | `/api/v1/users` | List users (authentication required) |

## Key Types (`src/lib/api/types.ts`)

### Response Types

```typescript
interface PageResponse {
  id: string
  document_id: string
  page_no: number
  width: number
  height: number
  image_url: string
  pdf_url: string                   // URL for PDF.js vector rendering
  annotation_data: AnnotationData   // OmniDocBench JSON
  auto_extracted_data: AnnotationData | null
  status: 'pending' | 'in_progress' | 'submitted' | 'reviewed'
  project_id?: string               // For breadcrumbs
  project_name?: string
  document_filename?: string
}
```

### Request Types

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

## Current Save Strategy

The current MVP uses a "full save" approach:

1. `annotationStore` manages the entire `annotationData`
2. On save, `savePage()` PUTs the entire `annotation_data`
3. Individual element/relation APIs are planned for future real-time saving
