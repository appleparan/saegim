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
│   ├── +layout.svelte          # 전역 레이아웃 + ModeWatcher
│   ├── +layout.ts              # ssr=false, prerender=false
│   ├── +page.svelte            # / (프로젝트 목록)
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
│   │   ├── ocr.ts             # OCR 엔진 라벨 매핑 (engineLabels)
│   │   ├── text-layout.ts     # 텍스트 블록 레이아웃 계산
│   │   ├── text-selection.ts  # 텍스트 선택/복사 유틸
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
│   │   ├── pdf.svelte.ts         # PDF.js 문서 로딩/캐싱
│   │   └── ui.svelte.ts          # 사이드바, 알림, 패널탭 (관계 포함)
│   └── components/
│       ├── ui/            # shadcn-svelte (button, badge, card, dialog, ...)
│       ├── common/         # 재사용 UI 위젯 (LoadingSpinner, Select)
│       ├── layout/         # Header, Sidebar (4탭: 요소/속성/텍스트/관계), ThemeToggle
│       ├── canvas/         # 3-layer 뷰어 + 오버레이 (HybridViewer, BboxLayer, ReadingOrderOverlay, RelationOverlay 등)
│       ├── panels/         # 사이드바 패널 (ElementList, AttributePanel, ExtractionPreview, PageNavigator, RelationPanel 등)
│       └── settings/       # 프로젝트 설정 (OcrSettingsPanel)
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

| 경로 | 라우트 파일 | 설명 |
| ------ | -------- | ------ |
| `/` | `routes/+page.svelte` | 프로젝트 목록 + 생성 |
| `/projects/[id]` | `routes/projects/[id]/+page.svelte` | 문서 목록 + PDF 업로드 |
| `/projects/[id]/settings` | `routes/projects/[id]/settings/+page.svelte` | OCR 엔진 설정 (4종 engine_type 선택) |
| `/label/[pageId]` | `routes/label/[pageId]/+page.svelte` | 3패널 레이블링 화면 |

## Data Flow

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
