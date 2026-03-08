# State Management

Uses a class store pattern based on Svelte 5 runes. Each store defines reactive state with `$state` and derived values with `$derived`. Singleton instances are exported via `export const`.

## AnnotationStore (`src/lib/stores/annotation.svelte.ts`)

Manages the entire lifecycle of page annotation data.

### State

| Field | Type | Description |
| ------ | ------ | ------ |
| `pageId` | `string \| null` | Current page ID |
| `annotationData` | `AnnotationData \| null` | Full annotation data (OmniDocBench) |
| `selectedElementId` | `number \| null` | anno_id of the selected element |
| `isDirty` | `boolean` | Whether unsaved changes exist |
| `isLoading` | `boolean` | Loading state |
| `error` | `string \| null` | Error message |

### Derived

| Field | Type | Description |
| ------ | ------ | ------ |
| `elements` | `readonly LayoutElement[]` | `annotationData.layout_dets` |
| `selectedElement` | `LayoutElement \| null` | Selected element object |
| `pageAttribute` | `PageAttribute \| null` | Page attributes |
| `relations` | `readonly Relation[]` | Relations between elements |

### Methods

| Method | Description |
| -------- | ------ |
| `load(pageId, data)` | Load page data, reset dirty state |
| `clear()` | Reset all state |
| `selectElement(annoId)` | Select an element (null = deselect) |
| `updateElement(annoId, updates)` | Update element fields (immutable) |
| `updateElementAttribute(annoId, key, value)` | Update an element attribute value |
| `addElement(categoryType, poly)` | Add a new element, returns anno_id |
| `removeElement(annoId)` | Delete element + related relations |
| `updatePageAttribute(updates)` | Update page attributes |
| `reorderElements(orderMap)` | Reorder reading order (anno_id -> order mapping) |
| `swapElementOrder(annoId1, annoId2)` | Swap the order of two elements |
| `addRelation(source, target, type)` | Add a relation (extra.relation[]) |
| `removeRelation(source, target)` | Remove a relation |
| `getRelationsForElement(annoId)` | Get the list of relations for a specific element |
| `markSaved()` | isDirty = false |
| `setLoading(loading)` | Set loading state |
| `setError(error)` | Set error message |

### Immutability Rules

All mutations create new objects:

```typescript
// updateElement example
this.annotationData = {
  ...this.annotationData,
  layout_dets: this.annotationData.layout_dets.map((el) =>
    el.anno_id === annoId ? { ...el, ...updates } : el,
  ),
}
```

`removeElement` removes both the element and its related relations.

---

## CanvasStore (`src/lib/stores/canvas.svelte.ts`)

Manages canvas viewport state.

### State

| Field | Type | Default | Description |
| ------ | ------ | -------- | ------ |
| `toolMode` | `'select' \| 'draw' \| 'pan'` | `'select'` | Current tool mode |
| `scale` | `number` | `1` | Zoom scale (0.1 ~ 10) |
| `offsetX` | `number` | `0` | Viewport X offset |
| `offsetY` | `number` | `0` | Viewport Y offset |
| `imageWidth` | `number` | `0` | Image width |
| `imageHeight` | `number` | `0` | Image height |
| `imageLoaded` | `boolean` | `false` | Image loaded |
| `showReadingOrder` | `boolean` | `false` | Show reading order overlay |

### Derived

| Field | Type | Description |
| ------ | ------ | ------ |
| `viewport` | `ViewportState` | `{ scale, offsetX, offsetY }` |

### Methods

| Method | Description |
| -------- | ------ |
| `setTool(mode)` | Change tool mode |
| `setScale(scale)` | Set zoom level (min/max clamped) |
| `setOffset(x, y)` | Set viewport offset |
| `resetView()` | Reset to 1:1 original size |
| `setImageDimensions(w, h)` | Set image dimensions |
| `zoomIn()` | Zoom in by 1.2x |
| `zoomOut()` | Zoom out by 1.2x |
| `fitToContainer(w, h)` | Zoom/center to fit container |
| `toggleReadingOrder()` | Toggle reading order overlay |

---

## PdfStore (`src/lib/stores/pdf.svelte.ts`)

Manages PDF.js document loading and page caching. Wraps `pdfjs-dist`'s `PDFDocumentProxy`/`PDFPageProxy`.

### Constants

| Name | Value | Description |
| ------ | ------ | ------ |
| `PDF_BASE_SCALE` | `2.0` | Rendering scale compatible with pypdfium2 `render(scale=2.0)` |

### State

| Field | Type | Default | Description |
| ------ | ------ | -------- | ------ |
| `pdfDoc` | `PDFDocumentProxy \| null` | `null` | Loaded PDF document |
| `currentPageNo` | `number` | `1` | Current page number (1-based) |
| `totalPages` | `number` | `0` | Total number of pages |
| `isLoading` | `boolean` | `false` | Loading state |
| `error` | `string \| null` | `null` | Error message |

### Methods

| Method | Description |
| -------- | ------ |
| `loadDocument(url)` | Load PDF from URL (caches same URL) |
| `getPage(pageNo)` | Return page proxy (cached) |
| `setCurrentPage(pageNo)` | Change current page |
| `nextPage()` | Go to next page |
| `prevPage()` | Go to previous page |
| `destroy()` | Clean up resources (cache, release document) |

### PDF.js Worker Setup

The worker URL is automatically resolved based on `import.meta.url`:

```typescript
GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()
```

---

## UiStore (`src/lib/stores/ui.svelte.ts`)

Manages UI state (sidebar, notifications).

### State

| Field | Type | Default | Description |
| ------ | ------ | -------- | ------ |
| `sidebarOpen` | `boolean` | `true` | Sidebar open |
| `activePanel` | `PanelTab` | `'elements'` | Active tab |
| `notification` | `Notification \| null` | `null` | Notification toast |

### Types

```typescript
type PanelTab = 'elements' | 'attributes' | 'text' | 'relations'
type NotificationType = 'info' | 'error' | 'success'
interface Notification { message: string; type: NotificationType }
```

### Methods

| Method | Description |
| -------- | ------ |
| `toggleSidebar()` | Toggle sidebar |
| `setActivePanel(panel)` | Change tab |
| `showNotification(message, type)` | Show notification (auto-dismiss after 3 seconds) |
| `dismissNotification()` | Dismiss notification immediately |
