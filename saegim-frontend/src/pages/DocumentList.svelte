<script lang="ts">
  import { link } from 'svelte-spa-router'
  import Header from '$lib/components/layout/Header.svelte'
  import Button from '$lib/components/common/Button.svelte'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { getProject } from '$lib/api/projects'
  import { listDocuments, uploadDocument, deleteDocument, listPages } from '$lib/api/documents'
  import type { ProjectResponse, DocumentResponse, PageSummary } from '$lib/api/types'
  import { untrack } from 'svelte'
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
    params.id
    untrack(() => loadData())
  })
</script>

<div class="h-full flex flex-col">
  <Header title={project?.name ?? 'saegim'} />

  <div class="flex-1 p-8 overflow-y-auto bg-gray-50/50">
    <div class="max-w-4xl mx-auto">
      <div class="mb-4">
        <a href="/" use:link class="text-sm text-gray-500 hover:text-primary-600 transition-colors flex items-center gap-1 w-fit">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          프로젝트 목록
        </a>
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
        <div class="bg-red-50/80 border border-red-200 rounded-xl p-6 text-center">
          <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-red-100 flex items-center justify-center">
            <svg class="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <p class="text-red-700 mb-4 font-medium">{error}</p>
          <Button variant="secondary" onclick={loadData}>다시 시도</Button>
        </div>
      {:else if documents.length === 0}
        <div class="bg-linear-to-br from-gray-50 to-gray-100/50 border border-gray-200/80 rounded-2xl p-16 text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-50 flex items-center justify-center">
            <svg class="w-8 h-8 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <p class="text-gray-600 font-medium text-lg mb-2">아직 문서가 없습니다</p>
          <p class="text-sm text-gray-400 mb-6">PDF 파일을 업로드하여 레이블링을 시작하세요.</p>
          <Button variant="primary" onclick={() => fileInput.click()}>
            PDF 업로드
          </Button>
        </div>
      {:else}
        <div class="space-y-3">
          {#each documents as doc}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div class="card-modern overflow-hidden">
              <div class="w-full p-5 text-left hover:bg-gray-50/50 transition-colors cursor-pointer" onclick={() => toggleDocPages(doc.id)}>
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="font-medium text-gray-900">{doc.filename}</h3>
                    <div class="flex items-center gap-2 mt-1.5">
                      <span class="text-sm text-gray-500">{doc.total_pages}페이지</span>
                      <span class="badge
                        {doc.status === 'ready' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                         doc.status === 'processing' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                         doc.status === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
                         'bg-gray-50 text-gray-600 border border-gray-200'}">
                        {doc.status === 'ready' ? '준비됨' : doc.status === 'processing' ? '처리 중' : doc.status === 'error' ? '오류' : '업로드 중'}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <button
                      class="text-xs text-red-400 hover:text-red-600 hover:bg-red-50 px-2 py-1 rounded-lg transition-all"
                      onclick={(e) => handleDeleteDoc(e, doc.id)}
                    >
                      삭제
                    </button>
                    <svg class="w-4 h-4 text-gray-400 transition-transform {expandedDoc === doc.id ? 'rotate-180' : ''}"
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {#if expandedDoc === doc.id}
                <div class="border-t border-gray-100 p-4 bg-gray-50/50">
                  {#if documentPages[doc.id]}
                    <div class="grid grid-cols-6 sm:grid-cols-8 gap-2">
                      {#each documentPages[doc.id] as page}
                        <a href="/label/{page.id}" use:link
                          class="block p-2.5 bg-white border rounded-lg text-center hover:border-primary-300 hover:shadow-sm transition-all
                            {page.status === 'submitted' ? 'border-l-4 border-l-emerald-400 border-gray-200' :
                             page.status === 'in_progress' ? 'border-l-4 border-l-blue-400 border-gray-200' :
                             page.status === 'reviewed' ? 'border-l-4 border-l-violet-400 border-gray-200' :
                             'border-gray-200'}">
                          <span class="text-sm font-medium text-gray-700">{page.page_no}</span>
                          <span class="block text-xs mt-0.5
                            {page.status === 'submitted' ? 'text-emerald-600' :
                             page.status === 'in_progress' ? 'text-blue-600' :
                             page.status === 'reviewed' ? 'text-violet-600' :
                             'text-gray-400'}">
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
