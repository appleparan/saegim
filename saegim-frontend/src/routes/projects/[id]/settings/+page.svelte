<script lang="ts">
  import { page } from '$app/state'
  import Header from '$lib/components/layout/Header.svelte'
  import { Button } from '$lib/components/ui/button'
  import * as Tabs from '$lib/components/ui/tabs'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import OcrSettingsPanel from '$lib/components/settings/OcrSettingsPanel.svelte'
  import ProjectMembersPanel from '$lib/components/settings/ProjectMembersPanel.svelte'
  import {
    getProject,
    getOcrConfig,
    addEngine,
    updateEngine,
    deleteEngine,
    setDefaultEngine,
    testEngineConnection,
    listProjectMembers,
    addProjectMember,
    updateProjectMemberRole,
    removeProjectMember,
  } from '$lib/api/projects'
  import { listUsers, type UserListItem } from '$lib/api/users'
  import type {
    ProjectResponse,
    ProjectMemberResponse,
    ProjectMemberRole,
    OcrConfigResponse,
    OcrConnectionTestResponse,
    EngineInstanceCreate,
  } from '$lib/api/types'
  import { untrack } from 'svelte'
  import { NetworkError } from '$lib/api/client'
  import { authStore } from '$lib/stores/auth.svelte'

  let project = $state<ProjectResponse | null>(null)
  let ocrConfig = $state<OcrConfigResponse | null>(null)
  let members = $state<readonly ProjectMemberResponse[]>([])
  let availableUsers = $state<readonly UserListItem[]>([])
  let isLoading = $state(true)
  let error = $state<string | null>(null)
  let successMessage = $state<string | null>(null)

  // Per-engine connection status and testing state
  let connectionStatuses = $state<Record<string, OcrConnectionTestResponse | null>>({})
  let testingEngines = $state(new Set<string>())

  let currentUserId = $derived(authStore.user?.id ?? null)

  let isOwnerOrAdmin = $derived(
    authStore.isAdmin ||
      members.some((m) => m.user_id === currentUserId && m.role === 'owner'),
  )

  async function loadData() {
    const id = page.params.id
    if (!id) return
    isLoading = true
    error = null
    try {
      const [proj, config, memberList] = await Promise.all([
        getProject(id),
        getOcrConfig(id),
        listProjectMembers(id),
      ])
      project = proj
      ocrConfig = config
      members = memberList

      // Load available users for add member dialog (owner/admin only)
      if (
        authStore.isAdmin ||
        memberList.some((m) => m.user_id === currentUserId && m.role === 'owner')
      ) {
        try {
          availableUsers = await listUsers()
        } catch {
          availableUsers = []
        }
      }
    } catch (e) {
      if (e instanceof NetworkError) {
        error = '백엔드 서버에 연결할 수 없습니다.'
      } else {
        error = '설정을 불러오는 데 실패했습니다.'
      }
    } finally {
      isLoading = false
    }
  }

  function showSuccess(msg: string) {
    successMessage = msg
    setTimeout(() => (successMessage = null), 3000)
  }

  // --- OCR Engine handlers ---

  async function handleAddEngine(data: EngineInstanceCreate) {
    const id = page.params.id
    if (!id) return
    error = null
    try {
      ocrConfig = await addEngine(id, data)
      showSuccess('엔진이 추가되었습니다.')
    } catch {
      error = '엔진 추가에 실패했습니다.'
    }
  }

  async function handleUpdateEngine(
    engineId: string,
    data: { name?: string; config?: Record<string, unknown> },
  ) {
    const id = page.params.id
    if (!id) return
    error = null
    try {
      ocrConfig = await updateEngine(id, engineId, data)
      showSuccess('엔진 설정이 저장되었습니다.')
    } catch {
      error = '엔진 설정 저장에 실패했습니다.'
    }
  }

  async function handleDeleteEngine(engineId: string) {
    const id = page.params.id
    if (!id) return
    error = null
    try {
      ocrConfig = await deleteEngine(id, engineId)
      // Clear connection status for deleted engine
      const next = { ...connectionStatuses }
      delete next[engineId]
      connectionStatuses = next
      showSuccess('엔진이 삭제되었습니다.')
    } catch {
      error = '엔진 삭제에 실패했습니다.'
    }
  }

  async function handleSetDefault(engineId: string) {
    const id = page.params.id
    if (!id) return
    error = null
    try {
      ocrConfig = await setDefaultEngine(id, { engine_id: engineId })
    } catch {
      error = '기본 엔진 설정에 실패했습니다.'
    }
  }

  async function handleTestEngine(engineId: string) {
    const id = page.params.id
    if (!id) return
    testingEngines = new Set([...testingEngines, engineId])
    try {
      const result = await testEngineConnection(id, { engine_id: engineId })
      connectionStatuses = { ...connectionStatuses, [engineId]: result }
    } catch {
      connectionStatuses = {
        ...connectionStatuses,
        [engineId]: { success: false, message: '연결 테스트에 실패했습니다.' },
      }
    } finally {
      const next = new Set(testingEngines)
      next.delete(engineId)
      testingEngines = next
    }
  }

  // --- Member handlers ---

  async function handleAddMember(userId: string, role: ProjectMemberRole) {
    const id = page.params.id
    if (!id) return
    error = null
    try {
      const newMember = await addProjectMember(id, { user_id: userId, role })
      members = [...members, newMember]
      showSuccess('멤버가 추가되었습니다.')
    } catch {
      error = '멤버 추가에 실패했습니다.'
    }
  }

  async function handleUpdateMemberRole(userId: string, role: ProjectMemberRole) {
    const id = page.params.id
    if (!id) return
    error = null
    try {
      const updated = await updateProjectMemberRole(id, userId, { role })
      members = members.map((m) => (m.user_id === userId ? updated : m))
      showSuccess('역할이 변경되었습니다.')
    } catch {
      error = '역할 변경에 실패했습니다.'
    }
  }

  async function handleRemoveMember(userId: string) {
    const id = page.params.id
    if (!id) return
    error = null
    try {
      await removeProjectMember(id, userId)
      members = members.filter((m) => m.user_id !== userId)
      showSuccess('멤버가 제거되었습니다.')
    } catch {
      error = '멤버 제거에 실패했습니다.'
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
    <div class="mx-auto max-w-2xl">
      <div class="mb-4">
        {#if page.params.id}
          <a
            href="/projects/{page.params.id}"
            class="text-muted-foreground hover:text-primary flex
              w-fit items-center gap-1 text-sm transition-colors"
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
            문서 목록
          </a>
        {/if}
      </div>

      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-foreground text-2xl font-bold">프로젝트 설정</h1>
          {#if project}
            <p class="text-muted-foreground mt-1 text-sm">{project.name}</p>
          {/if}
        </div>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="설정 불러오는 중..." />
        </div>
      {:else if error}
        <div
          class="bg-destructive/10 dark:bg-destructive/20 border-destructive/30 rounded-xl border p-6 text-center"
        >
          <p class="text-destructive mb-4 font-medium">{error}</p>
          <Button variant="outline" onclick={loadData}>다시 시도</Button>
        </div>
      {:else if ocrConfig}
        {#if successMessage}
          <div
            class="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3
              text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300"
          >
            {successMessage}
          </div>
        {/if}

        <Tabs.Root value="ocr" class="w-full">
          <Tabs.List class="mb-4">
            <Tabs.Trigger value="ocr">OCR 설정</Tabs.Trigger>
            <Tabs.Trigger value="members">멤버 관리</Tabs.Trigger>
          </Tabs.List>

          <Tabs.Content value="ocr">
            <div class="card-modern p-6">
              <OcrSettingsPanel
                config={ocrConfig}
                {connectionStatuses}
                {testingEngines}
                onadd={handleAddEngine}
                onupdate={handleUpdateEngine}
                ondelete={handleDeleteEngine}
                onsetdefault={handleSetDefault}
                ontest={handleTestEngine}
              />
            </div>
          </Tabs.Content>

          <Tabs.Content value="members">
            <div class="card-modern p-6">
              <ProjectMembersPanel
                {members}
                {currentUserId}
                {isOwnerOrAdmin}
                {availableUsers}
                onadd={handleAddMember}
                onupdate={handleUpdateMemberRole}
                onremove={handleRemoveMember}
              />
            </div>
          </Tabs.Content>
        </Tabs.Root>
      {/if}
    </div>
  </div>
</div>
