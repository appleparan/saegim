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

  <div class="flex-1 p-8 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-gray-900">프로젝트</h1>
        <Button variant="primary" onclick={() => (showCreateDialog = true)}>
          새 프로젝트
        </Button>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="프로젝트 불러오는 중..." />
        </div>
      {:else if error}
        <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p class="text-red-700 mb-4">{error}</p>
          <Button variant="secondary" onclick={loadProjects}>다시 시도</Button>
        </div>
      {:else if projects.length === 0}
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <p class="text-gray-500 mb-4">아직 프로젝트가 없습니다.</p>
          <Button variant="primary" onclick={() => (showCreateDialog = true)}>
            첫 프로젝트 만들기
          </Button>
        </div>
      {:else}
        <div class="grid gap-4">
          {#each projects as project}
            <div class="flex items-center bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all">
              <a
                href="/projects/{project.id}"
                use:link
                class="flex-1 p-4"
              >
                <h3 class="font-semibold text-gray-900">{project.name}</h3>
                {#if project.description}
                  <p class="text-sm text-gray-500 mt-1">{project.description}</p>
                {/if}
                <p class="text-xs text-gray-400 mt-2">
                  {new Date(project.created_at).toLocaleDateString('ko-KR')}
                </p>
              </a>
              <button
                class="px-3 py-2 mr-2 text-sm text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                onclick={(e) => handleDeleteProject(e, project.id)}
              >
                삭제
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  {#if showCreateDialog}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
        <h2 class="text-lg font-semibold mb-4">새 프로젝트 만들기</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1" for="project-name">프로젝트 이름</label>
            <input
              id="project-name"
              type="text"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              bind:value={newProjectName}
              placeholder="프로젝트 이름"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1" for="project-description">설명 (선택)</label>
            <textarea
              id="project-description"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              bind:value={newProjectDescription}
              placeholder="프로젝트 설명"
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
