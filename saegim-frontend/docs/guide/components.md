# Components Reference

## Pages

### ProjectList (`src/pages/ProjectList.svelte`)

프로젝트 목록 페이지. Route: `#/`

- 프로젝트 CRUD (목록 조회 + 생성 다이얼로그)
- 로딩/에러/빈 상태 UI
- 각 프로젝트 카드 클릭 시 `#/projects/:id`로 이동

### DocumentList (`src/pages/DocumentList.svelte`)

문서 목록 페이지. Route: `#/projects/:id`

- 프로젝트 내 문서 목록 + PDF 업로드 (`<input type="file" accept=".pdf">`)
- 문서 클릭 시 페이지 목록 확장 (accordion)
- 페이지별 상태 뱃지 (대기/진행 중/완료/검토됨)
- 페이지 클릭 시 `#/label/:pageId`로 이동

### ProjectSettings (`src/pages/ProjectSettings.svelte`)

프로젝트 설정 페이지. Route: `#/projects/:id/settings`

- OCR 프로바이더 선택 (MinerU / PyMuPDF / Gemini / vLLM)
- Gemini: API Key, 모델명 설정
- vLLM: 호스트, 포트, 모델명 설정
- 연결 테스트 버튼 (Gemini/vLLM)
- 문서 목록에서 톱니바퀴 아이콘으로 진입

### LabelingPage (`src/pages/LabelingPage.svelte`)

3패널 레이블링 화면. Route: `#/label/:pageId`

```text
┌──────────────────────────────────────────────────┐
│                    Header (저장 버튼)              │
├──────────┬──────────────────────┬─────────────────┤
│          │                      │  요소 | 속성 | 텍스트 │
│  요소 목록 │   Canvas (Konva.js)  │                 │
│  (w-64)  │   + 툴바             │   사이드바        │
│          │                      │   (w-80)        │
└──────────┴──────────────────────┴─────────────────┘
```

- 좌측: ElementList (요소 목록 + 색상 인디케이터)
- 중앙: ImageViewer + 툴바 (선택/그리기/이동 + 줌)
- 우측: Sidebar (탭: 요소 속성 / 페이지 속성 / 텍스트 편집)

---

## Common Components (`src/lib/components/common/`)

### Button

```svelte
<Button variant="primary" size="sm" active={true} onclick={fn}>텍스트</Button>
```

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `variant` | `'primary' \| 'secondary' \| 'danger' \| 'ghost'` | `'secondary'` | 스타일 변형 |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | 크기 |
| `disabled` | `boolean` | `false` | 비활성화 |
| `active` | `boolean` | `false` | 활성 상태 (ring 표시) |
| `onclick` | `(e: MouseEvent) => void` | - | 클릭 핸들러 |
| `children` | `Snippet` | - | 버튼 내용 |

### Select

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

### Toggle

```svelte
<Toggle label="워터마크" checked={false} onchange={fn} />
```

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `label` | `string?` | - | 라벨 텍스트 |
| `checked` | `boolean` | - | 토글 상태 |
| `disabled` | `boolean` | `false` | 비활성화 |
| `onchange` | `(checked: boolean) => void` | - | 변경 핸들러 |

### LoadingSpinner

```svelte
<LoadingSpinner message="로딩 중..." size="sm" />
```

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `message` | `string?` | - | 로딩 메시지 |
| `size` | `'sm' \| 'md'` | `'md'` | 스피너 크기 |

---

## Layout Components (`src/lib/components/layout/`)

### Header

상단 네비게이션 바 (h-14). 좌측 타이틀 + 우측 저장 상태/버튼.

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `title` | `string` | `'saegim'` | 헤더 타이틀 |
| `showSave` | `boolean` | `false` | 저장 버튼 표시 |
| `onsave` | `() => void` | - | 저장 핸들러 |
| `saving` | `boolean` | `false` | 저장 중 상태 |

알림 토스트도 Header 내에서 렌더링 (`uiStore.notification`).

### Sidebar

탭 네비게이션이 있는 우측 사이드바 (w-80). `uiStore.sidebarOpen`으로 토글.

