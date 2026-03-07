# Saegim Frontend Architecture

## Overview

Saegim 프론트엔드는 한국어 문서 VLM 벤치마크를 위한 레이블링 웹앱이다. OmniDocBench JSON 형식의 어노테이션 데이터를 Canvas 위에서 편집하고 FastAPI 백엔드에 저장한다.

## Tech Stack

| 영역 | 기술 | 버전 |
| ------ | ------ | ------ |
| UI Framework | Svelte 5 (runes) | ^5.43 |
| Build Tool | SvelteKit (Vite-based) + adapter-static | ^2.21 |
| Styling | Tailwind CSS 4 + shadcn-svelte (bits-ui) | ^4.1 |
| Theme | Violet 테마 (OKLCH CSS 변수) + 다크모드 (mode-watcher) | - |
| Canvas | Konva.js | ^10.2 |
| PDF Rendering | pdfjs-dist (PDF.js) | ^5.4 |
| Router | SvelteKit file-based routing | - |
| Test | Vitest + jsdom | ^4.0 |
| Package Manager | Bun | - |

## Directory Structure

```text
src/
├── app.html                # SvelteKit HTML 템플릿
├── app.css                 # Tailwind + shadcn 테마 CSS 변수 (violet OKLCH) + 카테고리 색상
├── routes/                 # SvelteKit 파일 기반 라우트
│   ├── +layout.svelte          # 전역 레이아웃 + Auth Guard + ModeWatcher
│   ├── +layout.ts              # ssr=false, prerender=false
│   ├── +page.svelte            # / (프로젝트 목록)
│   ├── login/+page.svelte      # /login (로그인)
│   ├── register/+page.svelte   # /register (회원가입)
│   ├── admin/+page.svelte      # /admin (관리자 대시보드, admin 전용)
│   ├── account/
│   │   └── security/+page.svelte  # /account/security (비밀번호 변경)
│   ├── projects/[id]/
│   │   ├── +page.svelte        # /projects/:id (문서 목록)
│   │   └── settings/+page.svelte  # /projects/:id/settings (OCR 설정)
│   └── label/[pageId]/
│       └── +page.svelte        # /label/:pageId (레이블링)
├── lib/
│   ├── types/              # 타입 정의
│   │   ├── omnidocbench.ts     # AnnotationData, LayoutElement, Poly 등
│   │   ├── categories.ts      # 18개 블록 카테고리, 속성 enum, 한국어 라벨
│   │   ├── canvas.ts          # Point, Rect, ToolMode, ViewportState
│   │   └── element-groups.ts  # IMAGE/TEXT_BLOCK_CATEGORIES, 블록 분류 헬퍼
│   ├── utils/              # 순수 함수
│   │   ├── bbox.ts             # 좌표 변환 (poly <-> rect, screen <-> image)
│   │   ├── color.ts            # 카테고리별 색상
│   │   ├── interaction.ts     # 인터랙션 모드 해석, 포인터 이벤트 계산
│   │   ├── jwt.ts             # JWT 디코딩 (클라이언트), 만료 체크
│   │   ├── text-layout.ts     # 텍스트 블록 레이아웃 계산
│   │   ├── text-selection.ts  # 텍스트 선택/복사 유틸
│   │   └── validation.ts      # 어노테이션 유효성 검증
│   ├── api/                # HTTP 클라이언트
│   │   ├── client.ts           # fetch 래퍼 + Bearer 자동 주입 + 401 silent refresh
│   │   ├── types.ts            # API request/response 타입
│   │   ├── auth.ts             # 로그인/회원가입/토큰갱신/로그아웃 API
│   │   ├── admin.ts            # 관리자 API (유저/프로젝트/통계)
│   │   ├── projects.ts
│   │   ├── documents.ts
│   │   ├── pages.ts
│   │   ├── elements.ts
│   │   └── relations.ts
│   ├── stores/             # Svelte 5 runes 상태 관리
│   │   ├── auth.svelte.ts        # 인증 상태 (token, user, role, mustChangePassword)
│   │   ├── annotation.svelte.ts  # 어노테이션 데이터 + CRUD
│   │   ├── canvas.svelte.ts      # 뷰포트 (zoom/pan/tool)
│   │   ├── pdf.svelte.ts         # PDF.js 문서 로딩/캐싱
│   │   └── ui.svelte.ts          # 사이드바, 알림, 패널탭 (관계 포함)
│   └── components/
│       ├── ui/            # shadcn-svelte (button, badge, card, dialog, ...)
│       ├── common/         # 재사용 UI 위젯 (LoadingSpinner, Select)
│       ├── layout/         # Header, Sidebar (4탭: 요소/속성/텍스트/관계), ThemeToggle
│       ├── canvas/         # 3-layer 뷰어 + 오버레이 (HybridViewer, BboxLayer, ReadingOrderOverlay, RelationOverlay 등)
│       ├── panels/         # 사이드바 패널 (ElementList, AttributePanel, ExtractionPreview, PageNavigator, RelationPanel 등)
│       ├── settings/       # 프로젝트 설정 (OcrSettingsPanel)
│       └── admin/          # 관리자 대시보드 패널 (AdminUsersPanel, AdminProjectsPanel, AdminStatsPanel)
└── tests/
    ├── lib/utils/bbox.test.ts
    ├── lib/utils/interaction.test.ts
    ├── lib/utils/text-layout.test.ts
    ├── lib/utils/text-selection.test.ts
    ├── lib/stores/canvas.test.ts
    ├── lib/stores/pdf.test.ts
    ├── lib/types/element-groups.test.ts
    ├── lib/components/canvas/HybridViewer.test.ts
    ├── lib/components/canvas/TextOverlay.test.ts
    ├── lib/components/panels/PageNavigator.test.ts
    ├── lib/components/panels/ExtractionPreview.test.ts
    └── lib/components/settings/OcrSettingsPanel.test.ts
```

