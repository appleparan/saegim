# Components Reference

## Pages

### ProjectList (`src/routes/+page.svelte`)

Project list page. Route: `/`

- Project CRUD (list view + create dialog)
- Loading/error/empty state UI
- Click on each project card navigates to `/projects/:id`

### DocumentList (`src/routes/projects/[id]/+page.svelte`)

Document list page. Route: `/projects/:id`

- Document list within a project + PDF upload (`<input type="file" accept=".pdf">`)
- Click on a document expands the page list (accordion)
- Per-page status badges (pending/in progress/completed/reviewed)
- Click on a page navigates to `/label/:pageId`

### ProjectSettings (`src/routes/projects/[id]/settings/+page.svelte`)

Project settings page. Route: `/projects/:id/settings`

- Multi-instance engine management (EngineCard-based UI)
  - Multiple engines of the same type can be registered (e.g., vLLM server A, B)
  - Engine types: `commercial_api` (Gemini API), `vllm`, `split_pipeline` (Docling+OCR)
  - `pdfminer` is always available as a fallback (no registration needed)
- Default engine configuration (for full-page OCR)
- Inline connection status icon on each engine card (connected/failed/untested)
- Engine add dialog (EngineAddDialog)
- Accessed via the gear icon in the document list

### LabelingPage (`src/routes/label/[pageId]/+page.svelte`)

3-panel labeling screen. Route: `/label/:pageId`

```text
┌──────────────────────────────────────────────────────┐
│  Header (Project name / Save button)                 │
├──────────────────────────────────────────────────────┤
│  Breadcrumb (Project > Document > Page N)            │
├───────────┬──────────────────────┬───────────────────┤
│           │  Icon Toolbar        │  Element | Attr | Text │
│ PageNav   │  (S/D/H + Zoom ±%)  │                   │
│ Extraction│  ┌────────────────┐  │   Sidebar         │
│ Preview   │  │  HybridViewer  │  │   (w-80)          │
│ Element   │  │  (3-layer)     │  │                   │
│ List      │  └────────────────┘  │                   │
│  (w-64)   │  [PDF.js / Image]    │                   │
└───────────┴──────────────────────┴───────────────────┘
```

- Left: PageNavigator (page navigation) + ExtractionPreview (OCR results/status) + ElementList (element list)
- Center: Icon-based compact toolbar (select/draw/pan + zoom percentage) + HybridViewer (3-layer hybrid viewer)
- Right: Sidebar (tabs: element attributes / page attributes / text editing)
- Bottom right: Rendering mode indicator (PDF.js / Image)

---

## UI Components (`src/lib/components/ui/`) -- shadcn-svelte

shadcn-svelte based components. bits-ui headless primitives + Tailwind CSS v4 styling.
Full list: button, badge, card, dialog, input, label, popover, select, separator, switch, tabs, textarea.

### Button (`ui/button`)

```svelte
<script>
  import { Button } from '$lib/components/ui/button'
</script>
<Button variant="default" size="sm" onclick={fn}>Text</Button>
```

| Variant | Usage |
| ------ | ------ |
| `default` | Primary action (violet primary) |
| `destructive` | Dangerous actions like delete |
| `outline` | Secondary action |
| `secondary` | Tertiary action |
| `ghost` | Transparent button without background |
| `link` | Link style |

Sizes: `default`, `sm`, `lg`, `icon`, `icon-sm`, `icon-lg`

### Switch (`ui/switch`)

Toggle replacement. `checked` -> `onCheckedChange` pattern.

```svelte
<script>
  import { Switch } from '$lib/components/ui/switch'
  import { Label } from '$lib/components/ui/label'
</script>
<div class="flex items-center gap-2">
  <Switch id="watermark" checked={value} onCheckedChange={(v) => handleChange(v)} />
  <Label for="watermark">Watermark</Label>
</div>
```

### Other shadcn Components

- **Badge**: Status display (`default`, `secondary`, `destructive`, `outline`)
- **Card**: Card layout (Card, CardHeader, CardTitle, CardContent)
- **Dialog**: Modal (DialogTrigger, DialogContent, DialogHeader, DialogFooter)
- **Popover**: Popover (PopoverTrigger, PopoverContent, PopoverClose)
- **Input / Textarea**: Form inputs (auto-themed)
- **Label**: Form label
- **Select**: Dropdown (SelectTrigger, SelectContent, SelectItem)
- **Separator**: Divider
- **Tabs**: Tab navigation (TabsList, TabsTrigger, TabsContent)

## Common Components (`src/lib/components/common/`)

### Select (Native)

Native `<select>` wrapper. Used for simple option lists (shadcn Select is a compound component).

```svelte
<Select label="Language" value="ko" options={PAGE_LANGUAGES} labels={PAGE_LANGUAGE_LABELS} onchange={fn} />
```

| Prop | Type | Default | Description |
| ------ | ------ | --------- | ------ |
| `label` | `string?` | - | Label text |
| `value` | `string` | - | Current value |
| `options` | `readonly string[]` | - | Options array |
| `labels` | `Record<string, string>?` | - | Display label mapping |
| `disabled` | `boolean` | `false` | Disabled |
| `onchange` | `(value: string) => void` | - | Change handler |

