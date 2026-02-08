<script lang="ts">
  import { BLOCK_CATEGORIES, CATEGORY_LABELS } from '$lib/types/categories'
  import type { BlockCategoryType } from '$lib/types/categories'
  import { getCategoryColor } from '$lib/utils/color'

  interface Props {
    value: BlockCategoryType
    onchange: (category: BlockCategoryType) => void
  }

  let { value, onchange }: Props = $props()
</script>

<div>
  <label class="block text-xs font-medium text-gray-500 mb-1" for="category-select">카테고리</label>
  <select
    id="category-select"
    class="block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
    value={value}
    onchange={(e) => onchange((e.target as HTMLSelectElement).value as BlockCategoryType)}
  >
    {#each BLOCK_CATEGORIES as cat}
      <option value={cat}>
        {CATEGORY_LABELS[cat]}
      </option>
    {/each}
  </select>
</div>
