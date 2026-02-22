<script lang="ts">
  import { page } from '$app/state'
  import { goto } from '$app/navigation'
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

  let pageData = $state<PageResponse | null>(null)
  let currentPageProxy = $state<PDFPageProxy | null>(null)
  let documentPages = $state<readonly PageSummary[]>([])
  let saving = $state(false)

  let renderMode = $derived<'pdfjs' | 'image' | 'none'>(
    currentPageProxy ? 'pdfjs' : pageData ? 'image' : 'none',
  )

  async function loadPage() {
    const pageId = page.params.pageId
    if (!pageId) return
    annotationStore.setLoading(true)
    annotationStore.setError(null)
    currentPageProxy = null
    try {
      const data = await getPage(pageId)
      pageData = data
      annotationStore.load(pageId, data.annotation_data)
      canvasStore.setImageDimensions(data.width, data.height)

      // Load page list for document navigation (non-blocking)
      listPages(data.document_id).then((pages) => {
        documentPages = pages
      }).catch(() => {
        documentPages = []
      })

      // Load PDF for vector rendering if available
      if (data.pdf_url && data.pdf_url.length > 0) {
        try {
          await pdfStore.loadDocument(`${API_BASE}${data.pdf_url}`)
          currentPageProxy = await pdfStore.getPage(data.page_no)
        } catch (pdfErr) {
          console.warn('[saegim] PDF.js load failed, falling back to image:', pdfErr)
          currentPageProxy = null
        }
      } else {
        console.warn('[saegim] No pdf_url available, using image rendering')
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
    const pageId = page.params.pageId
    if (!pageId || !annotationStore.annotationData) return
    saving = true
    try {
      await savePage(pageId, {
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
    const pageId = page.params.pageId
    if (documentPages.length <= 1 || !pageId) return
    const currentIndex = documentPages.findIndex((p) => p.id === pageId)
    if (currentIndex < 0) return
    const targetIndex = currentIndex + direction
    if (targetIndex >= 0 && targetIndex < documentPages.length) {
      goto(`/label/${documentPages[targetIndex].id}`)
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
    const pageId = page.params.pageId
    if (pageId) {
      annotationStore.load(pageId, data)
    }
  }

  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (annotationStore.isDirty) {
      e.preventDefault()
    }
  }

  $effect(() => {
    page.params.pageId
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
            currentPageId={page.params.pageId!}
          />
        {/if}
        {#if pageData}
          <ExtractionPreview
            pageId={page.params.pageId!}
            autoExtractedData={pageData.auto_extracted_data}
            onAccepted={handleExtractionAccepted}
          />
        {/if}
        <ElementList />
      </div>

      <!-- Center: Canvas area -->
      <div class="flex-1 relative bg-muted">
        <div class="absolute top-3 left-3 z-30 flex">
          <div class="flex items-center bg-card/95 backdrop-blur-sm rounded-xl shadow-md border border-border p-1 gap-0.5">
            <!-- Tool buttons -->
            <button
              class="p-1.5 rounded-lg transition-all
                {canvasStore.toolMode === 'select' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('select')}
              title="선택 (S)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.042 21.672L13.684 16.6m0 0l-2.51 2.225.569-9.47 5.227 7.917-3.286-.672zM12 2.25V4.5m5.834.166l-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243l-1.59-1.59" />
              </svg>
            </button>
            <button
              class="p-1.5 rounded-lg transition-all
                {canvasStore.toolMode === 'draw' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('draw')}
              title="그리기 (D)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
            </button>
            <button
              class="p-1.5 rounded-lg transition-all
                {canvasStore.toolMode === 'pan' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('pan')}
              title="이동 (H)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.05 4.575a1.575 1.575 0 10-3.15 0v3.15m3.15-3.15v-1.5a1.575 1.575 0 013.15 0v1.5m-3.15 0l-.075 5.925m3.225-5.925a1.575 1.575 0 013.15 0v1.5m-3.15-1.5v5.925m0-5.925a1.575 1.575 0 013.15 0v5.925m-3.15 0a7.007 7.007 0 01-.088.967m.088-.967a7.032 7.032 0 01-3.225 4.672l-.26.163a3.375 3.375 0 01-4.476-1.123l-.04-.068a6.685 6.685 0 01-.932-3.569V6.75a1.575 1.575 0 013.15 0v4.125" />
              </svg>
            </button>

            <!-- Separator -->
            <div class="w-px h-5 bg-border mx-0.5"></div>

            <!-- Zoom controls -->
            <button
              class="p-1.5 rounded-lg text-muted-foreground hover:bg-accent transition-all"
              onclick={() => canvasStore.zoomOut()}
              title="축소"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 12h-15" />
              </svg>
            </button>
            <button
              class="px-1.5 py-1 text-[11px] font-mono font-medium rounded-lg text-muted-foreground hover:bg-accent transition-all min-w-[3rem] text-center"
              onclick={() => canvasStore.resetView()}
              title="1:1 보기로 리셋"
            >
              {Math.round(canvasStore.scale * 100)}%
            </button>
            <button
              class="p-1.5 rounded-lg text-muted-foreground hover:bg-accent transition-all"
              onclick={() => canvasStore.zoomIn()}
              title="확대"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </button>
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

        <!-- Render mode indicator (dev) -->
        {#if renderMode !== 'none'}
          <div
            class="absolute bottom-3 right-3 z-30 px-2 py-1 text-[10px] font-mono rounded-md shadow-sm border
              {renderMode === 'pdfjs'
                ? 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 border-green-300 dark:border-green-700'
                : 'bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-700'}"
          >
            {renderMode === 'pdfjs' ? 'PDF.js' : 'Image'}
          </div>
        {/if}
      </div>

      <!-- Right panel: Sidebar -->
      <Sidebar />
    </div>
  {/if}
</div>
