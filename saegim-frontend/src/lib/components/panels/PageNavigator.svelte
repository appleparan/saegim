<script lang="ts">
  import { goto } from '$app/navigation'
  import type { PageSummary } from '$lib/api/types'

  interface Props {
    pages: readonly PageSummary[]
    currentPageId: string
  }

  let { pages, currentPageId }: Props = $props()

  let currentIndex = $derived(pages.findIndex((p) => p.id === currentPageId))

  let hasPrev = $derived(currentIndex > 0)
  let hasNext = $derived(currentIndex < pages.length - 1)

  function goToPage(pageId: string): void {
    if (pageId !== currentPageId) {
      goto(`/label/${pageId}`)
    }
  }

  function prevPage(): void {
    if (hasPrev) {
      goToPage(pages[currentIndex - 1].id)
    }
  }

  function nextPage(): void {
    if (hasNext) {
      goToPage(pages[currentIndex + 1].id)
    }
  }

  const statusColors: Record<string, string> = {
    pending: 'bg-muted text-muted-foreground',
    in_progress: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    submitted: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
    reviewed: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
  }
</script>

<div class="border-border bg-muted/50 border-b">
  <div class="flex items-center justify-between px-3 py-2">
    <span class="text-muted-foreground text-xs font-medium tracking-wider uppercase">페이지</span>
    <div class="flex items-center gap-1">
      <button
        class="text-muted-foreground hover:text-foreground hover:bg-accent rounded p-1 transition-colors disabled:cursor-not-allowed disabled:opacity-30"
        disabled={!hasPrev}
        onclick={prevPage}
        title="이전 페이지 ([)"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <span class="text-muted-foreground min-w-[3rem] text-center text-xs">
        {currentIndex + 1} / {pages.length}
      </span>
      <button
        class="text-muted-foreground hover:text-foreground hover:bg-accent rounded p-1 transition-colors disabled:cursor-not-allowed disabled:opacity-30"
        disabled={!hasNext}
        onclick={nextPage}
        title="다음 페이지 (])"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  </div>

  <div class="max-h-48 overflow-y-auto px-2 pb-2">
    <div class="flex flex-wrap gap-1">
      {#each pages as page (page.id)}
        <button
          class="min-w-[2rem] rounded px-1.5 py-0.5 text-xs transition-all
            {page.id === currentPageId
            ? 'bg-primary text-primary-foreground font-medium shadow-sm'
            : 'bg-card border-border text-foreground hover:border-primary/30 hover:bg-primary/10 border'}"
          onclick={() => goToPage(page.id)}
          title="페이지 {page.page_no} ({page.status})"
        >
          {page.page_no}
        </button>
      {/each}
    </div>
  </div>

  {#if pages.length > 0}
    <div class="flex flex-wrap gap-1 px-3 pb-2">
      {#each ['pending', 'in_progress', 'submitted', 'reviewed'] as status}
        {@const count = pages.filter((p) => p.status === status).length}
        {#if count > 0}
          <span class="rounded-full px-1.5 py-0.5 text-[10px] {statusColors[status]}">
            {status === 'in_progress'
              ? '진행중'
              : status === 'pending'
                ? '대기'
                : status === 'submitted'
                  ? '제출'
                  : '검토완료'}
            {count}
          </span>
        {/if}
      {/each}
    </div>
  {/if}
</div>
