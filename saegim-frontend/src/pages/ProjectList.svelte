<script lang="ts">
  import { link } from 'svelte-spa-router'
  import Header from '$lib/components/layout/Header.svelte'
  import Button from '$lib/components/common/Button.svelte'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { listProjects, createProject, deleteProject } from '$lib/api/projects'
  import type { ProjectResponse } from '$lib/api/types'
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
    loadProjects()
  })
</script>

<div class="h-full flex flex-col">
  <Header title="saegim" />

  <div class="flex-1 p-8 overflow-y-auto bg-gray-50/50">
    <div class="max-w-4xl mx-auto">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">프로젝트</h1>
          <p class="text-sm text-gray-500 mt-1">문서 레이블링 프로젝트를 관리합니다</p>
        </div>
        <Button variant="primary" onclick={() => (showCreateDialog = true)}>
          새 프로젝트
        </Button>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="프로젝트 불러오는 중..." />
        </div>
      {:else if error}
        <div class="bg-red-50/80 border border-red-200 rounded-xl p-6 text-center">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-red-100 flex items-center justify-center">
            <svg class="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <p class="text-red-700 mb-4 font-medium">{error}</p>
          <Button variant="secondary" onclick={loadProjects}>다시 시도</Button>
        </div>
      {:else if projects.length === 0}
        <div class="bg-linear-to-br from-gray-50 to-gray-100/50 border border-gray-200/80 rounded-2xl p-16 text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-50 flex items-center justify-center">
            <svg class="w-8 h-8 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 10.5v6m3-3H9m4.06-7.19l-2.12-2.12a1.5 1.5 0 00-1.06-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
            </svg>
          </div>
          <p class="text-gray-600 font-medium text-lg mb-2">아직 프로젝트가 없습니다</p>
          <p class="text-sm text-gray-400 mb-6">첫 프로젝트를 만들어 문서 레이블링을 시작하세요.</p>
          <Button variant="primary" onclick={() => (showCreateDialog = true)}>
            첫 프로젝트 만들기
          </Button>
        </div>
      {:else}
        <div class="grid gap-4 sm:grid-cols-2">
          {#each projects as project}
            <div class="card-modern card-accent">
              <a
                href="/projects/{project.id}"
                use:link
                class="block p-5"
              >
                <h3 class="font-semibold text-gray-900 text-base">{project.name}</h3>
                {#if project.description}
                  <p class="text-sm text-gray-500 mt-1.5 line-clamp-2">{project.description}</p>
                {/if}
                <p class="text-xs text-gray-400 mt-3">
                  {new Date(project.created_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </a>
              <div class="border-t border-gray-100 px-5 py-2 flex justify-end">
                <button
                  class="text-xs text-red-400 hover:text-red-600 transition-colors"
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
    <div class="fixed inset-0 modal-backdrop flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4 border border-gray-100">
        <h2 class="text-lg font-semibold text-gray-900 mb-1">새 프로젝트 만들기</h2>
        <p class="text-sm text-gray-400 mb-5">프로젝트 정보를 입력하세요.</p>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5" for="project-name">프로젝트 이름</label>
            <input
              id="project-name"
              type="text"
              class="block w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all outline-none"
              bind:value={newProjectName}
              placeholder="프로젝트 이름을 입력하세요"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5" for="project-description">설명 (선택)</label>
            <textarea
              id="project-description"
              class="block w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all outline-none resize-none"
              bind:value={newProjectDescription}
              placeholder="프로젝트에 대한 설명을 입력하세요"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-6">
          <Button variant="secondary" onclick={() => (showCreateDialog = false)}>취소</Button>
          <Button
            variant="primary"
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
