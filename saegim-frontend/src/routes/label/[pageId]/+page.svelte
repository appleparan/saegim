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
  import { autosaveStore } from '$lib/stores/autosave.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { pdfStore } from '$lib/stores/pdf.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import { untrack } from 'svelte'
  import { getPage, savePage, submitPage, extractElementText } from '$lib/api/pages'
  import { authStore } from '$lib/stores/auth.svelte'
  import Lock from '@lucide/svelte/icons/lock'
  import type { PageStatus } from '$lib/api/types'
  import { listPages, getDocumentStatus, reExtractDocument } from '$lib/api/documents'
  import { getOcrConfig, getAvailableEngines } from '$lib/api/projects'
  import { ApiError, NetworkError } from '$lib/api/client'
  import type {
    AvailableEngine,
    DocumentStatus,
    OcrConfigResponse,
    PageResponse,
    PageSummary,
  } from '$lib/api/types'
  import type { AnnotationData } from '$lib/types/omnidocbench'
  import type { PDFPageProxy } from 'pdfjs-dist'
  function getDefaultEngineName(config: OcrConfigResponse): string {
    if (!config.default_engine_id) return 'pdfminer'
    const engine = config.engines[config.default_engine_id]
    return engine?.name ?? config.default_engine_id
  }
  import { resolveBackendAssetUrl, resolvePdfUrl } from '$lib/utils/url'

  let pageData = $state<PageResponse | null>(null)
  let ocrConfig = $state<OcrConfigResponse | null>(null)
  let availableEngines = $state<readonly AvailableEngine[]>([])
  let currentPageProxy = $state<PDFPageProxy | null>(null)
  let documentPages = $state<readonly PageSummary[]>([])
  let documentStatus = $state<DocumentStatus | undefined>(undefined)
  let reExtractVersion = $state(0)
  let imageUrl = $state('')
  let saving = $state(false)
  let submitting = $state(false)
  let shortcutHelpOpen = $state(false)
  let statusPollTimer = $state<ReturnType<typeof setInterval> | null>(null)

  const statusColors: Record<PageStatus, string> = {
    pending:
      'border border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900/30 dark:text-zinc-300',
    in_progress:
      'border border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-300',
    submitted:
      'border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300',
    reviewed:
      'border border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300',
  }

  const statusLabels: Record<PageStatus, string> = {
    pending: '대기',
    in_progress: '진행중',
    submitted: '제출됨',
    reviewed: '검토완료',
  }

  let isLockedByOther = $derived(
    pageData?.assigned_to != null &&
      pageData.assigned_to !== authStore.user?.id,
  )

  let canSubmit = $derived(
    pageData?.status === 'in_progress' &&
      pageData?.assigned_to === authStore.user?.id,
  )

  let renderMode = $derived<'pdfjs' | 'image' | 'none'>(
    currentPageProxy ? 'pdfjs' : pageData ? 'image' : 'none',
  )

  async function loadPage() {
    const pageId = page.params.pageId
    if (!pageId) return
    annotationStore.setLoading(true)
    annotationStore.setError(null)
    currentPageProxy = null
    imageUrl = ''
    try {
      const data = await getPage(pageId)
      pageData = data
      annotationStore.load(pageId, data.annotation_data)
      canvasStore.setImageDimensions(data.width, data.height)
      imageUrl = resolveBackendAssetUrl(data.image_url)

      // Load OCR config and available engines (non-blocking)
      if (data.project_id) {
        getOcrConfig(data.project_id)
          .then((config) => {
            ocrConfig = config
          })
          .catch(() => {
            ocrConfig = null
          })
        getAvailableEngines(data.project_id)
          .then((result) => {
            availableEngines = result.engines
          })
          .catch(() => {
            availableEngines = []
          })
      }

      // Load page list and document status (non-blocking)
      listPages(data.document_id)
        .then((pages) => {
          documentPages = pages
        })
        .catch(() => {
          documentPages = []
        })
      getDocumentStatus(data.document_id)
        .then((status) => {
          documentStatus = status.status
          if (status.status === 'extracting') {
            startStatusPolling(data.document_id)
          }
        })
        .catch(() => {
          documentStatus = undefined
        })

      // Load PDF for vector rendering if available
      const pdfDocUrl = resolvePdfUrl(data.pdf_url, data.pdf_path)
      if (pdfDocUrl) {
        try {
          await pdfStore.loadDocument(pdfDocUrl)
          currentPageProxy = await pdfStore.getPage(data.page_no)
        } catch (pdfErr) {
          console.warn('[saegim] PDF.js load failed, falling back to image:', pdfErr)
          currentPageProxy = null
        }
      } else {
        console.warn('[saegim] No pdf_url/pdf_path available, using image rendering')
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

  async function handleAutoSave() {
    const pageId = page.params.pageId
    if (!pageId || !annotationStore.annotationData) return
    if (!annotationStore.isDirty || saving || autosaveStore.isSaving) return
    autosaveStore.markSaving()
    try {
      await savePage(pageId, {
        annotation_data: annotationStore.annotationData,
      })
      annotationStore.markSaved()
      autosaveStore.markSaved()
    } catch {
      autosaveStore.markSaveFailed()
      uiStore.showNotification('자동 저장 실패', 'error')
    }
  }

  async function handleSubmit() {
    const pageId = page.params.pageId
    if (!pageId) return
    if (!confirm('이 페이지를 검수 제출하시겠습니까?')) return
    submitting = true
    try {
      const updated = await submitPage(pageId)
      pageData = updated
      uiStore.showNotification('검수 제출 완료', 'success')
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        uiStore.showNotification('제출할 수 없는 상태입니다', 'error')
      } else {
        uiStore.showNotification('제출에 실패했습니다', 'error')
      }
    } finally {
      submitting = false
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
    // Ignore shortcuts when typing in input/textarea/contenteditable
    const target = e.target as HTMLElement
    const tag = target?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target?.isContentEditable)
      return

    if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'z' || e.key === 'Z')) {
      e.preventDefault()
      annotationStore.redo()
    } else if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z')) {
      e.preventDefault()
      annotationStore.undo()
    } else if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      handleSave()
    } else if (e.key === '1') {
      canvasStore.setTool('select')
    } else if (e.key === '2') {
      canvasStore.setTool('draw')
    } else if (e.key === '3') {
      canvasStore.setTool('pan')
    } else if (e.key === 'x' || e.key === 'X') {
      if (annotationStore.selectedElementId !== null) {
        annotationStore.removeElement(annotationStore.selectedElementId)
      }
    } else if (e.key === 'r' || e.key === 'R') {
      canvasStore.toggleReadingOrder()
    } else if (e.key === 'Escape') {
      annotationStore.selectElement(null)
    } else if (e.key === 'q' || e.key === 'Q') {
      navigateToAdjacentPage(-1)
    } else if (e.key === 'e' || e.key === 'E') {
      navigateToAdjacentPage(1)
    } else if (e.key === '`') {
      shortcutHelpOpen = !shortcutHelpOpen
    }
  }

  function handleExtractionAccepted(data: AnnotationData) {
    const pageId = page.params.pageId
    if (pageId) {
      annotationStore.load(pageId, data)
    }
  }

  async function handleOcrRequest(annoId: number, engineId?: string) {
    const pageId = page.params.pageId
    if (!pageId) return
    const el = annotationStore.elements.find((e) => e.anno_id === annoId)
    if (!el) return
    try {
      const result = await extractElementText(pageId, [...el.poly], engineId)
      if (result.text) {
        annotationStore.updateElement(annoId, {
          text: result.text,
          ...(engineId ? { ocr_engine: engineId } : {}),
        })
        uiStore.showNotification('텍스트가 추출되었습니다', 'success')
      } else {
        uiStore.showNotification('텍스트를 찾지 못했습니다', 'info')
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        uiStore.showNotification('OCR 엔드포인트가 아직 준비되지 않았습니다', 'info')
      } else if (e instanceof ApiError && e.status === 503) {
        uiStore.showNotification(
          'OCR 엔진이 설정되지 않았습니다. 프로젝트 설정에서 OCR 엔진을 구성해주세요.',
          'info',
        )
      } else {
        uiStore.showNotification('텍스트 추출에 실패했습니다', 'error')
      }
    }
  }

  function stopStatusPolling() {
    if (statusPollTimer) {
      clearInterval(statusPollTimer)
      statusPollTimer = null
    }
  }

  function startStatusPolling(documentId: string) {
    stopStatusPolling()
    statusPollTimer = setInterval(async () => {
      try {
        const status = await getDocumentStatus(documentId)
        documentStatus = status.status
        if (status.status !== 'extracting') {
          stopStatusPolling()
          // Reload page data to get new auto_extracted_data
          const currentPageId = page.params.pageId
          if (currentPageId) {
            const data = await getPage(currentPageId)
            pageData = data
          }
          reExtractVersion++
        }
      } catch {
        // Polling failures are non-critical
      }
    }, 3000)
  }

  async function handleReExtract() {
    if (!pageData?.document_id) return
    if (!confirm('현재 OCR 엔진으로 전체 페이지를 재추출하시겠습니까?')) return
    try {
      const result = await reExtractDocument(pageData.document_id)
      documentStatus = result.status
      if (result.status === 'extracting') {
        startStatusPolling(pageData.document_id)
      } else if (result.status === 'ready') {
        // Synchronous extraction completed (e.g. pdfminer), reload page data
        const currentPageId = page.params.pageId
        if (currentPageId) {
          const data = await getPage(currentPageId)
          pageData = data
        }
        reExtractVersion++
      }
      uiStore.showNotification('재추출이 시작되었습니다', 'success')
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        uiStore.showNotification('이미 추출이 진행 중입니다', 'info')
      } else {
        uiStore.showNotification('재추출 요청에 실패했습니다', 'error')
      }
    }
  }

  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (annotationStore.isDirty) {
      e.preventDefault()
    }
  }

  $effect(() => {
    void page.params.pageId
    untrack(() => loadPage())
  })

  $effect(() => {
    window.addEventListener('keydown', handleKeydown)
    window.addEventListener('beforeunload', handleBeforeUnload)
    autosaveStore.init()
    return () => {
      window.removeEventListener('keydown', handleKeydown)
      window.removeEventListener('beforeunload', handleBeforeUnload)
      stopStatusPolling()
      pdfStore.destroy()
    }
  })

  // Auto-save interval: save every 30 seconds when enabled and dirty
  $effect(() => {
    if (!autosaveStore.enabled) return

    const intervalId = setInterval(() => {
      handleAutoSave()
    }, 30_000)

    return () => clearInterval(intervalId)
  })
