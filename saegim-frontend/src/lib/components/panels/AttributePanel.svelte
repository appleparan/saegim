<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { CATEGORY_ATTRIBUTES, CATEGORY_LABELS } from '$lib/types/categories'
  import type { BlockCategoryType } from '$lib/types/categories'
  import CategorySelect from './CategorySelect.svelte'
  import Select from '$lib/components/common/Select.svelte'
  import Toggle from '$lib/components/common/Toggle.svelte'

  let element = $derived(annotationStore.selectedElement)
  let fields = $derived(
    element ? CATEGORY_ATTRIBUTES[element.category_type] ?? [] : [],
  )

  function handleCategoryChange(category: BlockCategoryType) {
    if (!element) return
    annotationStore.updateElement(element.anno_id, { category_type: category })
  }

  function handleToggleIgnore() {
    if (!element) return
    annotationStore.updateElement(element.anno_id, { ignore: !element.ignore })
  }

  function handleAttributeChange(key: string, value: string | boolean) {
    if (!element) return
    annotationStore.updateElementAttribute(element.anno_id, key, value)
  }
</script>

{#if element}
  <div class="p-3 space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-gray-700">
        요소 #{element.anno_id}
      </h3>
      <span class="text-xs text-gray-400">순서: {element.order}</span>
    </div>

    <CategorySelect
      value={element.category_type}
      onchange={handleCategoryChange}
    />

    <Toggle
      label="무시 처리"
      checked={element.ignore}
      onchange={handleToggleIgnore}
    />

    {#if fields.length > 0}
      <div class="border-t border-gray-100 pt-3 space-y-3">
        <h4 class="text-xs font-medium text-gray-500 uppercase">속성</h4>
        {#each fields as field}
          {#if field.type === 'select' && field.options}
            <Select
              label={field.label}
              value={(element.attribute?.[field.key] as string) ?? ''}
              options={field.options}
              onchange={(v) => handleAttributeChange(field.key, v)}
            />
          {:else if field.type === 'toggle'}
            <Toggle
              label={field.label}
              checked={!!element.attribute?.[field.key]}
              onchange={() =>
                handleAttributeChange(
                  field.key,
                  !element!.attribute?.[field.key],
                )}
            />
          {/if}
        {/each}
      </div>
    {/if}
  </div>
{:else}
  <div class="p-3 text-center">
    <p class="text-sm text-gray-400 py-8">요소를 선택하세요.</p>
  </div>
{/if}
