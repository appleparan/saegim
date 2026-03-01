# Components Reference

## Pages

### ProjectList (`src/routes/+page.svelte`)

프로젝트 목록 페이지. Route: `/`

- 프로젝트 CRUD (목록 조회 + 생성 다이얼로그)
- 로딩/에러/빈 상태 UI
- 각 프로젝트 카드 클릭 시 `/projects/:id`로 이동

### DocumentList (`src/routes/projects/[id]/+page.svelte`)

문서 목록 페이지. Route: `/projects/:id`

- 프로젝트 내 문서 목록 + PDF 업로드 (`<input type="file" accept=".pdf">`)
- 문서 클릭 시 페이지 목록 확장 (accordion)
- 페이지별 상태 뱃지 (대기/진행 중/완료/검토됨)
- 페이지 클릭 시 `/label/:pageId`로 이동

### ProjectSettings (`src/routes/projects/[id]/settings/+page.svelte`)

프로젝트 설정 페이지. Route: `/projects/:id/settings`

- `engine_type` 기반 OCR 엔진 선택 (카드 UI)
  - `commercial_api`: Gemini/vLLM full-page VLM (API key, model)
  - `integrated_server`: PP-StructureV3 또는 vLLM 통합 서버 (host, port, model)
  - `split_pipeline`: PP-StructureV3 레이아웃 + 외부 OCR (layout URL, OCR provider, key/host)
  - `pdfminer`: pdfminer.six 폴백 (추가 설정 불필요)
- 엔진별 세부 설정 폼 (선택한 카드에 따라 동적 표시)
- 연결 테스트 버튼 (`build_engine → test_connection`)
- 문서 목록에서 톱니바퀴 아이콘으로 진입

### LabelingPage (`src/routes/label/[pageId]/+page.svelte`)

3패널 레이블링 화면. Route: `/label/:pageId`

```text
┌──────────────────────────────────────────────────────┐
│  Header (프로젝트명 / 저장 버튼)                        │
├──────────────────────────────────────────────────────┤
│  Breadcrumb (프로젝트 > 문서 > 페이지 N)                │
├───────────┬──────────────────────┬───────────────────┤
│           │  아이콘 툴바          │  요소 | 속성 | 텍스트 │
│ PageNav   │  (S/D/H + 줌 ±%)    │                   │
│ Extraction│  ┌────────────────┐  │   사이드바          │
│ Preview   │  │  HybridViewer  │  │   (w-80)          │
│ 요소 목록  │  │  (3-layer)     │  │                   │
│  (w-64)   │  └────────────────┘  │                   │
│           │  [PDF.js / Image]    │                   │
└───────────┴──────────────────────┴───────────────────┘
```

- 좌측: PageNavigator (페이지 이동) + ExtractionPreview (OCR 결과/상태) + ElementList (요소 목록)
- 중앙: 아이콘 기반 컴팩트 툴바 (선택/그리기/이동 + 줌 퍼센트) + HybridViewer (3-layer 하이브리드 뷰어)
- 우측: Sidebar (탭: 요소 속성 / 페이지 속성 / 텍스트 편집)
- 하단 우측: 렌더링 모드 표시기 (PDF.js / Image)

---

## UI Components (`src/lib/components/ui/`) — shadcn-svelte

shadcn-svelte 기반 컴포넌트. bits-ui 헤드리스 프리미티브 + Tailwind CSS v4 스타일.
전체 목록: button, badge, card, dialog, input, label, popover, select, separator, switch, tabs, textarea.

### Button (`ui/button`)

```svelte
<script>
  import { Button } from '$lib/components/ui/button'
</script>
<Button variant="default" size="sm" onclick={fn}>텍스트</Button>
```

| Variant | 용도 |
| ------ | ------ |
| `default` | 주요 액션 (violet primary) |
| `destructive` | 삭제 등 위험 액션 |
| `outline` | 보조 액션 |
| `secondary` | 부차적 액션 |
| `ghost` | 배경 없는 투명 버튼 |
| `link` | 링크 스타일 |

크기: `default`, `sm`, `lg`, `icon`, `icon-sm`, `icon-lg`

### Switch (`ui/switch`)

Toggle 대체. `checked` → `onCheckedChange` 패턴.

```svelte
<script>
  import { Switch } from '$lib/components/ui/switch'
  import { Label } from '$lib/components/ui/label'
</script>
<div class="flex items-center gap-2">
  <Switch id="watermark" checked={value} onCheckedChange={(v) => handleChange(v)} />
  <Label for="watermark">워터마크</Label>
</div>
```

### 기타 shadcn 컴포넌트

