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

  let draggedAnnoId = $state<number | null>(null)
  let dragOverAnnoId = $state<number | null>(null)

  function handleDelete(e: MouseEvent, annoId: number) {
    e.stopPropagation()
    annotationStore.removeElement(annoId)
  }

  function getLabel(category: BlockCategoryType): string {
    return CATEGORY_LABELS[category] ?? category
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

    const pageId = annotationStore.pageId
    if (pageId) {
      try {
        const apiOrderMap: Record<string, number> = {}
        for (const [k, v] of Object.entries(orderMap)) {
          apiOrderMap[String(k)] = v
        }
        await updateReadingOrder(pageId, apiOrderMap)
        annotationStore.markSaved()
      } catch {
        uiStore.showNotification('순서 저장에 실패했습니다', 'error')
      }
    }
  }
</script>

<div class="border-border bg-muted flex items-center justify-between border-b p-3">
  <div>
    <h3 class="text-foreground text-sm font-semibold">요소 목록</h3>
    <p class="text-muted-foreground mt-0.5 text-xs">
      {annotationStore.elements.length}개 요소
    </p>
  </div>
  <label class="flex cursor-pointer items-center gap-1.5" title="순서 표시 (O)">
    <input
      type="checkbox"
      class="accent-primary h-3.5 w-3.5 rounded"
      checked={canvasStore.showReadingOrder}
      onchange={() => canvasStore.toggleReadingOrder()}
    />
    <span class="text-muted-foreground text-xs">순서</span>
  </label>
</div>

<div class="flex-1 overflow-y-auto p-1.5">
  {#each sortedElements as element (element.anno_id)}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="group mb-0.5 flex w-full cursor-pointer items-center gap-1.5 rounded-lg px-2.5 py-2 text-left text-sm transition-all
        {annotationStore.selectedElementId === element.anno_id
        ? 'bg-primary/10 text-primary border-primary/30 border shadow-sm'
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
      onclick={() => annotationStore.selectElement(element.anno_id)}
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
          <span class="text-muted-foreground text-xs italic">(무시)</span>
        {/if}
      </span>
      <button
        class="text-muted-foreground hover:text-destructive px-1 opacity-0 transition-all group-hover:opacity-100"
        onclick={(e) => handleDelete(e, element.anno_id)}
        aria-label="삭제"
      >
        &times;
      </button>
    </div>
  {/each}
  {#if annotationStore.elements.length === 0}
    <p class="text-muted-foreground py-8 text-center text-xs">
      요소가 없습니다.<br />그리기 도구로 추가하세요.
    </p>
  {/if}
</div>
