<script lang="ts">
  import { link } from 'svelte-spa-router'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'

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

<header class="h-12 bg-linear-to-r from-slate-900 to-slate-800 flex items-center px-4 shrink-0 shadow-sm">
  <div class="flex items-center gap-4">
    <a href="/" use:link class="text-base font-bold text-white hover:text-primary-300 transition-colors">
      {title}
    </a>
  </div>

  <div class="flex-1"></div>

  <div class="flex items-center gap-3">
    {#if annotationStore.isDirty}
      <span class="badge bg-amber-500/20 text-amber-300 border border-amber-500/30">
        저장되지 않은 변경
      </span>
    {/if}

    {#if showSave}
      <button
        class="px-3 py-1.5 text-sm font-medium rounded-lg transition-all
          {saving || !annotationStore.isDirty
            ? 'bg-white/10 text-white/40 cursor-not-allowed'
            : 'bg-primary-500 text-white hover:bg-primary-400 active:bg-primary-600 shadow-sm'}"
        disabled={saving || !annotationStore.isDirty}
        onclick={onsave}
      >
        {saving ? '저장 중...' : '저장'}
      </button>
    {/if}
  </div>

  {#if uiStore.notification}
    <div
      class="fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm border
        {uiStore.notification.type === 'error'
          ? 'bg-red-50 text-red-800 border-red-200'
          : uiStore.notification.type === 'success'
            ? 'bg-green-50 text-green-800 border-green-200'
            : 'bg-blue-50 text-blue-800 border-blue-200'}"
    >
      {uiStore.notification.message}
    </div>
  {/if}
</header>