- **Badge**: 상태 표시 (`default`, `secondary`, `destructive`, `outline`)
- **Card**: 카드 레이아웃 (Card, CardHeader, CardTitle, CardContent)
- **Dialog**: 모달 (DialogTrigger, DialogContent, DialogHeader, DialogFooter)
- **Popover**: 팝오버 (PopoverTrigger, PopoverContent, PopoverClose)
- **Input / Textarea**: 폼 입력 (자동 테마 적용)
- **Label**: 폼 라벨
- **Select**: 드롭다운 (SelectTrigger, SelectContent, SelectItem)
- **Separator**: 구분선
- **Tabs**: 탭 네비게이션 (TabsList, TabsTrigger, TabsContent)

## Common Components (`src/lib/components/common/`)

### Select (네이티브)

네이티브 `<select>` 래퍼. 간단한 옵션 목록에 사용 (shadcn Select는 compound component).

```svelte
<Select label="언어" value="ko" options={PAGE_LANGUAGES} labels={PAGE_LANGUAGE_LABELS} onchange={fn} />
```

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `label` | `string?` | - | 라벨 텍스트 |
| `value` | `string` | - | 현재 값 |
| `options` | `readonly string[]` | - | 선택지 배열 |
| `labels` | `Record<string, string>?` | - | 표시 라벨 매핑 |
| `disabled` | `boolean` | `false` | 비활성화 |
| `onchange` | `(value: string) => void` | - | 변경 핸들러 |

### LoadingSpinner

```svelte
<LoadingSpinner message="로딩 중..." size="sm" />
```

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `message` | `string?` | - | 로딩 메시지 |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | 스피너 크기 |

---

## Layout Components (`src/lib/components/layout/`)

### Header

상단 네비게이션 바 (h-14). 좌측 타이틀 + 우측 ThemeToggle + 저장 상태/버튼.

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `title` | `string` | `'saegim'` | 헤더 타이틀 |
| `showSave` | `boolean` | `false` | 저장 버튼 표시 |
| `onsave` | `() => void` | - | 저장 핸들러 |
| `saving` | `boolean` | `false` | 저장 중 상태 |
| `showShortcutHelp` | `boolean` | `false` | 단축키 도움말 버튼 표시 |
| `shortcutHelpOpen` | `boolean` | `false` | 단축키 도움말 팝오버 열림 상태 (bindable) |

알림 토스트도 Header 내에서 렌더링 (`uiStore.notification`).

### ShortcutHelp

키보드 단축키 도움말 팝오버. Header에 포함되며 `showShortcutHelp` prop으로 제어.
키보드 아이콘 클릭 또는 `?` 키로 토글. 카테고리별(도구/편집/보기/탐색/도움말) 그룹핑.

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `open` | `boolean` | `false` | 팝오버 열림 상태 (bindable) |

### ThemeToggle

다크모드 토글 버튼. `mode-watcher`의 `toggleMode()`를 사용.
Sun/Moon 아이콘 전환 애니메이션. Header에 포함.

### Sidebar

탭 네비게이션이 있는 우측 사이드바 (w-80). `uiStore.sidebarOpen`으로 토글.

| 탭 | key | 내용 |
| --- | ------ | ------ |
| 요소 | `'elements'` | AttributePanel |
| 속성 | `'attributes'` | PageAttributePanel |
| 텍스트 | `'text'` | TextEditor |
| 관계 | `'relations'` | RelationPanel |

---

## Canvas Components (`src/lib/components/canvas/`)

3-layer 하이브리드 렌더링 아키텍처:

```text
Layer 1 (z-index: 0)  — 배경: PDF.js <canvas> 또는 <img> 폴백
Layer 2 (z-index: 10) — Konva.js: 이미지 블록 bbox + 선택된 요소 bbox
Layer 3 (z-index: 20) — DOM TextOverlay: 텍스트 블록 위치에 선택 가능한 텍스트 (이미지 폴백 모드만)
```

### HybridViewer

3-layer 하이브리드 뷰어 컨테이너. Konva Stage + PDF.js/이미지 배경 + TextOverlay를 통합 관리한다.

| Prop | Type | 설명 |
| ------ | ------ | ------ |
| `pageProxy` | `PDFPageProxy?` | PDF.js 페이지 (있으면 벡터 렌더링) |
| `imageUrl` | `string?` | 이미지 URL (PDF.js 폴백) |
| `width` | `number` | 이미지 너비 (px) |
| `height` | `number` | 이미지 높이 (px) |

내부 상태 머신:

