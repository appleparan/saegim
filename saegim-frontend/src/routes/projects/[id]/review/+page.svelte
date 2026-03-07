<script lang="ts">
  import { page } from '$app/state'
  import Header from '$lib/components/layout/Header.svelte'
  import { Button } from '$lib/components/ui/button'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { getProject } from '$lib/api/projects'
  import { getReviewQueue } from '$lib/api/tasks'
  import { reviewPage } from '$lib/api/pages'
  import { uiStore } from '$lib/stores/ui.svelte'
  import type { ProjectResponse, ReviewQueueItem } from '$lib/api/types'
  import { ApiError, NetworkError } from '$lib/api/client'
  import { untrack } from 'svelte'

  let project = $state<ProjectResponse | null>(null)
  let queue = $state<readonly ReviewQueueItem[]>([])
  let isLoading = $state(true)
  let error = $state<string | null>(null)
  let activeRejectId = $state<string | null>(null)
  let rejectComment = $state('')
  let processingId = $state<string | null>(null)

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  async function loadData() {
    const projectId = page.params.id
    if (!projectId) return
    isLoading = true
    error = null
    try {
      const [proj, items] = await Promise.all([getProject(projectId), getReviewQueue(projectId)])
      project = proj
      queue = items
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

  async function handleApprove(pageId: string) {
    processingId = pageId
    try {
      await reviewPage(pageId, { action: 'approved' })
      queue = queue.filter((item) => item.page_id !== pageId)
      uiStore.showNotification('승인 완료', 'success')
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        uiStore.showNotification('이미 처리된 항목입니다', 'info')
        queue = queue.filter((item) => item.page_id !== pageId)
      } else {
        uiStore.showNotification('승인에 실패했습니다', 'error')
      }
    } finally {
      processingId = null
    }
  }

  function startReject(pageId: string) {
    activeRejectId = pageId
    rejectComment = ''
  }

  function cancelReject() {
    activeRejectId = null
    rejectComment = ''
  }

  async function confirmReject(pageId: string) {
    processingId = pageId
    try {
      await reviewPage(pageId, {
        action: 'rejected',
        comment: rejectComment.trim() || undefined,
      })
      queue = queue.filter((item) => item.page_id !== pageId)
      activeRejectId = null
      rejectComment = ''
      uiStore.showNotification('반려 완료', 'success')
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        uiStore.showNotification('이미 처리된 항목입니다', 'info')
        queue = queue.filter((item) => item.page_id !== pageId)
      } else {
        uiStore.showNotification('반려에 실패했습니다', 'error')
      }
    } finally {
      processingId = null
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
    <div class="mx-auto max-w-4xl">
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
        <h1 class="text-foreground text-2xl font-bold">검수 큐</h1>
        <p class="text-muted-foreground mt-1 text-sm">제출된 페이지를 검수합니다</p>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="검수 대기 목록 불러오는 중..." />
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
      {:else if queue.length === 0}
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
          <p class="text-muted-foreground mb-2 text-lg font-medium">검수 대기 항목이 없습니다</p>
          <p class="text-muted-foreground text-sm">제출된 페이지가 있으면 여기에 표시됩니다.</p>
        </div>
      {:else}
        <div class="text-muted-foreground mb-4 text-sm">
          {queue.length}건의 검수 대기 항목
        </div>
        <div class="space-y-3">
          {#each queue as item (item.page_id)}
            <div class="card-modern overflow-hidden">
              <div class="p-5">
                <div class="flex items-center justify-between">
                  <div>
                    <div class="flex items-center gap-2">
                      <a
                        href="/label/{item.page_id}"
                        class="text-foreground hover:text-primary font-medium transition-colors"
                      >
                        {item.document_filename}
                        <span class="font-normal">— 페이지 {item.page_no}</span>
                      </a>
                    </div>
                    <div class="text-muted-foreground mt-1.5 flex items-center gap-3 text-sm">
                      {#if item.assigned_to_name}
                        <span>작업자: {item.assigned_to_name}</span>
                        <span>·</span>
                      {/if}
                      <span>제출: {formatDate(item.submitted_at)}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={processingId === item.page_id}
                      onclick={() => startReject(item.page_id)}
                    >
                      반려
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      disabled={processingId === item.page_id}
                      onclick={() => handleApprove(item.page_id)}
                    >
                      {processingId === item.page_id ? '처리 중...' : '승인'}
                    </Button>
                  </div>
                </div>
              </div>

              {#if activeRejectId === item.page_id}
                <div class="border-border border-t p-4">
                  <label
                    class="text-foreground mb-1.5 block text-sm font-medium"
                    for="reject-comment-{item.page_id}"
                  >
                    반려 사유 (선택)
                  </label>
                  <textarea
                    id="reject-comment-{item.page_id}"
                    class="border-border focus:border-ring focus:ring-ring/20 bg-background text-foreground mb-3 block w-full resize-none rounded-lg border px-3 py-2.5 text-sm transition-all outline-none focus:ring-2"
                    bind:value={rejectComment}
                    placeholder="반려 사유를 입력하세요"
                    rows="2"
                    maxlength={2000}
                  ></textarea>
                  <div class="flex justify-end gap-2">
                    <Button variant="outline" size="sm" onclick={cancelReject}>취소</Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      disabled={processingId === item.page_id}
                      onclick={() => confirmReject(item.page_id)}
                    >
                      {processingId === item.page_id ? '처리 중...' : '반려 확인'}
                    </Button>
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
