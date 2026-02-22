<script lang="ts">
  import Header from '$lib/components/layout/Header.svelte'
  import { Button } from '$lib/components/ui/button'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { listProjects, createProject, deleteProject } from '$lib/api/projects'
  import type { ProjectResponse } from '$lib/api/types'
  import { untrack } from 'svelte'
  import { NetworkError } from '$lib/api/client'

  let projects = $state<readonly ProjectResponse[]>([])
  let isLoading = $state(true)
  let error = $state<string | null>(null)
  let showCreateDialog = $state(false)
  let newProjectName = $state('')
  let newProjectDescription = $state('')
  let isCreating = $state(false)

  async function loadProjects() {
    isLoading = true
    error = null
    try {
      projects = await listProjects()
    } catch (e) {
      if (e instanceof NetworkError) {
        error = '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.'
      } else {
        error = '프로젝트 목록을 불러오는 데 실패했습니다.'
      }
    } finally {
      isLoading = false
    }
  }

  async function handleCreateProject() {
    if (!newProjectName.trim()) return
    isCreating = true
    try {
      const project = await createProject({
        name: newProjectName.trim(),
        description: newProjectDescription.trim() || undefined,
      })
      projects = [...projects, project]
      showCreateDialog = false
      newProjectName = ''
      newProjectDescription = ''
    } catch {
      error = '프로젝트 생성에 실패했습니다.'
    } finally {
      isCreating = false
    }
  }

  async function handleDeleteProject(e: Event, projectId: string) {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm('이 프로젝트와 모든 문서를 삭제하시겠습니까?')) return
    try {
      await deleteProject(projectId)
      projects = projects.filter((p) => p.id !== projectId)
    } catch {
      error = '프로젝트 삭제에 실패했습니다.'
    }
  }

  $effect(() => {
    untrack(() => loadProjects())
  })
</script>

<div class="flex h-full flex-col">
  <Header title="saegim" />

  <div class="bg-background flex-1 overflow-y-auto p-8">
    <div class="mx-auto max-w-4xl">
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-foreground text-2xl font-bold">프로젝트</h1>
          <p class="text-muted-foreground mt-1 text-sm">문서 레이블링 프로젝트를 관리합니다</p>
        </div>
        <Button variant="default" onclick={() => (showCreateDialog = true)}>새 프로젝트</Button>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="프로젝트 불러오는 중..." />
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
          <Button variant="outline" onclick={loadProjects}>다시 시도</Button>
        </div>
      {:else if projects.length === 0}
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
                d="M12 10.5v6m3-3H9m4.06-7.19l-2.12-2.12a1.5 1.5 0 00-1.06-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
              />
            </svg>
          </div>
          <p class="text-muted-foreground mb-2 text-lg font-medium">아직 프로젝트가 없습니다</p>
          <p class="text-muted-foreground mb-6 text-sm">
            첫 프로젝트를 만들어 문서 레이블링을 시작하세요.
          </p>
          <Button variant="default" onclick={() => (showCreateDialog = true)}>
            첫 프로젝트 만들기
          </Button>
        </div>
      {:else}
        <div class="grid gap-4 sm:grid-cols-2">
          {#each projects as project}
            <div class="card-modern card-accent">
              <a href="/projects/{project.id}" class="block p-5">
                <h3 class="text-foreground text-base font-semibold">{project.name}</h3>
                {#if project.description}
                  <p class="text-muted-foreground mt-1.5 line-clamp-2 text-sm">
                    {project.description}
                  </p>
                {/if}
                <p class="text-muted-foreground mt-3 text-xs">
                  {new Date(project.created_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </a>
              <div class="border-border flex justify-end border-t px-5 py-2">
                <button
                  class="text-muted-foreground hover:text-destructive text-xs transition-colors"
                  onclick={(e) => handleDeleteProject(e, project.id)}
                >
                  삭제
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  {#if showCreateDialog}
    <div class="modal-backdrop fixed inset-0 z-50 flex items-center justify-center">
      <div class="bg-card border-border mx-4 w-full max-w-md rounded-2xl border p-6 shadow-2xl">
        <h2 class="text-foreground mb-1 text-lg font-semibold">새 프로젝트 만들기</h2>
        <p class="text-muted-foreground mb-5 text-sm">프로젝트 정보를 입력하세요.</p>
        <div class="space-y-4">
          <div>
            <label class="text-foreground mb-1.5 block text-sm font-medium" for="project-name"
              >프로젝트 이름</label
            >
            <input
              id="project-name"
              type="text"
              class="border-border focus:border-ring focus:ring-ring/20 bg-background text-foreground block w-full rounded-lg border px-3 py-2.5 text-sm transition-all outline-none focus:ring-2"
              bind:value={newProjectName}
              placeholder="프로젝트 이름을 입력하세요"
            />
          </div>
          <div>
            <label
              class="text-foreground mb-1.5 block text-sm font-medium"
              for="project-description">설명 (선택)</label
            >
            <textarea
              id="project-description"
              class="border-border focus:border-ring focus:ring-ring/20 bg-background text-foreground block w-full resize-none rounded-lg border px-3 py-2.5 text-sm transition-all outline-none focus:ring-2"
              bind:value={newProjectDescription}
              placeholder="프로젝트에 대한 설명을 입력하세요"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="mt-6 flex justify-end gap-2">
          <Button variant="outline" onclick={() => (showCreateDialog = false)}>취소</Button>
          <Button
            variant="default"
            disabled={!newProjectName.trim() || isCreating}
            onclick={handleCreateProject}
          >
            {isCreating ? '생성 중...' : '생성'}
          </Button>
        </div>
      </div>
    </div>
  {/if}
</div>