- `interactionMode`: `'browse'` (기본) → `'edit'` (요소 선택 시)
- browse 모드: 텍스트 선택 가능, bbox는 호버 시만 표시
- edit 모드: bbox 편집 가능, 텍스트 오버레이 비활성화

### PdfRenderer

PDF.js `PDFPageProxy`를 `<canvas>`에 벡터 렌더링한다. `PDF_BASE_SCALE`(2.0)로 고해상도 렌더링 후 CSS transform으로 표시.

| Prop | Type | 설명 |
| ------ | ------ | ------ |
| `pageProxy` | `PDFPageProxy` | PDF.js 페이지 프록시 |

### BboxLayer

`annotationStore.elements`를 Konva Rect로 동기화한다.

| Prop | Type | 설명 |
| ------ | ------ | ------ |
| `stage` | `Konva.Stage` | Konva 스테이지 |
| `filter` | `(el: LayoutElement) => boolean` | 렌더링 필터 (선택적) |
| `interactionMode` | `'browse' \| 'edit'` | 인터랙션 모드 (선택적) |

동작:

- 각 요소를 카테고리 색상으로 렌더링
- browse 모드에서 비선택 요소는 투명 (호버 시 반투명)
- 선택된 요소에 Konva Transformer (리사이즈 핸들) 표시
- 드래그/리사이즈 완료 시 `annotationStore.updateElement()` 호출
- 빈 영역 클릭 시 선택 해제
- 이미지 블록 + 현재 선택된 요소를 렌더링 (텍스트 블록은 TextOverlay가 담당)

### BboxDrawTool

`draw` 모드에서 마우스 드래그로 새 bbox를 그린다.

- mousedown → mousemove → mouseup으로 사각형 생성
- 5px 미만 드래그는 무시 (실수 클릭 방지)
- 생성 후 자동으로 `select` 모드로 전환
- 기본 카테고리: `text_block`

### TextOverlay

텍스트 블록 요소를 DOM 오버레이로 렌더링한다. 이미지 폴백 모드에서만 활성화 (PDF.js 모드에서는 PDF 자체 텍스트 레이어 사용).

- 텍스트 선택/복사 지원
- 요소 클릭 시 `annotationStore.selectElement()` 호출
- `pointerEvents` prop으로 인터랙션 모드에 따라 활성/비활성

### ReadingOrderOverlay

읽기 순서 번호 배지를 캔버스 위에 표시한다. `canvasStore.showReadingOrder`가 `true`일 때만 렌더링.

- 각 요소의 bbox 좌상단에 24x24 원형 배지 표시
- 배지 배경: `getCategoryColor()`로 카테고리별 색상
- 배지 텍스트: `el.order` (0-based 인덱스)
- `O` 단축키 또는 체크박스로 토글

### RelationOverlay

요소 간 관계를 SVG 화살표로 시각화한다.

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `visible` | `boolean` | `true` | 오버레이 표시 여부 |