</script>

<div class="flex h-full flex-col">
  <Header
    title={pageData?.project_name ?? '레이블링'}
    showSave
    showAutoSave
    onsave={handleSave}
    {saving}
    showShortcutHelp
    bind:shortcutHelpOpen
  />

  {#if pageData?.project_id}
    <nav class="bg-card border-border flex h-9 shrink-0 items-center border-b px-4 text-sm">
      <a
        href="/projects/{pageData.project_id}"
        class="text-muted-foreground hover:text-primary flex items-center gap-1 transition-colors"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        {pageData.project_name ?? '프로젝트'}
      </a>
      <span class="text-muted-foreground mx-2">/</span>
      <span class="text-muted-foreground">{pageData.document_filename ?? '문서'}</span>
      <span class="text-muted-foreground mx-2">/</span>
      <span class="text-foreground font-medium">페이지 {pageData.page_no}</span>
      <span class="badge ml-2 rounded-full px-2 py-0.5 text-xs font-medium {statusColors[pageData.status]}">
        {statusLabels[pageData.status]}
      </span>
      {#if isLockedByOther}
        <span
          class="ml-2 inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-xs text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300"
        >
          <Lock class="size-3" />
          다른 사용자 편집 중
        </span>
      {/if}
      {#if canSubmit}
        <button
          class="bg-primary text-primary-foreground hover:bg-primary/90 ml-2 rounded-lg px-3 py-0.5 text-xs font-medium shadow-sm transition-all disabled:cursor-not-allowed disabled:opacity-50"
          onclick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? '제출 중...' : '검수 제출'}
        </button>
      {/if}
      {#if ocrConfig}
        <a
          href="/projects/{pageData.project_id}/settings"
          class="bg-muted text-muted-foreground border-border hover:border-primary hover:text-primary ml-auto inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors"
          title="OCR 엔진 설정"
        >
          {getDefaultEngineName(ocrConfig)}
          <span class="text-muted-foreground/70 ml-1 text-[10px]">(기본)</span>
        </a>
      {/if}
    </nav>
  {/if}

  {#if annotationStore.isLoading}
    <div class="flex flex-1 items-center justify-center">
      <LoadingSpinner message="페이지 불러오는 중..." />
    </div>
  {:else if annotationStore.error}
    <div class="flex flex-1 items-center justify-center">
      <div
        class="bg-destructive/10 dark:bg-destructive/20 border-destructive/30 max-w-md rounded-xl border p-6 text-center"
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
        <p class="text-destructive mb-4 font-medium">{annotationStore.error}</p>
        <Button variant="outline" onclick={loadPage}>다시 시도</Button>
      </div>
    </div>
  {:else}
    <div class="flex flex-1 overflow-hidden">
      <!-- Left panel: Page navigator + Element list + extraction preview -->
      <div class="border-border bg-card flex w-64 flex-col border-r shadow-sm">
        {#if documentPages.length > 1}
          <PageNavigator pages={documentPages} currentPageId={page.params.pageId!} />
        {/if}
        {#if pageData}
          <ExtractionPreview
            pageId={page.params.pageId!}
            documentId={pageData.document_id}
            autoExtractedData={pageData.auto_extracted_data}
            {documentStatus}
            {reExtractVersion}
            onAccepted={handleExtractionAccepted}
            onReExtract={handleReExtract}
          />
        {/if}
        <div class="min-h-0 flex-1 overflow-y-auto">
          <ElementList />
        </div>
      </div>

      <!-- Center: Canvas area -->
      <div class="bg-muted relative flex-1">
        <div class="absolute top-3 left-3 z-30 flex">
          <div
            class="bg-card/95 border-border flex items-center gap-0.5 rounded-xl border p-1 shadow-md backdrop-blur-sm"
          >
            <!-- Tool buttons -->
            <button
              class="rounded-lg p-1.5 transition-all
                {canvasStore.toolMode === 'select'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('select')}
              title="선택 (1)"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M15.042 21.672L13.684 16.6m0 0l-2.51 2.225.569-9.47 5.227 7.917-3.286-.672zM12 2.25V4.5m5.834.166l-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243l-1.59-1.59"
                />
              </svg>
            </button>
            <button
              class="rounded-lg p-1.5 transition-all
                {canvasStore.toolMode === 'draw'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('draw')}
              title="그리기 (2)"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
                />
              </svg>
            </button>
            <button
              class="rounded-lg p-1.5 transition-all
                {canvasStore.toolMode === 'pan'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:bg-accent'}"
              onclick={() => canvasStore.setTool('pan')}
              title="이동 (3)"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M10.05 4.575a1.575 1.575 0 10-3.15 0v3.15m3.15-3.15v-1.5a1.575 1.575 0 013.15 0v1.5m-3.15 0l-.075 5.925m3.225-5.925a1.575 1.575 0 013.15 0v1.5m-3.15-1.5v5.925m0-5.925a1.575 1.575 0 013.15 0v5.925m-3.15 0a7.007 7.007 0 01-.088.967m.088-.967a7.032 7.032 0 01-3.225 4.672l-.26.163a3.375 3.375 0 01-4.476-1.123l-.04-.068a6.685 6.685 0 01-.932-3.569V6.75a1.575 1.575 0 013.15 0v4.125"
                />
              </svg>
            </button>

            <!-- Separator -->
            <div class="bg-border mx-0.5 h-5 w-px"></div>

            <!-- Zoom controls -->
            <button
              class="text-muted-foreground hover:bg-accent rounded-lg p-1.5 transition-all"
              onclick={() => canvasStore.zoomOut()}
              title="축소"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 12h-15" />
              </svg>
            </button>
            <button
              class="text-muted-foreground hover:bg-accent min-w-[3rem] rounded-lg px-1.5 py-1 text-center font-mono text-[11px] font-medium transition-all"
              onclick={() => canvasStore.resetView()}
              title="1:1 보기로 리셋"
            >
              {Math.round(canvasStore.scale * 100)}%
            </button>
            <button
              class="text-muted-foreground hover:bg-accent rounded-lg p-1.5 transition-all"
              onclick={() => canvasStore.zoomIn()}
              title="확대"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </button>
          </div>
        </div>

        {#if pageData}
          <HybridViewer
            pageProxy={currentPageProxy ?? undefined}
            {imageUrl}
            width={pageData.width}
            height={pageData.height}
            {availableEngines}
            onOcrRequest={handleOcrRequest}
          />
        {:else}
          <div class="absolute inset-0 flex items-center justify-center">
            <p class="text-muted-foreground text-sm">이미지를 불러오는 중...</p>
          </div>
        {/if}

        <!-- Render mode indicator (dev) -->
        {#if renderMode !== 'none'}
          <div
            class="absolute right-3 bottom-3 z-30 rounded-md border px-2 py-1 font-mono text-[10px] shadow-sm
              {renderMode === 'pdfjs'
              ? 'border-green-300 bg-green-100 text-green-700 dark:border-green-700 dark:bg-green-900/50 dark:text-green-300'
              : 'border-amber-300 bg-amber-100 text-amber-700 dark:border-amber-700 dark:bg-amber-900/50 dark:text-amber-300'}"
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
