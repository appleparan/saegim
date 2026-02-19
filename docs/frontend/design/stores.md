# State Management

Svelte 5 runes 기반 class store 패턴을 사용한다. 각 store는 `$state`로 반응형 상태를, `$derived`로 파생 값을 정의한다. 싱글톤 인스턴스를 `export const`로 내보낸다.

## AnnotationStore (`src/lib/stores/annotation.svelte.ts`)

페이지 어노테이션 데이터의 전체 생명주기를 관리한다.

### State

| 필드 | 타입 | 설명 |
| ------ | ------ | ------ |
| `pageId` | `string \| null` | 현재 페이지 ID |
| `annotationData` | `AnnotationData \| null` | 전체 어노테이션 (OmniDocBench) |
| `selectedElementId` | `number \| null` | 선택된 요소의 anno_id |
| `isDirty` | `boolean` | 저장되지 않은 변경 존재 여부 |
| `isLoading` | `boolean` | 로딩 상태 |
| `error` | `string \| null` | 에러 메시지 |

### Derived

| 필드 | 타입 | 설명 |
| ------ | ------ | ------ |
| `elements` | `readonly LayoutElement[]` | `annotationData.layout_dets` |
| `selectedElement` | `LayoutElement \| null` | 선택된 요소 객체 |
| `pageAttribute` | `PageAttribute \| null` | 페이지 속성 |
| `relations` | `readonly Relation[]` | 요소 간 관계 |

### Methods

| 메서드 | 설명 |
| -------- | ------ |
| `load(pageId, data)` | 페이지 데이터 로드, dirty 초기화 |
| `clear()` | 전체 상태 초기화 |
| `selectElement(annoId)` | 요소 선택 (null = 해제) |
| `updateElement(annoId, updates)` | 요소 필드 업데이트 (immutable) |
| `updateElementAttribute(annoId, key, value)` | 요소 속성 값 업데이트 |
| `addElement(categoryType, poly)` | 새 요소 추가, anno_id 반환 |
| `removeElement(annoId)` | 요소 삭제 + 관련 relation 삭제 |
| `updatePageAttribute(updates)` | 페이지 속성 업데이트 |
| `markSaved()` | isDirty = false |
| `setLoading(loading)` | 로딩 상태 설정 |
| `setError(error)` | 에러 메시지 설정 |

### Immutability 규칙

모든 mutation은 새 객체를 생성한다:

```typescript
// updateElement 예시
this.annotationData = {
  ...this.annotationData,
  layout_dets: this.annotationData.layout_dets.map((el) =>
    el.anno_id === annoId ? { ...el, ...updates } : el,
  ),
}
```

`removeElement`는 요소와 관련 relation을 함께 제거한다.

---

## CanvasStore (`src/lib/stores/canvas.svelte.ts`)

Canvas 뷰포트 상태를 관리한다.

### State

| 필드 | 타입 | 기본값 | 설명 |
| ------ | ------ | -------- | ------ |
| `toolMode` | `'select' \| 'draw' \| 'pan'` | `'select'` | 현재 도구 모드 |
| `scale` | `number` | `1` | 줌 배율 (0.1 ~ 10) |
| `offsetX` | `number` | `0` | 뷰포트 X 오프셋 |
| `offsetY` | `number` | `0` | 뷰포트 Y 오프셋 |
| `imageWidth` | `number` | `0` | 이미지 너비 |
| `imageHeight` | `number` | `0` | 이미지 높이 |
| `imageLoaded` | `boolean` | `false` | 이미지 로드 완료 |

### Derived

| 필드 | 타입 | 설명 |
| ------ | ------ | ------ |
| `viewport` | `ViewportState` | `{ scale, offsetX, offsetY }` |

### Methods

| 메서드 | 설명 |
| -------- | ------ |
| `setTool(mode)` | 도구 모드 변경 |
| `setScale(scale)` | 줌 레벨 설정 (min/max 클램프) |
| `setOffset(x, y)` | 뷰포트 오프셋 설정 |
| `resetView()` | 1:1 원본 크기로 리셋 |
| `setImageDimensions(w, h)` | 이미지 크기 설정 |
| `zoomIn()` | 1.2배 확대 |
| `zoomOut()` | 1.2배 축소 |
| `fitToContainer(w, h)` | 컨테이너에 맞춰 줌/센터링 |

---

## UiStore (`src/lib/stores/ui.svelte.ts`)

UI 상태 (사이드바, 알림)를 관리한다.

### State

| 필드 | 타입 | 기본값 | 설명 |
| ------ | ------ | -------- | ------ |
| `sidebarOpen` | `boolean` | `true` | 사이드바 열림 |
| `activePanel` | `PanelTab` | `'elements'` | 활성 탭 |
| `notification` | `Notification \| null` | `null` | 알림 토스트 |

### Types

```typescript
type PanelTab = 'elements' | 'attributes' | 'text'
type NotificationType = 'info' | 'error' | 'success'
interface Notification { message: string; type: NotificationType }
```

### Methods

| 메서드 | 설명 |
| -------- | ------ |
| `toggleSidebar()` | 사이드바 토글 |
| `setActivePanel(panel)` | 탭 변경 |
| `showNotification(message, type)` | 알림 표시 (3초 후 자동 소멸) |
| `dismissNotification()` | 알림 즉시 닫기 |