## Routing

SvelteKit 파일 기반 라우팅 (`adapter-static` SPA 모드):

| 경로 | 라우트 파일 | 인증 | 설명 |
| ---- | ---------- | ---- | ---- |
| `/login` | `routes/login/+page.svelte` | 공개 | 로그인 |
| `/register` | `routes/register/+page.svelte` | 공개 | 회원가입 |
| `/` | `routes/+page.svelte` | 필요 | 프로젝트 목록 + 생성 |
| `/projects/[id]` | `routes/projects/[id]/+page.svelte` | 필요 | 문서 목록 + PDF 업로드 |
| `/projects/[id]/settings` | `routes/projects/[id]/settings/+page.svelte` | 필요 | OCR 엔진 설정 |
| `/label/[pageId]` | `routes/label/[pageId]/+page.svelte` | 필요 | 3패널 레이블링 화면 |
| `/admin` | `routes/admin/+page.svelte` | admin | 관리자 대시보드 |
| `/account/security` | `routes/account/security/+page.svelte` | 필요 | 비밀번호 변경 |

## Data Flow

### 인증 흐름

```text
앱 시작 → authStore.initialize() → POST /auth/refresh (silent)
       → 성공: token 저장, 보호된 페이지 접근 허용
       → 실패: /login 리다이렉트

API 요청 → client.ts → Bearer 헤더 주입 → 서버
         → 401: refreshToken() → 재시도 (1회)
         → 성공: 응답 반환
         → 실패: logout() → /login

1분 주기 → shouldRefresh() (만료 2분 전) → refreshToken()
         → checkExpiration() → 만료 시 logout()
```

### 레이블링 흐름

```text
Backend API  →  api/client.ts  →  stores/annotation.svelte.ts  →  components
                                  stores/canvas.svelte.ts
                                  stores/pdf.svelte.ts
                                  stores/ui.svelte.ts
```

1. 페이지 로드 시 `getPage()` API 호출
2. 응답 데이터를 `annotationStore.load()`로 저장
3. `pdf_url`이 있으면 `pdfStore.loadDocument()` → PDF.js 벡터 렌더링
4. `$derived` 속성이 자동으로 elements, selectedElement 등을 계산
5. HybridViewer가 3-layer 구조로 렌더링 (배경 PDF/이미지 → Konva bbox → TextOverlay)
6. 사용자 편집 → store 업데이트 → `isDirty = true`
7. 저장 버튼 → `savePage()` API 호출 → `markSaved()`

## Key Patterns

### Immutability

모든 상태 업데이트는 새 객체를 생성한다 (spread operator):

```typescript
// annotationStore.updateElement()
this.annotationData = {
  ...this.annotationData,
  layout_dets: this.annotationData.layout_dets.map((el) =>
    el.anno_id === annoId ? { ...el, ...updates } : el,
  ),
}
```

### Class-based Stores with Runes

Svelte 5의 `$state`와 `$derived`를 클래스 필드로 사용:

```typescript
class AnnotationStore {
  annotationData = $state<AnnotationData | null>(null)
  elements = $derived(this.annotationData?.layout_dets ?? [])
}
export const annotationStore = new AnnotationStore()
```

### AuthStore (인증 상태 관리)

인증 상태는 `AuthStore` 클래스에서 관리. Access token은 메모리에만 저장 (XSS 방지):

```typescript
class AuthStore {
  token = $state<string | null>(null)          // in-memory only
  isInitialized = $state(false)
  payload = $derived(/* JWT decode */)         // user_id, role, exp
  user = $derived<AuthUser | null>(/* ... */)  // id, name, role
  isAuthenticated = $derived(/* ... */)
  isAdmin = $derived(/* role === 'admin' */)
  mustChangePassword = $derived(/* ... */)
}
```

### Canvas + Store Sync

Konva.js 객체는 `$effect` 내에서 store 상태와 동기화:

```typescript
$effect(() => {
  const _elements = annotationStore.elements
  syncRects(_elements)  // Konva Rect 생성/업데이트/삭제
})
```

## Environment Variables

| 변수 | 기본값 | 설명 |
| ------ | -------- | ------ |
| `VITE_API_URL` | `http://localhost:8000` | 백엔드 API 주소 |

## Scripts

```bash
bun run dev         # 개발 서버 (localhost:5173)
bun run build       # 프로덕션 빌드
bun run preview     # 빌드 결과 미리보기
bun run check       # TypeScript 타입 체크
bun run test        # Vitest 테스트 실행
bun run test:watch  # Vitest watch 모드
```
