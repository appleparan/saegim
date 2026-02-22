<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { getCategoryColor } from '$lib/utils/color'
  import { CATEGORY_LABELS } from '$lib/types/categories'
  import type { BlockCategoryType } from '$lib/types/categories'
  function handleDelete(e: MouseEvent, annoId: number) {
    e.stopPropagation()
    annotationStore.removeElement(annoId)
  }

  function getLabel(category: BlockCategoryType): string {
    return CATEGORY_LABELS[category] ?? category
  }
</script>

<div class="border-border bg-muted flex items-center justify-between border-b p-3">
  <div>
    <h3 class="text-foreground text-sm font-semibold">요소 목록</h3>
    <p class="text-muted-foreground mt-0.5 text-xs">
      {annotationStore.elements.length}개 요소
    </p>
  </div>
</div>

<div class="flex-1 overflow-y-auto p-1.5">
  {#each annotationStore.elements as element}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="group mb-0.5 flex w-full cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm transition-all
        {annotationStore.selectedElementId === element.anno_id
        ? 'bg-primary/10 text-primary border-primary/30 border shadow-sm'
        : 'hover:bg-accent text-foreground border border-transparent'}"
      onclick={() => annotationStore.selectElement(element.anno_id)}
    >
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
