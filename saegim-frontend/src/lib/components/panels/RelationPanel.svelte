<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import { getCategoryColor } from '$lib/utils/color'
  import type { BlockCategoryType } from '$lib/types/categories'
  import type { Relation } from '$lib/types/omnidocbench'

  const RELATION_TYPES = [
    { value: 'parent_son', label: '부모-자식' },
    { value: 'figure_caption', label: 'Figure ↔ Caption' },
    { value: 'table_caption', label: 'Table ↔ Caption' },
    { value: 'table_footnote', label: 'Table ↔ Footnote' },
    { value: 'equation_caption', label: 'Equation ↔ Caption' },
    { value: 'code_caption', label: 'Code ↔ Caption' },
  ] as const

  let selectedElement = $derived(annotationStore.selectedElement)
  let elementRelations = $derived(
    selectedElement ? annotationStore.getRelationsForElement(selectedElement.anno_id) : [],
  )

  /** State for the "add relation" flow */
  let isSelectingTarget = $state(false)
  let selectedRelationType = $state('parent_son')

  function getElementLabel(annoId: number): string {
    const el = annotationStore.elements.find((e) => e.anno_id === annoId)
    if (!el) return `#${annoId} (삭제됨)`
    const text = el.text ? ` "${el.text.slice(0, 20)}${el.text.length > 20 ? '...' : ''}"` : ''
    return `#${annoId} ${el.category_type}${text}`
  }

  function getElementCategoryType(annoId: number): BlockCategoryType | null {
    const el = annotationStore.elements.find((e) => e.anno_id === annoId)
    return el ? (el.category_type as BlockCategoryType) : null
  }

  function startSelectTarget(): void {
    isSelectingTarget = true
  }

  function cancelSelectTarget(): void {
    isSelectingTarget = false
  }

  function selectTarget(targetAnnoId: number): void {
    if (!selectedElement) return
    if (targetAnnoId === selectedElement.anno_id) return

    annotationStore.addRelation(selectedElement.anno_id, targetAnnoId, selectedRelationType)
    isSelectingTarget = false
    uiStore.showNotification('관계가 추가되었습니다', 'success')
  }

  function handleRemoveRelation(relation: Relation): void {
    annotationStore.removeRelation(relation.source_anno_id, relation.target_anno_id)
    uiStore.showNotification('관계가 삭제되었습니다', 'success')
  }

  function getRelationTypeLabel(type: string): string {
    const found = RELATION_TYPES.find((t) => t.value === type)
    return found ? found.label : type
  }

  function getRelationDirection(
    relation: Relation,
    currentAnnoId: number,
  ): 'outgoing' | 'incoming' {
    return relation.source_anno_id === currentAnnoId ? 'outgoing' : 'incoming'
  }

  /** Elements available as targets (exclude current selection) */
  let targetCandidates = $derived(
    annotationStore.elements.filter((el) => el.anno_id !== selectedElement?.anno_id),
  )
</script>

{#if selectedElement}
  <div class="space-y-3 p-3">
    <h3 class="text-foreground text-sm font-semibold">관계 편집</h3>

    <!-- Current element info -->
    <div class="bg-muted rounded-md px-2.5 py-1.5 text-xs">
      <span class="text-muted-foreground">선택된 요소:</span>
      <span class="text-foreground font-medium">
        #{selectedElement.anno_id} {selectedElement.category_type}
      </span>
    </div>

    <!-- Existing relations -->
    {#if elementRelations.length > 0}
      <div class="space-y-1">
        <p class="text-muted-foreground text-xs font-medium">연결된 관계 ({elementRelations.length})</p>
        {#each elementRelations as relation}
          {@const direction = getRelationDirection(relation, selectedElement.anno_id)}
          {@const otherAnnoId = direction === 'outgoing' ? relation.target_anno_id : relation.source_anno_id}
          {@const otherCategory = getElementCategoryType(otherAnnoId)}
          <div
            class="border-border bg-background group flex items-center gap-2 rounded-md border px-2 py-1.5"
          >
            {#if otherCategory}
              <span
                class="h-2.5 w-2.5 shrink-0 rounded-sm"
                style="background-color: {getCategoryColor(otherCategory)}"
              ></span>
            {/if}
            <div class="min-w-0 flex-1 text-xs">
              <span class="text-muted-foreground">
                {direction === 'outgoing' ? '→' : '←'}
              </span>
              <button
                class="text-foreground hover:text-primary truncate hover:underline"
                onclick={() => annotationStore.selectElement(otherAnnoId)}
              >
                {getElementLabel(otherAnnoId)}
              </button>
              <span class="bg-muted text-muted-foreground ml-1 rounded px-1 py-0.5 text-[10px]">
                {getRelationTypeLabel(relation.relation_type)}
              </span>
            </div>
            <button
              class="text-muted-foreground hover:text-destructive shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
              onclick={() => handleRemoveRelation(relation)}
              aria-label="관계 삭제"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        {/each}
      </div>
    {:else}
      <p class="text-muted-foreground text-xs">이 요소에 연결된 관계가 없습니다.</p>
    {/if}

    <!-- Add relation -->
    {#if isSelectingTarget}
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <p class="text-foreground text-xs font-medium">대상 요소 선택</p>
          <button
            class="text-muted-foreground hover:text-foreground text-xs"
            onclick={cancelSelectTarget}
          >
            취소
          </button>
        </div>

        <!-- Relation type selector -->
        <select
          class="border-input bg-background text-foreground focus:border-ring w-full rounded-md border px-2 py-1.5 text-xs"
          bind:value={selectedRelationType}
        >
          {#each RELATION_TYPES as type}
            <option value={type.value}>{type.label}</option>
          {/each}
        </select>

        <!-- Target element list -->
        <div class="max-h-48 space-y-0.5 overflow-y-auto">
          {#each targetCandidates as candidate (candidate.anno_id)}
            <button
              class="border-border hover:bg-accent flex w-full items-center gap-2 rounded-md border px-2 py-1.5 text-left text-xs transition-colors"
              onclick={() => selectTarget(candidate.anno_id)}
            >
              <span
                class="h-2.5 w-2.5 shrink-0 rounded-sm"
                style="background-color: {getCategoryColor(candidate.category_type as BlockCategoryType)}"
              ></span>
              <span class="text-foreground truncate">
                #{candidate.anno_id} {candidate.category_type}
                {#if candidate.text}
                  <span class="text-muted-foreground">
                    "{candidate.text.slice(0, 15)}{candidate.text.length > 15 ? '...' : ''}"
                  </span>
                {/if}
              </span>
            </button>
          {/each}
        </div>
      </div>
    {:else}
      <button
        class="bg-primary text-primary-foreground hover:bg-primary/90 w-full rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
        onclick={startSelectTarget}
      >
        + 관계 추가
      </button>
    {/if}
  </div>
{:else}
  <div class="p-3 text-center">
    <p class="text-muted-foreground py-8 text-sm">요소를 선택하면 관계를 편집할 수 있습니다.</p>
  </div>
{/if}
