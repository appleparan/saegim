<script lang="ts">
  interface Props {
    label?: string
    checked: boolean
    disabled?: boolean
    onchange?: (checked: boolean) => void
  }

  let {
    label,
    checked,
    disabled = false,
    onchange,
  }: Props = $props()

  function handleChange() {
    onchange?.(!checked)
  }
</script>

<div class="flex items-center gap-2">
  <button
    type="button"
    role="switch"
    aria-checked={checked}
    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed {checked ? 'bg-blue-600' : 'bg-gray-200'}"
    {disabled}
    onclick={handleChange}
  >
    <span
      class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {checked ? 'translate-x-4' : 'translate-x-0'}"
    ></span>
  </button>
  {#if label}
    <span class="text-sm text-gray-700">{label}</span>
  {/if}
</div>
