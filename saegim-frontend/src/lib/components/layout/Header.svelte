<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import ThemeToggle from './ThemeToggle.svelte'

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

<header class="h-12 bg-zinc-900 dark:bg-zinc-950 flex items-center px-4 shrink-0 shadow-sm">
  <div class="flex items-center gap-4">
    <a href="/" class="text-base font-bold text-white hover:text-violet-300 transition-colors">
      {title}
    </a>
  </div>

  <div class="flex-1"></div>

  <div class="flex items-center gap-3">
    {#if annotationStore.isDirty}
      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30">
        저장되지 않은 변경
      </span>
    {/if}

    {#if showSave}
      <button
        class="px-3 py-1.5 text-sm font-medium rounded-lg transition-all
          {saving || !annotationStore.isDirty
            ? 'bg-white/10 text-white/40 cursor-not-allowed'
            : 'bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/80 shadow-sm'}"
        disabled={saving || !annotationStore.isDirty}
        onclick={onsave}
      >
        {saving ? '저장 중...' : '저장'}
      </button>
    {/if}

    <ThemeToggle />
  </div>

  {#if uiStore.notification}
    <div
      class="fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm border
        {uiStore.notification.type === 'error'
          ? 'bg-red-50 dark:bg-red-950/50 text-red-800 dark:text-red-200 border-red-200 dark:border-red-800'
          : uiStore.notification.type === 'success'
            ? 'bg-green-50 dark:bg-green-950/50 text-green-800 dark:text-green-200 border-green-200 dark:border-green-800'
            : 'bg-blue-50 dark:bg-blue-950/50 text-blue-800 dark:text-blue-200 border-blue-200 dark:border-blue-800'}"
    >
      {uiStore.notification.message}
    </div>
  {/if}
</header>
