<script lang="ts">
  import { BLOCK_CATEGORIES, CATEGORY_LABELS } from '$lib/types/categories'
  import type { BlockCategoryType } from '$lib/types/categories'

  interface Props {
    value: BlockCategoryType
    onchange: (category: BlockCategoryType) => void
  }

  let { value, onchange }: Props = $props()
</script>

<div>
  <label class="text-muted-foreground mb-1 block text-xs font-medium" for="category-select"
    >카테고리</label
  >
  <select
    id="category-select"
    class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-2 py-1.5 text-sm focus:ring-1"
    {value}
    onchange={(e) => onchange((e.target as HTMLSelectElement).value as BlockCategoryType)}
  >
    {#each BLOCK_CATEGORIES as cat (cat)}
      <option value={cat}>
        {CATEGORY_LABELS[cat]}
      </option>
    {/each}
  </select>
</div>
