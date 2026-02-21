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

<div class="p-3 border-b border-border flex items-center justify-between bg-muted">
  <div>
    <h3 class="text-sm font-semibold text-foreground">요소 목록</h3>
    <p class="text-xs text-muted-foreground mt-0.5">
      {annotationStore.elements.length}개 요소
    </p>
  </div>
</div>

<div class="p-1.5 overflow-y-auto flex-1">
  {#each annotationStore.elements as element}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="w-full text-left px-2.5 py-2 rounded-lg text-sm transition-all flex items-center gap-2.5 group cursor-pointer mb-0.5
        {annotationStore.selectedElementId === element.anno_id
          ? 'bg-primary/10 text-primary shadow-sm border border-primary/30'
          : 'hover:bg-accent text-foreground border border-transparent'}"
      onclick={() => annotationStore.selectElement(element.anno_id)}
    >
      <span
        class="w-3 h-3 rounded-sm shrink-0 shadow-sm"
        style="background-color: {getCategoryColor(element.category_type)}"
      ></span>
      <span class="flex-1 truncate">
        <span class="font-medium text-muted-foreground mr-0.5">{element.order}.</span>
        {getLabel(element.category_type)}
        {#if element.ignore}
          <span class="text-xs text-muted-foreground italic">(무시)</span>
        {/if}
      </span>
      <button
        class="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive px-1 transition-all"
        onclick={(e) => handleDelete(e, element.anno_id)}
        aria-label="삭제"
      >
        &times;
      </button>
    </div>
  {/each}
  {#if annotationStore.elements.length === 0}
    <p class="text-xs text-muted-foreground text-center py-8">
      요소가 없습니다.<br/>그리기 도구로 추가하세요.
    </p>
  {/if}
</div>
