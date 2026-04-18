<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import { getCategoryColor } from '$lib/utils/color'
  import { CATEGORY_LABELS } from '$lib/types/categories'
  import type { BlockCategoryType } from '$lib/types/categories'
  import { updateReadingOrder } from '$lib/api/pages'

  let sortedElements = $derived(
    [...annotationStore.elements].sort((a, b) => a.order - b.order),
  )
  let selectedCount = $derived(annotationStore.selectedCount)

  let draggedAnnoId = $state<number | null>(null)
  let dragOverAnnoId = $state<number | null>(null)

  function handleDelete(e: MouseEvent, annoId: number) {
    e.stopPropagation()
    annotationStore.removeElement(annoId)
  }

  function getLabel(category: BlockCategoryType): string {
    return CATEGORY_LABELS[category] ?? category
  }

  function getOrderMapFromStore(): Record<number, number> {
    const sorted = [...annotationStore.elements].sort((a, b) => a.order - b.order)
    const orderMap: Record<number, number> = {}
    for (let i = 0; i < sorted.length; i++) {
      orderMap[sorted[i].anno_id] = i
    }
    return orderMap
  }

  async function persistReadingOrder(orderMap: Record<number, number>): Promise<void> {
    const pageId = annotationStore.pageId
    if (!pageId) return

    try {
      const apiOrderMap: Record<string, number> = {}
      for (const [k, v] of Object.entries(orderMap)) {
        apiOrderMap[String(k)] = v
      }
      await updateReadingOrder(pageId, apiOrderMap)
      annotationStore.markSaved()
    } catch {
      uiStore.showNotification('Failed to save order', 'error')
    }
  }

  function handleSelect(e: MouseEvent, annoId: number): void {
    const isAdditive = e.metaKey || e.ctrlKey
    if (e.shiftKey) {
      annotationStore.selectRangeToElement(annoId, isAdditive)
      return
    }
    if (isAdditive) {
      annotationStore.toggleElementSelection(annoId)
      return
    }
    annotationStore.selectElement(annoId)
  }

  async function handleMoveSelected(delta: -1 | 1): Promise<void> {
    annotationStore.moveSelectedElements(delta)
    await persistReadingOrder(getOrderMapFromStore())
  }

  function handleDeleteSelected(): void {
    annotationStore.removeSelectedElements()
  }

  function handleDragStart(e: DragEvent, annoId: number): void {
    draggedAnnoId = annoId
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/plain', String(annoId))
    }
  }

  function handleDragOver(e: DragEvent, annoId: number): void {
    e.preventDefault()
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'move'
    }
    dragOverAnnoId = annoId
  }

  function handleDragLeave(): void {
    dragOverAnnoId = null
  }

  function handleDragEnd(): void {
    draggedAnnoId = null
    dragOverAnnoId = null
  }

  async function handleDrop(e: DragEvent, targetAnnoId: number): Promise<void> {
    e.preventDefault()
    dragOverAnnoId = null

    if (draggedAnnoId === null || draggedAnnoId === targetAnnoId) {
      draggedAnnoId = null
      return
    }

    const currentSorted = [...annotationStore.elements].sort((a, b) => a.order - b.order)
    const fromIdx = currentSorted.findIndex((el) => el.anno_id === draggedAnnoId)
    const toIdx = currentSorted.findIndex((el) => el.anno_id === targetAnnoId)

    if (fromIdx < 0 || toIdx < 0) {
      draggedAnnoId = null
      return
    }

    const reordered = [...currentSorted]
    const [moved] = reordered.splice(fromIdx, 1)
    reordered.splice(toIdx, 0, moved)

    const orderMap: Record<number, number> = {}
    for (let i = 0; i < reordered.length; i++) {
      orderMap[reordered[i].anno_id] = i
    }

    annotationStore.reorderElements(orderMap)
    draggedAnnoId = null
    await persistReadingOrder(orderMap)
  }
</script>

<div class="border-border bg-muted flex items-center justify-between border-b p-3">
  <div>
    <h3 class="text-foreground text-sm font-semibold">Element List</h3>
    <p class="text-muted-foreground mt-0.5 text-xs">
      {annotationStore.elements.length} elements
    </p>
  </div>
  <div class="flex items-center gap-3">
    <label class="flex cursor-pointer items-center gap-1.5" title="Show Elements (I)">
      <input
        type="checkbox"
        class="accent-primary h-3.5 w-3.5 rounded"
        checked={canvasStore.showElementIndex}
        onchange={() => canvasStore.toggleElementIndex()}
      />
      <span class="text-muted-foreground text-xs">Element</span>
    </label>
    <label class="flex cursor-pointer items-center gap-1.5" title="Show Order (R)">
      <input
        type="checkbox"
        class="accent-primary h-3.5 w-3.5 rounded"
        checked={canvasStore.showReadingOrder}
        onchange={() => canvasStore.toggleReadingOrder()}
      />
      <span class="text-muted-foreground text-xs">Order</span>
    </label>
  </div>