| 탭 | key | 내용 |
| --- | ------ | ------ |
| 요소 | `'elements'` | AttributePanel |
| 속성 | `'attributes'` | PageAttributePanel |
| 텍스트 | `'text'` | TextEditor |

---

## Canvas Components (`src/lib/components/canvas/`)

### ImageViewer

Konva.js Stage를 생성하고 이미지를 로드한다. 줌(마우스 휠), 팬(드래그/중간버튼), 리사이즈 대응.

| Prop | Type | 설명 |
| ------ | ------ | ------ |
| `imageUrl` | `string` | 이미지 URL |
| `width` | `number` | 이미지 너비 (px) |
| `height` | `number` | 이미지 높이 (px) |

내부적으로 BboxLayer와 BboxDrawTool을 자식으로 마운트한다.

### BboxLayer

`annotationStore.elements`를 Konva Rect로 동기화한다.

- 각 요소를 카테고리 색상으로 렌더링
- 선택된 요소에 Konva Transformer (리사이즈 핸들) 표시
- 드래그/리사이즈 완료 시 `annotationStore.updateElement()` 호출
- 빈 영역 클릭 시 선택 해제

### BboxDrawTool

`draw` 모드에서 마우스 드래그로 새 bbox를 그린다.

- mousedown → mousemove → mouseup으로 사각형 생성
- 5px 미만 드래그는 무시 (실수 클릭 방지)
- 생성 후 자동으로 `select` 모드로 전환
- 기본 카테고리: `text_block`

---

## Panel Components (`src/lib/components/panels/`)

### ElementList

요소 목록 패널. 좌측 사이드바에 표시.

- 카테고리 색상 인디케이터
- 한국어 카테고리 라벨
- 클릭으로 요소 선택
- hover 시 삭제(X) 버튼

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

### ExtractionPreview

자동 추출 결과 프리뷰 배너. LabelingPage 좌측 상단에 표시.

- `auto_extracted_data`가 있고 `annotation_data.layout_dets`가 비어있을 때만 표시
- 추출된 요소 수 표시 (텍스트 N개, 이미지 N개 — 총 N개 요소)
- "수락" 버튼 → `acceptExtraction()` API 호출 → 어노테이션 갱신
- "무시" 버튼 → 배너 닫기 (세션 내 `dismissed` 상태)
- × 버튼으로도 닫기 가능

| Prop | Type | 설명 |
| ------ | ------ | ------ |
| `pageId` | `string` | 페이지 UUID |
| `autoExtractedData` | `AnnotationData \| null` | 자동 추출 데이터 |
| `onAccepted` | `(data: AnnotationData) => void` | 수락 후 콜백 |

### TextEditor

선택된 요소의 텍스트 편집 (Text / LaTeX / HTML 탭).

- 탭 전환으로 `text`, `latex`, `html` 필드 편집
- monospace 폰트 textarea

---

## Settings Components (`src/lib/components/settings/`)

### OcrSettingsPanel

OCR 프로바이더 설정 폼 컴포넌트.

| Prop | Type | Default | 설명 |
| ------ | ------ | --------- | ------ |
| `config` | `OcrConfigResponse` | - | 현재 OCR 설정 |
| `saving` | `boolean` | `false` | 저장 중 상태 |
| `testing` | `boolean` | `false` | 테스트 중 상태 |
| `testResult` | `OcrConnectionTestResponse \| null` | `null` | 연결 테스트 결과 |
| `onsave` | `(config: OcrConfigResponse) => void` | - | 저장 핸들러 |
| `ontest` | `(config: OcrConfigResponse) => void` | - | 연결 테스트 핸들러 |

기능:
- 4개 프로바이더 선택 (카드 UI): MinerU, PyMuPDF, Gemini, vLLM
- Gemini 선택 시 API Key (password) + 모델명 입력 표시
- vLLM 선택 시 호스트 + 포트 + 모델명 입력 표시
- 연결 테스트 버튼 (Gemini/vLLM만 표시)
- 유효성 검증 (Gemini: API Key 필수, vLLM: 호스트 필수)
