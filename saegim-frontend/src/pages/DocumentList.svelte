<script lang="ts">
  import { link } from 'svelte-spa-router'
  import Header from '$lib/components/layout/Header.svelte'
  import Button from '$lib/components/common/Button.svelte'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { getProject } from '$lib/api/projects'
  import { listDocuments, uploadDocument, deleteDocument, listPages } from '$lib/api/documents'
  import type { ProjectResponse, DocumentResponse, PageSummary } from '$lib/api/types'
  import { NetworkError } from '$lib/api/client'

  let { params }: { params: { id: string } } = $props()

  let project = $state<ProjectResponse | null>(null)
  let documents = $state<readonly DocumentResponse[]>([])
  let documentPages = $state<Record<string, readonly PageSummary[]>>({})
  let isLoading = $state(true)
  let error = $state<string | null>(null)
  let isUploading = $state(false)
  let expandedDoc = $state<string | null>(null)

  let fileInput: HTMLInputElement

  async function loadData() {
    if (!params?.id) return
    isLoading = true
    error = null
    try {
      const [proj, docs] = await Promise.all([
        getProject(params.id),
        listDocuments(params.id),
      ])
      project = proj
      documents = docs
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

  async function handleUpload(e: Event) {
    const target = e.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file || !params?.id) return

    isUploading = true
    error = null
    try {
      const doc = await uploadDocument(params.id, file)
      documents = [...documents, doc]
    } catch {
      error = 'PDF 업로드에 실패했습니다.'
    } finally {
      isUploading = false
      target.value = ''
    }
  }

  async function toggleDocPages(docId: string) {
    if (expandedDoc === docId) {
      expandedDoc = null
      return
    }
    expandedDoc = docId
    if (!documentPages[docId]) {
      try {
        const pages = await listPages(docId)
        documentPages = { ...documentPages, [docId]: pages }
      } catch {
        // Pages list is supplementary
      }
    }
  }

  async function handleDeleteDoc(e: Event, docId: string) {
    e.stopPropagation()
    if (!confirm('이 문서를 삭제하시겠습니까?')) return
    try {
      await deleteDocument(docId)
      documents = documents.filter((d) => d.id !== docId)
      const { [docId]: _, ...rest } = documentPages
      documentPages = rest
      if (expandedDoc === docId) expandedDoc = null
    } catch {
      error = '문서 삭제에 실패했습니다.'
    }
  }

  $effect(() => {
    loadData()
  })
</script>

<div class="h-full flex flex-col">
  <Header title={project?.name ?? 'saegim'} />

  <div class="flex-1 p-8 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
      <div class="mb-4">
        <a href="/" use:link class="text-sm text-blue-600 hover:text-blue-800">&larr; 프로젝트 목록</a>
      </div>

      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{project?.name ?? '문서'}</h1>
          {#if project?.description}
            <p class="text-sm text-gray-500 mt-1">{project.description}</p>
          {/if}
        </div>
        <div>
          <input type="file" accept=".pdf" class="hidden" bind:this={fileInput} onchange={handleUpload} />
          <Button variant="primary" disabled={isUploading} onclick={() => fileInput.click()}>
            {isUploading ? '업로드 중...' : 'PDF 업로드'}
          </Button>
        </div>
      </div>

      {#if isLoading}
        <div class="py-12"><LoadingSpinner message="문서 불러오는 중..." /></div>
      {:else if error}
        <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p class="text-red-700 mb-4">{error}</p>
          <Button variant="secondary" onclick={loadData}>다시 시도</Button>
        </div>
      {:else if documents.length === 0}
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <p class="text-gray-500 mb-4">아직 문서가 없습니다.</p>
          <p class="text-sm text-gray-400">PDF 파일을 업로드하여 레이블링을 시작하세요.</p>
        </div>
      {:else}
        <div class="space-y-3">
          {#each documents as doc}
            <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <button class="w-full p-4 text-left hover:bg-gray-50 transition-colors" onclick={() => toggleDocPages(doc.id)}>
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="font-medium text-gray-900">{doc.filename}</h3>
                    <p class="text-sm text-gray-500 mt-1">
                      {doc.total_pages}페이지
                      <span class="mx-1">&middot;</span>
                      <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                        {doc.status === 'ready' ? 'bg-green-100 text-green-800' :
                         doc.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                         doc.status === 'error' ? 'bg-red-100 text-red-800' :
                         'bg-gray-100 text-gray-800'}">
                        {doc.status === 'ready' ? '준비됨' : doc.status === 'processing' ? '처리 중' : doc.status === 'error' ? '오류' : '업로드 중'}
                      </span>
                    </p>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      class="text-sm text-red-500 hover:text-red-700 hover:bg-red-50 px-2 py-1 rounded transition-colors"
                      onclick={(e) => handleDeleteDoc(e, doc.id)}
                    >
                      삭제
                    </button>
                    <span class="text-gray-400 text-sm">{expandedDoc === doc.id ? '▲' : '▼'}</span>
                  </div>
                </div>
              </button>

              {#if expandedDoc === doc.id}
                <div class="border-t border-gray-100 p-4 bg-gray-50">
                  {#if documentPages[doc.id]}
                    <div class="grid grid-cols-6 gap-2">
                      {#each documentPages[doc.id] as page}
                        <a href="/label/{page.id}" use:link class="block p-2 bg-white border border-gray-200 rounded text-center hover:border-blue-300 transition-colors">
                          <span class="text-sm font-medium">{page.page_no}</span>
                          <span class="block text-xs mt-0.5
                            {page.status === 'submitted' ? 'text-green-600' :
                             page.status === 'in_progress' ? 'text-blue-600' : 'text-gray-400'}">
                            {page.status === 'submitted' ? '완료' : page.status === 'in_progress' ? '진행 중' : page.status === 'reviewed' ? '검토됨' : '대기'}
                          </span>
                        </a>
                      {/each}
                    </div>
                  {:else}
                    <LoadingSpinner size="sm" />
                  {/if}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
