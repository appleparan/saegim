<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { CATEGORY_ATTRIBUTES } from '$lib/types/categories'
  import type { BlockCategoryType } from '$lib/types/categories'
  import CategorySelect from './CategorySelect.svelte'
  import Select from '$lib/components/common/Select.svelte'
  import { Switch } from '$lib/components/ui/switch'
  import { Label } from '$lib/components/ui/label'

  let element = $derived(annotationStore.selectedElement)
  let fields = $derived(element ? (CATEGORY_ATTRIBUTES[element.category_type] ?? []) : [])

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
  <div class="space-y-4 p-3">
    <div class="flex items-center justify-between">
      <h3 class="text-foreground text-sm font-semibold">
        요소 #{element.anno_id}
      </h3>
      <span class="text-muted-foreground text-xs">순서: {element.order}</span>
    </div>

    <CategorySelect value={element.category_type} onchange={handleCategoryChange} />

    <div class="flex items-center gap-2">
      <Switch checked={element.ignore} onCheckedChange={handleToggleIgnore} />
      <Label class="text-sm">무시 처리</Label>
    </div>

    {#if fields.length > 0}
      <div class="border-border space-y-3 border-t pt-3">
        <h4 class="text-muted-foreground text-xs font-medium uppercase">속성</h4>
        {#each fields as field (field.key)}
          {#if field.type === 'select' && field.options}
            <Select
              label={field.label}
              value={(element.attribute?.[field.key] as string) ?? ''}
              options={field.options}
              onchange={(v) => handleAttributeChange(field.key, v)}
            />
          {:else if field.type === 'toggle'}
            <div class="flex items-center gap-2">
              <Switch
                checked={!!element.attribute?.[field.key]}
                onCheckedChange={() =>
                  handleAttributeChange(field.key, !element!.attribute?.[field.key])}
              />
              <Label class="text-sm">{field.label}</Label>
            </div>
          {/if}
        {/each}
      </div>
    {/if}
  </div>
{:else}
  <div class="p-3 text-center">
    <p class="text-muted-foreground py-8 text-sm">요소를 선택하세요.</p>
  </div>
{/if}
