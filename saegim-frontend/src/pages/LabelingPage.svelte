<script lang="ts">
  import { link } from 'svelte-spa-router'
  import Header from '$lib/components/layout/Header.svelte'
  import Sidebar from '$lib/components/layout/Sidebar.svelte'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import Button from '$lib/components/common/Button.svelte'
  import HybridViewer from '$lib/components/canvas/HybridViewer.svelte'
  import ElementList from '$lib/components/panels/ElementList.svelte'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import { untrack } from 'svelte'
  import { getPage, savePage } from '$lib/api/pages'
  import { API_BASE, NetworkError } from '$lib/api/client'
  import type { PageResponse } from '$lib/api/types'

  let { params }: { params: { pageId: string } } = $props()

  let pageData = $state<PageResponse | null>(null)
  let saving = $state(false)

  async function loadPage() {
    if (!params?.pageId) return
    annotationStore.setLoading(true)
    annotationStore.setError(null)
    try {
      const data = await getPage(params.pageId)
      pageData = data
      annotationStore.load(params.pageId, data.annotation_data)
      canvasStore.setImageDimensions(data.width, data.height)
    } catch (e) {
      if (e instanceof NetworkError) {
        annotationStore.setError('백엔드 서버에 연결할 수 없습니다.')
      } else {
        annotationStore.setError('페이지를 불러오는 데 실패했습니다.')
      }
    } finally {
      annotationStore.setLoading(false)
    }
  }

  async function handleSave() {
    if (!params?.pageId || !annotationStore.annotationData) return
    saving = true
    try {
      await savePage(params.pageId, {
        annotation_data: annotationStore.annotationData,
      })
      annotationStore.markSaved()
      uiStore.showNotification('저장 완료', 'success')
    } catch {
      uiStore.showNotification('저장 실패', 'error')
    } finally {
      saving = false
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    // Ignore shortcuts when typing in input/textarea
    const tag = (e.target as HTMLElement)?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

    if (e.key === 's' && !e.ctrlKey && !e.metaKey) {
      canvasStore.setTool('select')
    } else if (e.key === 'd') {
      canvasStore.setTool('draw')
    } else if (e.key === 'h') {
      canvasStore.setTool('pan')
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
      if (annotationStore.selectedElementId !== null) {
        annotationStore.removeElement(annotationStore.selectedElementId)
      }
    } else if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      annotationStore.selectElement(null)
    }
  }

  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (annotationStore.isDirty) {
      e.preventDefault()
    }
  }

  $effect(() => {
    params.pageId
    untrack(() => loadPage())
  })

  $effect(() => {
    window.addEventListener('keydown', handleKeydown)
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('keydown', handleKeydown)
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  })
</script>

<div class="h-full flex flex-col">
  <Header title={pageData?.project_name ?? '레이블링'} showSave onsave={handleSave} {saving} />

  {#if pageData?.project_id}
    <nav class="h-9 bg-white border-b border-gray-200 px-4 flex items-center text-sm shrink-0">
      <a
        href="/projects/{pageData.project_id}"
        use:link
        class="text-gray-500 hover:text-primary-600 transition-colors flex items-center gap-1"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        {pageData.project_name ?? '프로젝트'}
      </a>
      <span class="mx-2 text-gray-300">/</span>
      <span class="text-gray-500">{pageData.document_filename ?? '문서'}</span>
      <span class="mx-2 text-gray-300">/</span>
      <span class="text-gray-900 font-medium">페이지 {pageData.page_no}</span>
    </nav>
  {/if}

  {#if annotationStore.isLoading}
    <div class="flex-1 flex items-center justify-center">
      <LoadingSpinner message="페이지 불러오는 중..." />
    </div>
  {:else if annotationStore.error}
    <div class="flex-1 flex items-center justify-center">
      <div class="bg-red-50/80 border border-red-200 rounded-xl p-6 text-center max-w-md">
        <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-red-100 flex items-center justify-center">
          <svg class="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <p class="text-red-700 mb-4 font-medium">{annotationStore.error}</p>
        <Button variant="secondary" onclick={loadPage}>다시 시도</Button>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex overflow-hidden">
      <!-- Left panel: Element list -->
      <div class="w-64 border-r border-gray-200/80 bg-white overflow-y-auto flex flex-col shadow-sm">
        <ElementList />
      </div>

      <!-- Center: Canvas area -->
      <div class="flex-1 relative bg-gray-100">
        <div class="absolute top-3 left-3 z-10 flex gap-2">
          <!-- Tool group -->
          <div class="flex bg-white/95 backdrop-blur-sm rounded-xl shadow-md border border-gray-200/80 p-1 gap-0.5">
            <button class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
              {canvasStore.toolMode === 'select' ? 'bg-primary-500 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'}"
              onclick={() => canvasStore.setTool('select')}>선택</button>
            <button class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
              {canvasStore.toolMode === 'draw' ? 'bg-primary-500 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'}"
              onclick={() => canvasStore.setTool('draw')}>그리기</button>
            <button class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
              {canvasStore.toolMode === 'pan' ? 'bg-primary-500 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'}"
              onclick={() => canvasStore.setTool('pan')}>이동</button>
          </div>
          <!-- Zoom group -->
          <div class="flex bg-white/95 backdrop-blur-sm rounded-xl shadow-md border border-gray-200/80 p-1 gap-0.5">
            <button class="px-2.5 py-1.5 text-xs font-medium rounded-lg text-gray-600 hover:bg-gray-100 transition-all"
              onclick={() => canvasStore.zoomIn()}>+</button>
            <button class="px-2.5 py-1.5 text-xs font-medium rounded-lg text-gray-600 hover:bg-gray-100 transition-all"
              onclick={() => canvasStore.zoomOut()}>-</button>
            <button class="px-2.5 py-1.5 text-xs font-medium rounded-lg text-gray-600 hover:bg-gray-100 transition-all"
              onclick={() => canvasStore.resetView()}>1:1</button>
          </div>
        </div>

        {#if pageData}
          <HybridViewer
            imageUrl={`${API_BASE}${pageData.image_url}`}
            width={pageData.width}
            height={pageData.height}
          />
        {:else}
          <div class="absolute inset-0 flex items-center justify-center">
            <p class="text-gray-400 text-sm">이미지를 불러오는 중...</p>
          </div>
        {/if}
      </div>

      <!-- Right panel: Sidebar -->
      <Sidebar />
    </div>
  {/if}
</div>
