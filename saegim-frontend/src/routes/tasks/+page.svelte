<script lang="ts">
  import Header from '$lib/components/layout/Header.svelte'
  import { Button } from '$lib/components/ui/button'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { getMyTasks } from '$lib/api/tasks'
  import type { TaskResponse, PageStatus } from '$lib/api/types'
  import { NetworkError } from '$lib/api/client'
  import { untrack } from 'svelte'

  let tasks = $state<readonly TaskResponse[]>([])
  let isLoading = $state(true)
  let error = $state<string | null>(null)
  let statusFilter = $state<PageStatus | 'all'>('all')

  let filteredTasks = $derived(
    statusFilter === 'all' ? tasks : tasks.filter((t) => t.status === statusFilter),
  )

  let statusCounts = $derived({
    all: tasks.length,
    in_progress: tasks.filter((t) => t.status === 'in_progress').length,
    submitted: tasks.filter((t) => t.status === 'submitted').length,
  })

  const statusColors: Record<PageStatus, string> = {
    pending:
      'border border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900/30 dark:text-zinc-300',
    in_progress:
      'border border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-300',
    submitted:
      'border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300',
    reviewed:
      'border border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300',
  }

  const statusLabels: Record<PageStatus, string> = {
    pending: '대기',
    in_progress: '진행중',
    submitted: '제출됨',
    reviewed: '검토완료',
  }

  type FilterKey = 'all' | 'in_progress' | 'submitted'
  const filterOptions: { key: FilterKey; label: string }[] = [
    { key: 'all', label: '전체' },
    { key: 'in_progress', label: '진행중' },
    { key: 'submitted', label: '제출됨' },
  ]

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  async function loadTasks() {
    isLoading = true
    error = null
    try {
      tasks = await getMyTasks()
    } catch (e) {
      if (e instanceof NetworkError) {
        error = '백엔드 서버에 연결할 수 없습니다.'
      } else {
        error = '작업 목록을 불러오는 데 실패했습니다.'
      }
    } finally {
      isLoading = false
    }
  }

  $effect(() => {
    untrack(() => loadTasks())
  })
</script>

<div class="flex h-full flex-col">
  <Header title="saegim" />

  <div class="bg-background flex-1 overflow-y-auto p-8">
    <div class="mx-auto max-w-4xl">
      <div class="mb-6">
        <h1 class="text-foreground text-2xl font-bold">내 작업</h1>
        <p class="text-muted-foreground mt-1 text-sm">할당된 레이블링 작업을 관리합니다</p>
      </div>

      {#if !isLoading && !error}
        <div class="mb-6 flex items-center gap-2">
          {#each filterOptions as opt (opt.key)}
            <button
              class="rounded-lg px-3 py-1.5 text-sm font-medium transition-all
                {statusFilter === opt.key
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'bg-muted text-muted-foreground hover:bg-accent'}"
              onclick={() => (statusFilter = opt.key)}
            >
              {opt.label}
              <span
                class="ml-1 rounded-full px-1.5 py-0.5 text-xs
                  {statusFilter === opt.key
                  ? 'bg-primary-foreground/20'
                  : 'bg-muted-foreground/20'}"
              >
                {statusCounts[opt.key] ?? 0}
              </span>
            </button>
          {/each}
        </div>
      {/if}

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="작업 불러오는 중..." />
        </div>
      {:else if error}
        <div
          class="bg-destructive/10 dark:bg-destructive/20 border-destructive/30 rounded-xl border p-6 text-center"
        >
          <div
            class="bg-destructive/20 mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl"
          >
            <svg
              class="text-destructive h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
          </div>
          <p class="text-destructive mb-4 font-medium">{error}</p>
          <Button variant="outline" onclick={loadTasks}>다시 시도</Button>
        </div>
      {:else if tasks.length === 0}
        <div class="bg-muted border-border rounded-2xl border p-16 text-center">
          <div
            class="bg-primary/10 mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
          >
            <svg
              class="text-primary h-8 w-8"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p class="text-muted-foreground mb-2 text-lg font-medium">할당된 작업이 없습니다</p>
          <p class="text-muted-foreground text-sm">
            프로젝트 관리자가 작업을 할당하면 여기에 표시됩니다.
          </p>
        </div>
      {:else if filteredTasks.length === 0}
        <div class="bg-muted border-border rounded-xl border p-8 text-center">
          <p class="text-muted-foreground text-sm">해당 상태의 작업이 없습니다.</p>
        </div>
      {:else}
        <div class="space-y-3">
          {#each filteredTasks as task (task.page_id)}
            <a href="/label/{task.page_id}" class="card-modern block">
              <div class="hover:bg-accent p-5 transition-colors">
                <div class="flex items-center justify-between">
                  <div>
                    <div class="flex items-center gap-2">
                      <h3 class="text-foreground font-medium">
                        {task.document_filename}
                        <span class="text-muted-foreground font-normal">
                          — 페이지 {task.page_no}
                        </span>
                      </h3>
                      <span class="badge {statusColors[task.status]}">
                        {statusLabels[task.status]}
                      </span>
                    </div>
                    <div class="text-muted-foreground mt-1.5 flex items-center gap-3 text-sm">
                      <span>{task.project_name}</span>
                      <span>·</span>
                      <span>할당: {formatDate(task.assigned_at)}</span>
                    </div>
                  </div>
                  <svg
                    class="text-muted-foreground h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </a>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