### LoadingSpinner

```svelte
<LoadingSpinner message="Loading..." size="sm" />
```

| Prop | Type | Default | Description |
| ------ | ------ | --------- | ------ |
| `message` | `string?` | - | Loading message |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Spinner size |

---

## Layout Components (`src/lib/components/layout/`)

### Header

Top navigation bar (h-14). Left title + right ThemeToggle + save status/button.

| Prop | Type | Default | Description |
| ------ | ------ | --------- | ------ |
| `title` | `string` | `'saegim'` | Header title |
| `showSave` | `boolean` | `false` | Show save button |
| `onsave` | `() => void` | - | Save handler |
| `saving` | `boolean` | `false` | Saving state |
| `showShortcutHelp` | `boolean` | `false` | Show shortcut help button |
| `shortcutHelpOpen` | `boolean` | `false` | Shortcut help popover open state (bindable) |

Notification toasts are also rendered within Header (`uiStore.notification`).

### ShortcutHelp

Keyboard shortcut help popover. Included in Header and controlled via `showShortcutHelp` prop.
Toggled by clicking the keyboard icon or pressing the `` ` `` key. Grouped by category (tools/edit/view/navigation/help).

| Prop | Type | Default | Description |
| ------ | ------ | --------- | ------ |
| `open` | `boolean` | `false` | Popover open state (bindable) |

### ThemeToggle

Dark mode toggle button. Uses `mode-watcher`'s `toggleMode()`.
Sun/Moon icon transition animation. Included in Header.

### Sidebar

Right sidebar with tab navigation (w-80). Toggled via `uiStore.sidebarOpen`.

| Tab | key | Content |
| --- | ------ | ------ |
| Elements | `'elements'` | AttributePanel |
| Attributes | `'attributes'` | PageAttributePanel |
| Text | `'text'` | TextEditor |
| Relations | `'relations'` | RelationPanel |

---

## Canvas Components (`src/lib/components/canvas/`)

3-layer hybrid rendering architecture:

```text
Layer 1 (z-index: 0)  — Background: PDF.js <canvas> or <img> fallback
Layer 2 (z-index: 10) — Konva.js: image block bbox + selected element bbox
Layer 3 (z-index: 20) — DOM TextOverlay: selectable text at text block positions (image fallback mode only)
```

### HybridViewer

3-layer hybrid viewer container. Manages Konva Stage + PDF.js/image background + TextOverlay integration.

| Prop | Type | Description |
| ------ | ------ | ------ |
| `pageProxy` | `PDFPageProxy?` | PDF.js page (vector rendering when available) |
| `imageUrl` | `string?` | Image URL (PDF.js fallback) |
| `width` | `number` | Image width (px) |
| `height` | `number` | Image height (px) |

Internal state machine:

- `interactionMode`: `'browse'` (default) -> `'edit'` (when an element is selected)
- browse mode: text selectable, bboxes shown only on hover
- edit mode: bbox editing enabled, text overlay disabled

### PdfRenderer

Renders PDF.js `PDFPageProxy` as vector to `<canvas>`.
High-resolution rendering at `PDF_BASE_SCALE`(2.0) then displayed via CSS transform.

| Prop | Type | Description |
| ------ | ------ | ------ |
| `pageProxy` | `PDFPageProxy` | PDF.js page proxy |

### BboxLayer

Syncs `annotationStore.elements` as Konva Rects.

| Prop | Type | Description |
| ------ | ------ | ------ |
| `stage` | `Konva.Stage` | Konva stage |
| `filter` | `(el: LayoutElement) => boolean` | Render filter (optional) |
| `interactionMode` | `'browse' \| 'edit'` | Interaction mode (optional) |

Behavior:

- Renders each element with category-specific colors
- Non-selected elements are transparent in browse mode (semi-transparent on hover)
- Shows Konva Transformer (resize handles) for selected elements
- Calls `annotationStore.updateElement()` on drag/resize completion
- Deselects on empty area click
- Renders image blocks + currently selected element (text blocks are handled by TextOverlay)

### BboxDrawTool

Draws new bboxes via mouse drag in `draw` mode.

- mousedown -> mousemove -> mouseup creates a rectangle
- Drags under 5px are ignored (prevents accidental clicks)
- Automatically switches to `select` mode after creation
- Default category: `text_block`

### TextOverlay

Renders text block elements as DOM overlay. Only active in image fallback mode (PDF.js mode uses PDF's own text layer).

- Supports text selection/copy
- Calls `annotationStore.selectElement()` on element click
- Active/inactive based on interaction mode via `pointerEvents` prop

### ReadingOrderOverlay

Displays reading order number badges on the canvas. Only rendered when `canvasStore.showReadingOrder` is `true`.

- Shows 24x24 circular badges at the top-left of each element's bbox
- Badge background: category-specific color via `getCategoryColor()`
- Badge text: `el.order` (0-based index)
- Toggle via `O` shortcut or checkbox

### RelationOverlay

Visualizes relations between elements as SVG arrows.

| Prop | Type | Default | Description |
| ------ | ------ | --------- | ------ |
| `visible` | `boolean` | `true` | Overlay visibility |

- Color-coded by relation type:
  - `parent_son` (#6366f1), `figure_caption` (#22c55e)
  - `table_caption` (#f59e0b), `table_footnote` (#ef4444)
  - `equation_caption` (#a855f7), `code_caption` (#06b6d4)
- Dashed (6 3) stroke, arrow markers
- opacity 0.7, stroke-width 2
- Lines connecting element center points

---

## Panel Components (`src/lib/components/panels/`)

### ElementList

Element list panel. Displayed in the left sidebar.

- Category color indicators
- Korean category labels
- Click to select an element
- Delete (X) button + drag handle (6-dot) on hover
- HTML5 drag-and-drop for reading order reordering
- Semi-transparent effect during drag + top border visual feedback on drop target
- Calls `reorderElements()` + `updateReadingOrder()` API on order change

### CategorySelect

Block category dropdown (18 items, Korean labels).

| Prop | Type | Description |
| ------ | ------ | ------ |
| `value` | `BlockCategoryType` | Current category |
| `onchange` | `(category: BlockCategoryType) => void` | Change handler |

### AttributePanel

Panel for editing the selected element's attributes.

- Category selection (CategorySelect)
- Ignore toggle
- Dynamic attribute form per category (based on CATEGORY_ATTRIBUTES mapping)

### PageAttributePanel

Page-level attribute editing.

- Data source (11 items)
- Language (4 items)
- Layout (5 items)
- Watermark/fuzzy scan/colorful background toggles

### PageNavigator

Compact navigator for navigating between pages in multi-page documents.

| Prop | Type | Description |
| ------ | ------ | ------ |
| `pages` | `readonly PageSummary[]` | Page list |
| `currentPageId` | `string` | Current page ID |

- Previous/next page navigation with left/right arrows
- Current position display (N / M)
- Page status badges (pending/in progress/submitted/reviewed)
- Semantic theme tokens (dark mode compatible)

### ExtractionPreview

Auto-extraction result preview banner. Displayed on the left side of LabelingPage.

4 states:

1. **Extracting** (`documentStatus === 'extracting'`): Spinner + "OCR extraction in progress..." message
2. **No results** (no auto_extracted_data and annotation is empty): "No auto-extraction results" + link to OCR settings
3. **Awaiting acceptance** (auto_extracted_data exists and annotation is empty):
   Element count display + accept/dismiss buttons (blue theme)
4. **Awaiting force acceptance** (auto_extracted_data exists and annotation has content):
   Element count display + "Accepting will replace existing annotations" warning
   \+ accept/dismiss buttons (violet theme)

- Displays extracted element count (N text, N images -- N total elements)
- "Accept" button -> calls `acceptExtraction()` or `forceAcceptExtraction()` API -> updates annotations
- "Dismiss" button -> closes the banner (`dismissed` state within session)
- Also closable via X button
- "Full re-scan" button -> re-extracts entire document with current OCR engine (`reExtractDocument()`)

| Prop | Type | Description |
| ------ | ------ | ------ |
| `pageId` | `string` | Page UUID |
| `autoExtractedData` | `AnnotationData \| null` | Auto-extracted data |
| `annotationData` | `AnnotationData \| null` | Current annotation data |
| `documentId` | `string` | Document UUID (for re-extraction) |
| `documentStatus` | `DocumentStatus?` | Document processing status |
| `onAccepted` | `(data: AnnotationData) => void` | Callback after acceptance |
| `onReExtract` | `() => void` | Re-scan request callback |

### TextEditor

Text editing for the selected element (Text / LaTeX / HTML tabs).

- Tab switching to edit `text`, `latex`, `html` fields
- Monospace font textarea

### RelationPanel

Panel for managing relations of the selected element. Displayed in the "Relations" sidebar tab.

- Displays selected element's ID and category info
- Connected relation list (incoming: <-, outgoing: ->)
- Add relation: target element selection + relation type dropdown (6 types)
- Delete button on hover
- API integration: calls `createRelation()` / `deleteRelation()`

---

## Settings Components (`src/lib/components/settings/`)

### OcrSettingsPanel

OCR engine multi-instance management panel.

| Prop | Type | Default | Description |
| ------ | ------ | --------- | ------ |
| `config` | `OcrConfigResponse` | - | Current OCR config (multi-instance) |
| `connectionStatuses` | `Record<string, OcrConnectionTestResponse \| null>` | `{}` | Per-engine connection status |
| `testingEngines` | `Set<string>` | `new Set()` | Set of engine IDs currently being tested |
| `onadd` | `(data: EngineInstanceCreate) => void` | - | Engine add handler |
| `onupdate` | `(engineId, data) => void` | - | Engine update handler |
| `ondelete` | `(engineId) => void` | - | Engine delete handler |
| `onsetdefault` | `(engineId) => void` | - | Default engine set handler |
| `ontest` | `(engineId) => void` | - | Connection test handler |

Sub-components:

- `EngineCard`: Individual engine instance card (name, status icon, edit form, delete)
- `EngineAddDialog`: Engine add dialog (type selection -> config input)
