<script lang="ts">
  import { page } from '$app/state'
  import Header from '$lib/components/layout/Header.svelte'
  import { Button } from '$lib/components/ui/button'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { getProject, getOcrConfig } from '$lib/api/projects'
  import { listDocuments, uploadDocument, deleteDocument, listPages } from '$lib/api/documents'
  import type {
    ProjectResponse,
    DocumentResponse,
    PageSummary,
    OcrConfigResponse,
    EngineType,
  } from '$lib/api/types'
  import { untrack } from 'svelte'
  import { NetworkError } from '$lib/api/client'

  const POLL_INTERVAL_MS = 5000

  let project = $state<ProjectResponse | null>(null)
  let ocrConfig = $state<OcrConfigResponse | null>(null)
  let documents = $state<readonly DocumentResponse[]>([])
  let documentPages = $state<Record<string, readonly PageSummary[]>>({})
  let isLoading = $state(true)
  let error = $state<string | null>(null)
  let isUploading = $state(false)
  let expandedDoc = $state<string | null>(null)
  let pollTimer = $state<ReturnType<typeof setInterval> | null>(null)

  const engineLabels: Record<EngineType, string> = {
    pdfminer: 'pdfminer',
    commercial_api: 'Gemini API',
    vllm: 'vLLM',
    split_pipeline: 'Docling + OCR',
  }

  let fileInput: HTMLInputElement
  let isDragOver = $state(false)
  let dragCounter = $state(0)

  let hasPendingDocs = $derived(
    documents.some((d) => d.status === 'processing' || d.status === 'extracting'),
  )

  function startPolling() {
    stopPolling()
    pollTimer = setInterval(async () => {
      const id = page.params.id
      if (!id) return
      try {
        const docs = await listDocuments(id)
        documents = docs
        if (!docs.some((d) => d.status === 'processing' || d.status === 'extracting')) {
          stopPolling()
        }
      } catch {
        // Polling failures are non-critical
      }
    }, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  $effect(() => {
    if (hasPendingDocs && !pollTimer) {
      startPolling()
    }
    return () => stopPolling()
  })

  async function loadData() {
    const id = page.params.id
    if (!id) return
    isLoading = true
    error = null
    try {
      const [proj, docs, config] = await Promise.all([
        getProject(id),
        listDocuments(id),
        getOcrConfig(id).catch(() => null),
      ])
      project = proj
      documents = docs
      ocrConfig = config
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
    const id = page.params.id
    if (!file || !id) return

    isUploading = true
    error = null
    try {
      const doc = await uploadDocument(id, file)
      documents = [...documents, doc]
    } catch {
      error = 'PDF 업로드에 실패했습니다.'
    } finally {
      isUploading = false
      target.value = ''
    }
  }

  function handleDragEnter(e: DragEvent) {
    e.preventDefault()
    dragCounter += 1
    if (e.dataTransfer?.types.includes('Files')) {
      isDragOver = true
    }
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault()
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'copy'
    }
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault()
    dragCounter -= 1
    if (dragCounter <= 0) {
      dragCounter = 0
      isDragOver = false
    }
  }

  async function handleDrop(e: DragEvent) {
    e.preventDefault()
    dragCounter = 0
    isDragOver = false

    const id = page.params.id
    if (!id || isUploading) return

    const files = e.dataTransfer?.files
    if (!files || files.length === 0) return

    const file = files[0]

    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      error = 'PDF 파일만 업로드할 수 있습니다.'
      return
    }

    isUploading = true
    error = null
    try {
      const doc = await uploadDocument(id, file)
      documents = [...documents, doc]
    } catch {
      error = 'PDF 업로드에 실패했습니다.'
    } finally {
      isUploading = false
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
    void page.params.id
    untrack(() => loadData())
  })

  $effect(() => {
    function preventDefaultDrop(e: DragEvent) {
      if (e.target instanceof HTMLElement && !e.target.closest('[data-dropzone]')) {
        e.preventDefault()
        if (e.dataTransfer) {
          e.dataTransfer.dropEffect = 'none'
        }
      }
    }
    window.addEventListener('dragover', preventDefaultDrop)
    window.addEventListener('drop', preventDefaultDrop)
    return () => {
      window.removeEventListener('dragover', preventDefaultDrop)
      window.removeEventListener('drop', preventDefaultDrop)
    }
  })
</script>

<div class="flex h-full flex-col">
  <Header title={project?.name ?? 'saegim'} />

  <div class="bg-background flex-1 overflow-y-auto p-8">
    <div
      class="relative mx-auto max-w-4xl"
      data-dropzone
      role="region"
      aria-label="PDF 업로드 영역"
      ondragenter={handleDragEnter}
      ondragover={handleDragOver}
      ondragleave={handleDragLeave}
      ondrop={handleDrop}
    >
      {#if isDragOver}
        <div
          class="border-primary/50 bg-primary/5 pointer-events-none absolute inset-0 z-40 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed"
        >
          <div class="bg-primary/10 mb-4 flex h-16 w-16 items-center justify-center rounded-2xl">
            <svg
              class="text-primary h-8 w-8"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
              />
            </svg>
          </div>
          <p class="text-primary text-lg font-medium">PDF 파일을 여기에 놓으세요</p>
          <p class="text-muted-foreground mt-1 text-sm">파일을 놓으면 바로 업로드됩니다</p>
        </div>
      {/if}

      <div class="mb-4">
        <a
          href="/"
          class="text-muted-foreground hover:text-primary flex w-fit items-center gap-1 text-sm transition-colors"
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
          프로젝트 목록
        </a>
      </div>

      <div class="mb-6 flex items-center justify-between">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-foreground text-2xl font-bold">{project?.name ?? '문서'}</h1>
            {#if ocrConfig}
              <a
                href="/projects/{page.params.id}/settings"
                class="bg-muted text-muted-foreground border-border hover:border-primary hover:text-primary inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors"
                title="OCR 엔진 설정"
              >
                {engineLabels[ocrConfig.engine_type] ?? ocrConfig.engine_type}
              </a>
            {/if}
          </div>
          {#if project?.description}
            <p class="text-muted-foreground mt-1 text-sm">{project.description}</p>
          {/if}
        </div>
        <div class="flex items-center gap-2">
          <a
            href="/projects/{page.params.id}/settings"
            class="text-muted-foreground hover:text-accent-foreground hover:bg-accent border-border inline-flex h-9
              w-9 items-center justify-center
              rounded-lg border transition-all"
            title="프로젝트 설정"
          >
            <svg
              class="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </a>
          <input
            type="file"
            accept=".pdf"
            class="hidden"
            bind:this={fileInput}
            onchange={handleUpload}
          />
          <Button variant="default" disabled={isUploading} onclick={() => fileInput.click()}>
            {isUploading ? '업로드 중...' : 'PDF 업로드'}
          </Button>
        </div>
      </div>

      {#if isLoading}
        <div class="py-12"><LoadingSpinner message="문서 불러오는 중..." /></div>
      {:else if error}
        <div
          class="bg-destructive/10 dark:bg-destructive/20 border-destructive/30 rounded-xl border p-6 text-center"
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
          <p class="text-destructive mb-4 font-medium">{error}</p>
          <Button variant="outline" onclick={loadData}>다시 시도</Button>
        </div>
      {:else if documents.length === 0}
        <div class="bg-muted border-border rounded-2xl border p-16 text-center">
          <div
            class="bg-primary/10 mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
          >
            <svg
              class="text-primary h-8 w-8"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
              />
            </svg>
          </div>
          <p class="text-muted-foreground mb-2 text-lg font-medium">아직 문서가 없습니다</p>
          <p class="text-muted-foreground mb-6 text-sm">
            PDF 파일을 업로드하여 레이블링을 시작하세요.
          </p>
          <Button variant="default" onclick={() => fileInput.click()}>PDF 업로드</Button>
        </div>
      {:else}
        <div class="space-y-3">
          {#each documents as doc (doc.id)}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div class="card-modern overflow-hidden">
              <div
                class="hover:bg-accent w-full cursor-pointer p-5 text-left transition-colors"
                onclick={() => toggleDocPages(doc.id)}
              >
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-foreground font-medium">{doc.filename}</h3>
                    <div class="mt-1.5 flex items-center gap-2">
                      <span class="text-muted-foreground text-sm">{doc.total_pages}페이지</span>
                      <span
                        class="badge
                        {doc.status === 'ready'
                          ? 'border border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300'
                          : doc.status === 'processing'
                            ? 'border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300'
                            : doc.status === 'extracting'
                              ? 'border border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-300'
                              : doc.status === 'error' || doc.status === 'extraction_failed'
                                ? 'border border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300'
                                : 'bg-muted text-muted-foreground border-border border'}"
                      >
                        {doc.status === 'ready'
                          ? '준비됨'
                          : doc.status === 'processing'
                            ? '처리 중'
                            : doc.status === 'extracting'
                              ? '추출 중'
                              : doc.status === 'error'
                                ? '오류'
                                : doc.status === 'extraction_failed'
                                  ? '추출 실패'
                                  : '업로드 중'}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <button
                      class="text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg px-2 py-1 text-xs transition-all"
                      onclick={(e) => handleDeleteDoc(e, doc.id)}
                    >
                      삭제
                    </button>
                    <svg
                      class="text-muted-foreground h-4 w-4 transition-transform {expandedDoc ===
                      doc.id
                        ? 'rotate-180'
                        : ''}"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {#if expandedDoc === doc.id}
                <div class="border-border bg-background border-t p-4">
                  {#if documentPages[doc.id]}
                    <div class="grid grid-cols-6 gap-2 sm:grid-cols-8">
                      {#each documentPages[doc.id] as docPage (docPage.id)}
                        <a
                          href="/label/{docPage.id}"
                          class="bg-card hover:border-primary-300 block rounded-lg border p-2.5 text-center transition-all hover:shadow-sm
                            {docPage.status === 'submitted'
                            ? 'border-border border-l-4 border-l-emerald-400'
                            : docPage.status === 'in_progress'
                              ? 'border-border border-l-4 border-l-blue-400'
                              : docPage.status === 'reviewed'
                                ? 'border-border border-l-4 border-l-violet-400'
                                : 'border-border'}"
                        >
                          <span class="text-foreground text-sm font-medium">{docPage.page_no}</span>
                          <span
                            class="mt-0.5 block text-xs
                            {docPage.status === 'submitted'
                              ? 'text-emerald-600 dark:text-emerald-400'
                              : docPage.status === 'in_progress'
                                ? 'text-blue-600 dark:text-blue-400'
                                : docPage.status === 'reviewed'
                                  ? 'text-violet-600 dark:text-violet-400'
                                  : 'text-muted-foreground'}"
                          >
                            {docPage.status === 'submitted'
                              ? '완료'
                              : docPage.status === 'in_progress'
                                ? '진행 중'
                                : docPage.status === 'reviewed'
                                  ? '검토됨'
                                  : '대기'}
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