- 관계 유형별 색상 코딩:
  - `parent_son` (#6366f1), `figure_caption` (#22c55e)
  - `table_caption` (#f59e0b), `table_footnote` (#ef4444)
  - `equation_caption` (#a855f7), `code_caption` (#06b6d4)
- 점선(6 3) 스트로크, 화살표 마커
- opacity 0.7, stroke-width 2
- 요소 중심점 간 연결선

---

## Panel Components (`src/lib/components/panels/`)

### ElementList

요소 목록 패널. 좌측 사이드바에 표시.

- 카테고리 색상 인디케이터
- 한국어 카테고리 라벨
- 클릭으로 요소 선택
- hover 시 삭제(X) 버튼 + 드래그 핸들 (6dot)
- HTML5 드래그앤드롭으로 읽기 순서 재정렬
- 드래그 중 반투명 효과 + 드롭 대상 상단 보더 시각 피드백
- 순서 변경 시 `reorderElements()` + `updateReadingOrder()` API 호출

### CategorySelect

블록 카테고리 드롭다운 (18개 항목, 한국어 라벨).

| Prop | Type | 설명 |
| ------ | ------ | ------ |
| `value` | `BlockCategoryType` | 현재 카테고리 |
| `onchange` | `(category: BlockCategoryType) => void` | 변경 핸들러 |

### AttributePanel

선택된 요소의 속성을 편집하는 패널.

- 카테고리 선택 (CategorySelect)
- 무시 토글
- 카테고리별 동적 속성 폼 (CATEGORY_ATTRIBUTES 매핑 기반)

### PageAttributePanel

페이지 수준 속성 편집.

- 데이터 출처 (11개 항목)
- 언어 (4개 항목)
- 레이아웃 (5개 항목)
- 워터마크/흐린 스캔/컬러 배경 토글

### PageNavigator

다중 페이지 문서에서 페이지 간 이동을 지원하는 컴팩트 네비게이터.

| Prop | Type | 설명 |
| ------ | ------ | ------ |
| `pages` | `readonly PageSummary[]` | 페이지 목록 |
| `currentPageId` | `string` | 현재 페이지 ID |

- 좌/우 화살표로 이전/다음 페이지 이동
- 현재 위치 표시 (N / M)
- 페이지 상태 뱃지 (대기/진행 중/제출/검토)
- 시맨틱 테마 토큰 사용 (다크모드 호환)

### ExtractionPreview

자동 추출 결과 프리뷰 배너. LabelingPage 좌측에 표시.

4가지 상태:

1. **추출 중** (`documentStatus === 'extracting'`): 스피너 + "OCR 추출 진행 중..." 메시지
2. **결과 없음** (auto_extracted_data 없고 어노테이션도 비어있을 때): "자동 추출 결과가 없습니다" + OCR 설정 링크
3. **수락 대기** (auto_extracted_data 있고 어노테이션 비어있을 때): 요소 수 표시 + 수락/무시 버튼 (파란색 테마)
4. **강제 수락 대기** (auto_extracted_data 있고 어노테이션이 존재할 때): 요소 수 표시 + "수락하면 기존 주석이 대체됩니다" 경고 + 수락/무시 버튼 (보라색 테마)

- 추출된 요소 수 표시 (텍스트 N개, 이미지 N개 — 총 N개 요소)
- "수락" 버튼 → `acceptExtraction()` 또는 `forceAcceptExtraction()` API 호출 → 어노테이션 갱신
- "무시" 버튼 → 배너 닫기 (세션 내 `dismissed` 상태)
- × 버튼으로도 닫기 가능
- "전체 재스캔" 버튼 → 현재 OCR 엔진으로 문서 전체 재추출 (`reExtractDocument()`)

| Prop | Type | 설명 |
| ------ | ------ | ------ |
| `pageId` | `string` | 페이지 UUID |
| `autoExtractedData` | `AnnotationData \| null` | 자동 추출 데이터 |
| `annotationData` | `AnnotationData \| null` | 현재 어노테이션 데이터 |
| `documentId` | `string` | 문서 UUID (재추출용) |
| `documentStatus` | `DocumentStatus?` | 문서 처리 상태 |
| `onAccepted` | `(data: AnnotationData) => void` | 수락 후 콜백 |
| `onReExtract` | `() => void` | 재스캔 요청 콜백 |

### TextEditor

선택된 요소의 텍스트 편집 (Text / LaTeX / HTML 탭).

- 탭 전환으로 `text`, `latex`, `html` 필드 편집
- monospace 폰트 textarea

### RelationPanel

선택된 요소의 관계(relation)를 관리하는 패널. 사이드바 "관계" 탭에 표시.

- 선택된 요소의 ID·카테고리 정보 표시
- 연결된 관계 목록 (incoming: ←, outgoing: →)
- 관계 추가: 대상 요소 선택 + 관계 유형 드롭다운 (6종)
- hover 시 삭제 버튼
- API 연동: `createRelation()` / `deleteRelation()` 호출

---

## Settings Components (`src/lib/components/settings/`)

### OcrSettingsPanel

OCR 엔진 설정 폼 컴포넌트.

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `config` | `OcrConfigResponse` | - | 현재 OCR 설정 |
| `saving` | `boolean` | `false` | 저장 중 상태 |
| `testing` | `boolean` | `false` | 테스트 중 상태 |
| `testResult` | `OcrConnectionTestResponse \| null` | `null` | 연결 테스트 결과 |
| `onsave` | `(config: OcrConfigResponse) => void` | - | 저장 핸들러 |
| `ontest` | `(config: OcrConfigResponse) => void` | - | 연결 테스트 핸들러 |

기능:

- `engine_type` 카드 선택 UI (4종: commercial_api, integrated_server, split_pipeline, pdfminer)
- 선택한 엔진 카드에 따라 세부 설정 폼 동적 표시
  - `commercial_api`: provider (gemini/vllm), API key, model
  - `integrated_server`: host, port, model (PP-StructureV3 또는 vLLM 자동 분기)
  - `split_pipeline`: layout server URL, OCR provider, key/host/port/model
  - `pdfminer`: 추가 설정 없음
- 연결 테스트 버튼 (`build_engine → test_connection`)
- 저장 시 test-then-save 패턴 (연결 테스트 성공 후 저장)
- 유효성 검증 (엔진 타입별 필수 필드 체크)
