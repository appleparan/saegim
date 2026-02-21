<script lang="ts">
  import { link, push } from 'svelte-spa-router'
  import Header from '$lib/components/layout/Header.svelte'
  import Sidebar from '$lib/components/layout/Sidebar.svelte'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { Button } from '$lib/components/ui/button'
  import HybridViewer from '$lib/components/canvas/HybridViewer.svelte'
  import ElementList from '$lib/components/panels/ElementList.svelte'
  import ExtractionPreview from '$lib/components/panels/ExtractionPreview.svelte'
  import PageNavigator from '$lib/components/panels/PageNavigator.svelte'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { pdfStore } from '$lib/stores/pdf.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import { untrack } from 'svelte'
  import { getPage, savePage } from '$lib/api/pages'
  import { listPages } from '$lib/api/documents'
  import { API_BASE, NetworkError } from '$lib/api/client'
  import type { PageResponse, PageSummary } from '$lib/api/types'
  import type { AnnotationData } from '$lib/types/omnidocbench'
  import type { PDFPageProxy } from 'pdfjs-dist'

  let { params }: { params: { pageId: string } } = $props()

  let pageData = $state<PageResponse | null>(null)
  let currentPageProxy = $state<PDFPageProxy | null>(null)
  let documentPages = $state<readonly PageSummary[]>([])
  let saving = $state(false)

  async function loadPage() {
    if (!params?.pageId) return
    annotationStore.setLoading(true)
    annotationStore.setError(null)
    currentPageProxy = null
    try {
      const data = await getPage(params.pageId)
      pageData = data
      annotationStore.load(params.pageId, data.annotation_data)
      canvasStore.setImageDimensions(data.width, data.height)

      // Load page list for document navigation (non-blocking)
      listPages(data.document_id).then((pages) => {
        documentPages = pages
      }).catch(() => {
        documentPages = []
      })

      // Load PDF for vector rendering if available
      if (data.pdf_url) {
        try {
          await pdfStore.loadDocument(`${API_BASE}${data.pdf_url}`)
          currentPageProxy = await pdfStore.getPage(data.page_no)
        } catch {
          // PDF load failed — fall back to image rendering silently
          currentPageProxy = null
        }
      }
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

  function navigateToAdjacentPage(direction: -1 | 1): void {
    if (documentPages.length <= 1 || !params?.pageId) return
    const currentIndex = documentPages.findIndex((p) => p.id === params.pageId)
    if (currentIndex < 0) return
    const targetIndex = currentIndex + direction
    if (targetIndex >= 0 && targetIndex < documentPages.length) {
      push(`/label/${documentPages[targetIndex].id}`)
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
    } else if (e.key === '[') {
      navigateToAdjacentPage(-1)
    } else if (e.key === ']') {
      navigateToAdjacentPage(1)
    }
  }

  function handleExtractionAccepted(data: AnnotationData) {
    if (params?.pageId) {
      annotationStore.load(params.pageId, data)
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
      pdfStore.destroy()
    }
  })
</script>

<div class="h-full flex flex-col">
  <Header title={pageData?.project_name ?? '레이블링'} showSave onsave={handleSave} {saving} />

  {#if pageData?.project_id}
    <nav class="h-9 bg-card border-b border-border px-4 flex items-center text-sm shrink-0">
      <a
        href="/projects/{pageData.project_id}"
        use:link
        class="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        {pageData.project_name ?? '프로젝트'}
      </a>
      <span class="mx-2 text-muted-foreground">/</span>
      <span class="text-muted-foreground">{pageData.document_filename ?? '문서'}</span>
      <span class="mx-2 text-muted-foreground">/</span>
      <span class="text-foreground font-medium">페이지 {pageData.page_no}</span>
    </nav>
  {/if}

  {#if annotationStore.isLoading}
    <div class="flex-1 flex items-center justify-center">
      <LoadingSpinner message="페이지 불러오는 중..." />
    </div>
  {:else if annotationStore.error}
    <div class="flex-1 flex items-center justify-center">
      <div class="bg-destructive/10 dark:bg-destructive/20 border border-destructive/30 rounded-xl p-6 text-center max-w-md">
        <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-destructive/20 flex items-center justify-center">
          <svg class="w-6 h-6 text-destructive" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <p class="text-destructive mb-4 font-medium">{annotationStore.error}</p>
        <Button variant="outline" onclick={loadPage}>다시 시도</Button>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex overflow-hidden">
      <!-- Left panel: Page navigator + Element list + extraction preview -->
      <div class="w-64 border-r border-border bg-card overflow-y-auto flex flex-col shadow-sm">
        {#if documentPages.length > 1}
          <PageNavigator
            pages={documentPages}
            currentPageId={params.pageId}
          />
        {/if}
        {#if pageData}
          <ExtractionPreview
            pageId={params.pageId}
            autoExtractedData={pageData.auto_extracted_data}
            onAccepted={handleExtractionAccepted}
          />
        {/if}
        <ElementList />
      </div>

      <!-- Center: Canvas area -->
      <div class="flex-1 relative bg-muted">
        <div class="absolute top-3 left-3 z-30 flex gap-2">
          <!-- Tool group -->
          <div class="flex bg-card/95 backdrop-blur-sm rounded-xl shadow-md border border-border p-1 gap-0.5">
            <button class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
              {canvasStore.toolMode === 'select' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('select')}>선택</button>
            <button class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
              {canvasStore.toolMode === 'draw' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('draw')}>그리기</button>
            <button class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
              {canvasStore.toolMode === 'pan' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('pan')}>이동</button>
          </div>
          <!-- Zoom group -->
          <div class="flex bg-card/95 backdrop-blur-sm rounded-xl shadow-md border border-border p-1 gap-0.5">
            <button class="px-2.5 py-1.5 text-xs font-medium rounded-lg text-muted-foreground hover:bg-accent transition-all"
              onclick={() => canvasStore.zoomIn()}>+</button>
            <button class="px-2.5 py-1.5 text-xs font-medium rounded-lg text-muted-foreground hover:bg-accent transition-all"
              onclick={() => canvasStore.zoomOut()}>-</button>
            <button class="px-2.5 py-1.5 text-xs font-medium rounded-lg text-muted-foreground hover:bg-accent transition-all"
              onclick={() => canvasStore.resetView()}>1:1</button>
          </div>
        </div>

        {#if pageData}
          <HybridViewer
            pageProxy={currentPageProxy ?? undefined}
            imageUrl={`${API_BASE}${pageData.image_url}`}
            width={pageData.width}
            height={pageData.height}
          />
        {:else}
          <div class="absolute inset-0 flex items-center justify-center">
            <p class="text-muted-foreground text-sm">이미지를 불러오는 중...</p>
          </div>
        {/if}
      </div>

      <!-- Right panel: Sidebar -->
      <Sidebar />
    </div>
  {/if}
</div>
