<script lang="ts">
  interface Props {
    label?: string
    value: string
    options: readonly string[]
    labels?: Readonly<Record<string, string>>
    disabled?: boolean
    onchange?: (value: string) => void
  }

  let {
    label,
    value,
    options,
    labels,
    disabled = false,
    onchange,
  }: Props = $props()

  function handleChange(e: Event) {
    const target = e.target as HTMLSelectElement
    onchange?.(target.value)
  }
</script>

<div class="flex flex-col gap-1">
  {#if label}
    <label class="text-xs font-medium text-gray-600">{label}</label>
  {/if}
  <select
    class="block w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
    {value}
    {disabled}
    onchange={handleChange}
  >
    <option value="">-- 선택 --</option>
    {#each options as opt}
      <option value={opt}>{labels?.[opt] ?? opt}</option>
    {/each}
  </select>
</div>
