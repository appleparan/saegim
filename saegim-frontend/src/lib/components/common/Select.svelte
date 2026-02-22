<script lang="ts">
  interface Props {
    label?: string
    value: string
    options: readonly string[]
    labels?: Readonly<Record<string, string>>
    disabled?: boolean
    onchange?: (value: string) => void
  }

  let { label, value, options, labels, disabled = false, onchange }: Props = $props()

  const selectId = `select-${Math.random().toString(36).slice(2, 8)}`

  function handleChange(e: Event) {
    const target = e.target as HTMLSelectElement
    onchange?.(target.value)
  }
</script>

<div class="flex flex-col gap-1">
  {#if label}
    <label class="text-muted-foreground text-xs font-medium" for={selectId}>{label}</label>
  {/if}
  <select
    id={selectId}
    class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-2 py-1.5 text-sm focus:ring-1 disabled:opacity-50"
    {value}
    {disabled}
    onchange={handleChange}
  >
    <option value="">-- 선택 --</option>
    {#each options as opt (opt)}
      <option value={opt}>{labels?.[opt] ?? opt}</option>
    {/each}
  </select>
</div>
