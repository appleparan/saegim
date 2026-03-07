<script lang="ts">
  import { page } from '$app/state'
  import Header from '$lib/components/layout/Header.svelte'
  import { Button } from '$lib/components/ui/button'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { getProject, getProjectProgress } from '$lib/api/projects'
  import type { ProjectResponse, ProjectProgressResponse } from '$lib/api/types'
  import { NetworkError } from '$lib/api/client'
  import { untrack } from 'svelte'

  let project = $state<ProjectResponse | null>(null)
  let progress = $state<ProjectProgressResponse | null>(null)
  let isLoading = $state(true)
  let error = $state<string | null>(null)

  function roleLabel(role: string): string {
    const labels: Record<string, string> = {
      owner: '소유자',
      annotator: '작업자',
      reviewer: '검수자',
    }
    return labels[role] ?? role
  }

  const statusConfig = [
    { key: 'pending' as const, label: '대기', color: 'text-muted-foreground', bg: 'bg-muted' },
    {
      key: 'in_progress' as const,
      label: '진행 중',
      color: 'text-blue-700 dark:text-blue-300',
      bg: 'bg-blue-50 dark:bg-blue-950/30',
      border: 'border-blue-200 dark:border-blue-800',
    },
    {
      key: 'submitted' as const,
      label: '제출됨',
      color: 'text-amber-700 dark:text-amber-300',
      bg: 'bg-amber-50 dark:bg-amber-950/30',
      border: 'border-amber-200 dark:border-amber-800',
    },
    {
      key: 'reviewed' as const,
      label: '검토 완료',
      color: 'text-emerald-700 dark:text-emerald-300',
      bg: 'bg-emerald-50 dark:bg-emerald-950/30',
      border: 'border-emerald-200 dark:border-emerald-800',
    },
  ]

  async function loadData() {
    const projectId = page.params.id
    if (!projectId) return
    isLoading = true
    error = null
    try {
      const [proj, prog] = await Promise.all([
        getProject(projectId),
        getProjectProgress(projectId),
      ])
      project = proj
      progress = prog
    } catch (e) {
      if (e instanceof NetworkError) {
        error = '백엔드 서버에 연결할 수 없습니다.'
      } else {
        error = '데이터를 불러오는 데 실패했습니다.'
      }
    } finally {
      isLoading = false
    }
  }

  $effect(() => {
    void page.params.id
    untrack(() => loadData())
  })
</script>

<div class="flex h-full flex-col">
  <Header title={project?.name ?? 'saegim'} />

  <div class="bg-background flex-1 overflow-y-auto p-8">
    <div class="mx-auto max-w-5xl">
      <div class="mb-4">
        <a
          href="/projects/{page.params.id}"
          class="text-muted-foreground hover:text-primary flex w-fit items-center gap-1 text-sm transition-colors"
        >
          <svg
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          {project?.name ?? '프로젝트'}
        </a>
      </div>

      <div class="mb-6">
        <h1 class="text-foreground text-2xl font-bold">작업 현황</h1>
        <p class="text-muted-foreground mt-1 text-sm">프로젝트 전체 진행률을 확인합니다</p>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="진행 현황 불러오는 중..." />
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
          <Button variant="outline" onclick={loadData}>다시 시도</Button>
        </div>
      {:else if progress}
        <!-- Summary Cards -->
        <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div class="card-modern p-5">
            <div class="text-muted-foreground mb-1 text-sm">총 페이지</div>
            <div class="text-foreground text-2xl font-bold">{progress.total_pages}</div>
          </div>
          <div class="card-modern p-5">
            <div class="text-muted-foreground mb-1 text-sm">완료율</div>
            <div class="flex items-center gap-3">
              <div class="text-foreground text-2xl font-bold">{progress.completion_rate}%</div>
              <div class="bg-muted h-2.5 flex-1 overflow-hidden rounded-full">
                <div
                  class="bg-primary h-full rounded-full transition-all"
                  style="width: {progress.completion_rate}%"
                ></div>
              </div>
            </div>
          </div>
          <div class="card-modern p-5">
            <div class="text-muted-foreground mb-1 text-sm">검수 대기</div>
            <div class="text-foreground text-2xl font-bold">
              {progress.status_breakdown.submitted}
            </div>
          </div>
        </div>

        <!-- Status Breakdown -->
        <div class="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {#each statusConfig as cfg (cfg.key)}
            <div class="rounded-xl border {cfg.border ?? 'border-border'} {cfg.bg} p-4">
              <div class="text-muted-foreground text-xs">{cfg.label}</div>
              <div class="mt-1 text-xl font-bold {cfg.color}">
                {progress.status_breakdown[cfg.key]}
              </div>
            </div>
          {/each}
        </div>

        <!-- Documents Table -->
        {#if progress.documents.length > 0}
          <div class="mb-8">
            <h2 class="text-foreground mb-3 text-lg font-semibold">문서별 진행 현황</h2>
            <div class="card-modern overflow-hidden">
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-border border-b">
                      <th class="text-muted-foreground px-4 py-3 text-left font-medium">문서</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">페이지</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">대기</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">진행</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">제출</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">완료</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">진행률</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each progress.documents as doc (doc.document_id)}
                      <tr class="border-border hover:bg-muted/50 border-b last:border-b-0">
                        <td class="text-foreground px-4 py-3 font-medium">{doc.filename}</td>
                        <td class="text-muted-foreground px-3 py-3 text-right">
                          {doc.total_pages}
                        </td>
                        <td class="px-3 py-3 text-right">{doc.status_counts.pending}</td>
                        <td class="px-3 py-3 text-right">{doc.status_counts.in_progress}</td>
                        <td class="px-3 py-3 text-right">{doc.status_counts.submitted}</td>
                        <td class="px-3 py-3 text-right">{doc.status_counts.reviewed}</td>
                        <td class="px-3 py-3 text-right">
                          <div class="flex items-center justify-end gap-2">
                            <div class="bg-muted h-2 w-16 overflow-hidden rounded-full">
                              <div
                                class="bg-primary h-full rounded-full transition-all"
                                style="width: {doc.completion_rate}%"
                              ></div>
                            </div>
                            <span class="text-muted-foreground w-10 text-xs">
                              {doc.completion_rate}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        {/if}

        <!-- Members Table -->
        {#if progress.members.length > 0}
          <div>
            <h2 class="text-foreground mb-3 text-lg font-semibold">멤버별 활동</h2>
            <div class="card-modern overflow-hidden">
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-border border-b">
                      <th class="text-muted-foreground px-4 py-3 text-left font-medium">이름</th>
                      <th class="text-muted-foreground px-3 py-3 text-left font-medium">역할</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">할당</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">진행</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">제출</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">완료</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each progress.members as member (member.user_id)}
                      <tr class="border-border hover:bg-muted/50 border-b last:border-b-0">
                        <td class="text-foreground px-4 py-3 font-medium">{member.user_name}</td>
                        <td class="px-3 py-3">
                          <span
                            class="bg-muted text-muted-foreground inline-block rounded-md px-2 py-0.5 text-xs"
                          >
                            {roleLabel(member.role)}
                          </span>
                        </td>
                        <td class="px-3 py-3 text-right">{member.assigned_pages}</td>
                        <td class="px-3 py-3 text-right">{member.in_progress_pages}</td>
                        <td class="px-3 py-3 text-right">{member.submitted_pages}</td>
                        <td class="px-3 py-3 text-right">{member.reviewed_pages}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        {/if}
      {/if}
    </div>
  </div>
</div>
