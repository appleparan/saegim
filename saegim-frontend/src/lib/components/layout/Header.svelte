<script lang="ts">
  import { link } from 'svelte-spa-router'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import Button from '$lib/components/common/Button.svelte'

  interface Props {
    title?: string
    showSave?: boolean
    onsave?: () => void
    saving?: boolean
  }

  let {
    title = 'saegim',
    showSave = false,
    onsave,
    saving = false,
  }: Props = $props()
</script>

<header class="h-14 bg-white border-b border-gray-200 flex items-center px-4 shrink-0">
  <div class="flex items-center gap-4">
    <a href="/" use:link class="text-lg font-bold text-gray-900 hover:text-blue-600">
      {title}
    </a>
  </div>

  <div class="flex-1"></div>

  <div class="flex items-center gap-2">
    {#if annotationStore.isDirty}
      <span class="text-xs text-amber-600 font-medium">저장되지 않은 변경</span>
    {/if}

    {#if showSave}
      <Button
        variant="primary"
        size="sm"
        disabled={saving || !annotationStore.isDirty}
        onclick={onsave}
      >
        {saving ? '저장 중...' : '저장'}
      </Button>
    {/if}
  </div>

  {#if uiStore.notification}
    <div
      class="fixed top-4 right-4 z-50 px-4 py-2 rounded-md shadow-lg text-sm {uiStore.notification.type === 'error'
        ? 'bg-red-100 text-red-800'
        : uiStore.notification.type === 'success'
          ? 'bg-green-100 text-green-800'
          : 'bg-blue-100 text-blue-800'}"
    >
      {uiStore.notification.message}
    </div>
  {/if}
</header>
