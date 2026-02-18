<script lang="ts">
  import { link } from 'svelte-spa-router'
  import Header from '$lib/components/layout/Header.svelte'
  import Button from '$lib/components/common/Button.svelte'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import OcrSettingsPanel from '$lib/components/settings/OcrSettingsPanel.svelte'
  import { getProject, getOcrConfig, updateOcrConfig } from '$lib/api/projects'
  import type { ProjectResponse, OcrConfigResponse } from '$lib/api/types'
  import { untrack } from 'svelte'
  import { NetworkError } from '$lib/api/client'

  let { params }: { params: { id: string } } = $props()

  let project = $state<ProjectResponse | null>(null)
  let ocrConfig = $state<OcrConfigResponse | null>(null)
  let isLoading = $state(true)
  let isSaving = $state(false)
  let error = $state<string | null>(null)
  let successMessage = $state<string | null>(null)

  async function loadData() {
    if (!params?.id) return
    isLoading = true
    error = null
    try {
      const [proj, config] = await Promise.all([
        getProject(params.id),
        getOcrConfig(params.id),
      ])
      project = proj
      ocrConfig = config
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

  async function handleSave(config: OcrConfigResponse) {
    if (!params?.id) return
    isSaving = true
    error = null
    successMessage = null
    try {
      ocrConfig = await updateOcrConfig(params.id, config)
      successMessage = 'OCR 설정이 저장되었습니다.'
      setTimeout(() => (successMessage = null), 3000)
    } catch {
      error = 'OCR 설정 저장에 실패했습니다.'
    } finally {
      isSaving = false
    }
  }

  $effect(() => {
    params.id
    untrack(() => loadData())
  })
</script>

<div class="h-full flex flex-col">
  <Header title={project?.name ?? 'saegim'} />

  <div class="flex-1 p-8 overflow-y-auto bg-gray-50/50">
    <div class="max-w-2xl mx-auto">
      <div class="mb-4">
        {#if params?.id}
          <a
            href="/projects/{params.id}"
            use:link
            class="text-sm text-gray-500 hover:text-primary-600
              transition-colors flex items-center gap-1 w-fit"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
            문서 목록
          </a>
        {/if}
      </div>

      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">프로젝트 설정</h1>
          {#if project}
            <p class="text-sm text-gray-500 mt-1">{project.name}</p>
          {/if}
        </div>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="설정 불러오는 중..." />
        </div>
      {:else if error}
        <div
          class="bg-red-50/80 border border-red-200 rounded-xl p-6 text-center"
        >
          <p class="text-red-700 mb-4 font-medium">{error}</p>
          <Button variant="secondary" onclick={loadData}>다시 시도</Button>
        </div>
      {:else if ocrConfig}
        {#if successMessage}
          <div
            class="mb-4 bg-green-50 border border-green-200
              rounded-lg p-3 text-sm text-green-700"
          >
            {successMessage}
          </div>
        {/if}

        <div class="card-modern p-6">
          <OcrSettingsPanel
            config={ocrConfig}
            saving={isSaving}
            onsave={handleSave}
          />
        </div>
      {/if}
    </div>
  </div>
</div>