</div>

{#if selectedCount > 0}
  <div class="border-border bg-card flex items-center gap-1.5 border-b px-2 py-2">
    <span class="text-foreground mr-1 text-xs font-medium">{selectedCount} selected</span>
    <button
      type="button"
      class="text-muted-foreground hover:bg-accent hover:text-foreground rounded px-1.5 py-1 text-xs"
      onclick={() => handleMoveSelected(-1)}
      title="Move selected element up"
      aria-label="Move selected element up"
    >
      ↑
    </button>
    <button
      type="button"
      class="text-muted-foreground hover:bg-accent hover:text-foreground rounded px-1.5 py-1 text-xs"
      onclick={() => handleMoveSelected(1)}
      title="Move selected element down"
      aria-label="Move selected element down"
    >
      ↓
    </button>
    <button
      type="button"
      class="text-destructive/80 hover:bg-destructive/10 rounded px-1.5 py-1 text-xs"
      onclick={handleDeleteSelected}
      title="Delete selected elements"
      aria-label="Delete selected elements"
    >
      Delete
    </button>
    <button
      type="button"
      class="text-muted-foreground hover:bg-accent hover:text-foreground ml-auto rounded px-1.5 py-1 text-xs"
      onclick={() => annotationStore.clearSelection()}
      title="Clear Selection"
      aria-label="Clear Selection"
    >
      Clear
    </button>
  </div>
{/if}

<div class="flex-1 overflow-y-auto p-1.5">
  {#each sortedElements as element (element.anno_id)}
    {@const isSelected = annotationStore.isElementSelected(element.anno_id)}
    {@const isPrimary = annotationStore.selectedElementId === element.anno_id}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="group mb-0.5 flex w-full cursor-pointer items-center gap-1.5 rounded-lg px-2.5 py-2 text-left text-sm transition-all
        {isPrimary
        ? 'bg-primary/10 text-primary border-primary/30 border shadow-sm'
        : isSelected
          ? 'bg-primary/5 text-foreground border-primary/20 border'
        : 'hover:bg-accent text-foreground border border-transparent'}
        {draggedAnnoId === element.anno_id ? 'opacity-50' : ''}
        {dragOverAnnoId === element.anno_id && draggedAnnoId !== element.anno_id
        ? 'border-t-primary border-t-2' : ''}"
      draggable="true"
      ondragstart={(e) => handleDragStart(e, element.anno_id)}
      ondragover={(e) => handleDragOver(e, element.anno_id)}
      ondragleave={handleDragLeave}
      ondragend={handleDragEnd}
      ondrop={(e) => handleDrop(e, element.anno_id)}
      onclick={(e) => handleSelect(e, element.anno_id)}
    >
      <!-- Drag handle -->
      <span class="text-muted-foreground flex shrink-0 cursor-grab opacity-0 group-hover:opacity-60">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="9" cy="6" r="1.5" />
          <circle cx="15" cy="6" r="1.5" />
          <circle cx="9" cy="12" r="1.5" />
          <circle cx="15" cy="12" r="1.5" />
          <circle cx="9" cy="18" r="1.5" />
          <circle cx="15" cy="18" r="1.5" />
        </svg>
      </span>
      <span
        class="h-3 w-3 shrink-0 rounded-sm shadow-sm"
        style="background-color: {getCategoryColor(element.category_type)}"
      ></span>
      <span class="flex-1 truncate">
        <span class="text-muted-foreground mr-0.5 font-medium">{element.order}.</span>
        {getLabel(element.category_type)}
        {#if element.ignore}
          <span class="text-muted-foreground text-xs italic">(Ignore)</span>
        {/if}
      </span>
      <button
        class="text-muted-foreground hover:text-destructive px-1 opacity-0 transition-all group-hover:opacity-100"
        onclick={(e) => handleDelete(e, element.anno_id)}
        aria-label="Delete"
      >
        &times;
      </button>
    </div>
  {/each}
  {#if annotationStore.elements.length === 0}
    <p class="text-muted-foreground py-8 text-center text-xs">
      No elements yet.<br />Add one with the draw tool.
    </p>
  {/if}
</div>
