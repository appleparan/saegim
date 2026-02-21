# Saegim Frontend Architecture

## Overview

Saegim 프론트엔드는 한국어 문서 VLM 벤치마크를 위한 레이블링 웹앱이다. OmniDocBench JSON 형식의 어노테이션 데이터를 Canvas 위에서 편집하고 FastAPI 백엔드에 저장한다.

## Tech Stack

| 영역 | 기술 | 버전 |
| ------ | ------ | ------ |
| UI Framework | Svelte 5 (runes) | ^5.43 |
| Build Tool | Vite | ^7.2 |
| Styling | Tailwind CSS 4 + shadcn-svelte (bits-ui) | ^4.1 |
| Theme | Violet 테마 (OKLCH CSS 변수) + 다크모드 (mode-watcher) | - |
| Canvas | Konva.js | ^10.2 |
| Router | svelte-spa-router | ^4.0 |
| Test | Vitest + jsdom | ^4.0 |
| Package Manager | Bun | - |

## Directory Structure

```text
src/
├── main.ts                 # 앱 마운트
├── App.svelte              # 라우터 + 전역 레이아웃 + ModeWatcher
├── app.css                 # Tailwind + shadcn 테마 CSS 변수 (violet OKLCH) + 카테고리 색상
├── pages/                  # 라우트별 페이지
│   ├── ProjectList.svelte      # /
│   ├── DocumentList.svelte     # /projects/:id
│   ├── ProjectSettings.svelte  # /projects/:id/settings (OCR 설정)
│   └── LabelingPage.svelte     # /label/:pageId
├── lib/
│   ├── types/              # 타입 정의
│   │   ├── omnidocbench.ts     # AnnotationData, LayoutElement, Poly 등
│   │   ├── categories.ts      # 18개 블록 카테고리, 속성 enum, 한국어 라벨
│   │   └── canvas.ts          # Point, Rect, ToolMode, ViewportState
│   ├── utils/              # 순수 함수
│   │   ├── bbox.ts             # 좌표 변환 (poly <-> rect, screen <-> image)
│   │   ├── color.ts            # 카테고리별 색상
│   │   └── validation.ts      # 어노테이션 유효성 검증
│   ├── api/                # HTTP 클라이언트
│   │   ├── client.ts           # fetch 래퍼 + ApiError/NetworkError
│   │   ├── types.ts            # API request/response 타입
│   │   ├── projects.ts
│   │   ├── documents.ts
│   │   ├── pages.ts
│   │   ├── elements.ts
│   │   └── relations.ts
│   ├── stores/             # Svelte 5 runes 상태 관리
│   │   ├── annotation.svelte.ts  # 어노테이션 데이터 + CRUD
│   │   ├── canvas.svelte.ts      # 뷰포트 (zoom/pan/tool)
│   │   └── ui.svelte.ts          # 사이드바, 알림
│   └── components/
│       ├── ui/            # shadcn-svelte 컴포넌트 (button, badge, card, dialog, input, label, select, separator, switch, tabs, textarea)
│       ├── common/         # 재사용 UI 위젯 (LoadingSpinner, Select)
│       ├── layout/         # Header, Sidebar, ThemeToggle
│       ├── canvas/         # Konva.js 통합 (HybridViewer, BboxLayer, BboxDrawTool, TextOverlay)
│       ├── panels/         # 사이드바 패널 (ElementList, AttributePanel, ExtractionPreview 등)
│       └── settings/       # 프로젝트 설정 (OcrSettingsPanel)
└── tests/
    └── lib/utils/bbox.test.ts
```

## Routing

Hash-based SPA 라우팅 (`svelte-spa-router`):

| 경로 | 페이지 | 설명 |
| ------ | -------- | ------ |
| `#/` | ProjectList | 프로젝트 목록 + 생성 |
| `#/projects/:id` | DocumentList | 문서 목록 + PDF 업로드 |
| `#/projects/:id/settings` | ProjectSettings | OCR 엔진 설정 (engine_type 선택) |
| `#/label/:pageId` | LabelingPage | 3패널 레이블링 화면 |

## Data Flow

```text
Backend API  →  api/client.ts  →  stores/annotation.svelte.ts  →  components
                                  stores/canvas.svelte.ts
                                  stores/ui.svelte.ts
```

1. 페이지 로드 시 `getPage()` API 호출
2. 응답 데이터를 `annotationStore.load()`로 저장
3. `$derived` 속성이 자동으로 elements, selectedElement 등을 계산
4. Canvas 컴포넌트와 패널이 store를 구독하여 렌더링
5. 사용자 편집 → store 업데이트 → `isDirty = true`
6. 저장 버튼 → `savePage()` API 호출 → `markSaved()`

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
