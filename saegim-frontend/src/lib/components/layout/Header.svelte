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

  let { title = 'saegim', showSave = false, onsave, saving = false }: Props = $props()
</script>

<header class="flex h-12 shrink-0 items-center bg-zinc-900 px-4 shadow-sm dark:bg-zinc-950">
  <div class="flex items-center gap-4">
    <a href="/" class="text-base font-bold text-white transition-colors hover:text-violet-300">
      {title}
    </a>
  </div>

  <div class="flex-1"></div>

  <div class="flex items-center gap-3">
    {#if annotationStore.isDirty}
      <span
        class="inline-flex items-center rounded-full border border-amber-500/30 bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-300"
      >
        저장되지 않은 변경
      </span>
    {/if}

    {#if showSave}
      <button
        class="rounded-lg px-3 py-1.5 text-sm font-medium transition-all
          {saving || !annotationStore.isDirty
          ? 'cursor-not-allowed bg-white/10 text-white/40'
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
      class="fixed top-4 right-4 z-50 rounded-xl border px-4 py-3 text-sm shadow-lg
        {uiStore.notification.type === 'error'
        ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/50 dark:text-red-200'
        : uiStore.notification.type === 'success'
          ? 'border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950/50 dark:text-green-200'
          : 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-950/50 dark:text-blue-200'}"
    >
      {uiStore.notification.message}
    </div>
  {/if}
</header>
