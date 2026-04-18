<script lang="ts">
  import { acceptExtraction, forceAcceptExtraction } from '$lib/api/pages'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import type { AnnotationData } from '$lib/types/omnidocbench'
  import { isImageBlock, isTextBlock } from '$lib/types/element-groups'

  import type { DocumentStatus } from '$lib/api/types'

  interface Props {
    pageId: string
    documentId: string
    autoExtractedData: AnnotationData | null
    documentStatus?: DocumentStatus
    pageExtracting?: boolean
    reExtractVersion?: number
    onAccepted: (data: AnnotationData) => void
    onReExtract: () => void
  }

  let {
    pageId,
    documentId,
    autoExtractedData,
    documentStatus,
    pageExtracting = false,
    reExtractVersion,
    onAccepted,
    onReExtract,
  }: Props = $props()

  let dismissed = $state(false)
  let loading = $state(false)
  let wasExtracting = $state(false)
  let lastSeenVersion = $state(0)

  let isExtracting = $derived(documentStatus === 'extracting' || pageExtracting)

  // Reset dismissed when extraction completes (extracting → ready)
  $effect(() => {
    if (isExtracting) {
      wasExtracting = true
    } else if (wasExtracting) {
      wasExtracting = false
      dismissed = false
    }
  })

  // Reset dismissed when reExtractVersion changes (handles pdfminer sync case)
  $effect(() => {
    const version = reExtractVersion ?? 0
    if (version > lastSeenVersion) {
      lastSeenVersion = version
      dismissed = false
    }
  })

  let hasAutoData = $derived(
    autoExtractedData !== null &&
      autoExtractedData.layout_dets &&
      autoExtractedData.layout_dets.length > 0,
  )

  let annotationEmpty = $derived(annotationStore.elements.length === 0)

  // Show accept/dismiss when auto data exists and no annotations
  let showAccept = $derived(hasAutoData && annotationEmpty && !dismissed)
  // Show force-accept only after an explicit re-extract (reExtractVersion > 0)
  let showForceAccept = $derived(
    hasAutoData && !annotationEmpty && !dismissed && (reExtractVersion ?? 0) > 0,
  )

  let canReExtract = $derived(
    documentStatus === 'ready' ||
      documentStatus === 'extraction_failed' ||
      (documentStatus !== 'extracting' && documentStatus !== undefined),
  )

  let showNoDataHint = $derived(
    !hasAutoData &&
      annotationEmpty &&
      !isExtracting &&
      documentStatus !== undefined &&
      documentStatus !== 'extracting' &&
      !dismissed,
  )

  let textCount = $derived(
    autoExtractedData?.layout_dets?.filter((el) => isTextBlock(el)).length ?? 0,
  )

  let imageCount = $derived(
    autoExtractedData?.layout_dets?.filter((el) => isImageBlock(el)).length ?? 0,
  )

  let totalCount = $derived(autoExtractedData?.layout_dets?.length ?? 0)

  async function handleAccept() {
    loading = true
    try {
      const response = await acceptExtraction(pageId)
      onAccepted(response.annotation_data as AnnotationData)
      dismissed = true
      uiStore.showNotification('Automatic extraction results applied', 'success')
    } catch {
      uiStore.showNotification('Failed to accept automatic extraction', 'error')
    } finally {
      loading = false
    }
  }

  async function handleForceAccept() {
    loading = true
    try {
      const response = await forceAcceptExtraction(pageId)
      onAccepted(response.annotation_data as AnnotationData)
      dismissed = true
      uiStore.showNotification(
        'Automatic extraction results applied (existing annotations replaced)',
        'success',
      )
    } catch {
      uiStore.showNotification('Failed to accept automatic extraction', 'error')
    } finally {
      loading = false
    }
  }

  function handleDismiss() {
    dismissed = true
  }
</script>

<!-- Re-extract button (always visible when re-extraction is possible) -->
{#if canReExtract && !isExtracting}
  <div class="mx-3 mt-3">
    <button
      type="button"
      class="border-border bg-card hover:bg-accent text-foreground flex w-full items-center justify-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-colors"
      onclick={onReExtract}
    >
      <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M2.985 19.644l3.181-3.183"
        />
      </svg>
      Rescan All
    </button>
  </div>
{/if}

{#if isExtracting}
  <div
    class="mx-3 mt-3 rounded-lg border border-amber-200 bg-amber-50/80 p-3 shadow-sm dark:border-amber-800 dark:bg-amber-950/30"
  >
    <div class="flex items-center gap-2">
      <svg
        class="h-4 w-4 animate-spin text-amber-600 dark:text-amber-400"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <div>
        <p class="text-sm font-medium text-amber-900 dark:text-amber-200">OCR extraction in progress...</p>
        <p class="mt-0.5 text-xs text-amber-700 dark:text-amber-300">
          Results will appear automatically after structure analysis completes.
        </p>
      </div>
    </div>
  </div>
{:else if showNoDataHint}
  <div class="border-border bg-muted/50 mx-3 mt-3 rounded-lg border p-3">
    <div class="flex items-start gap-2">
      <svg
        class="text-muted-foreground mt-0.5 h-4 w-4 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <div>
        <p class="text-muted-foreground text-xs">No automatic extraction results.</p>
        <p class="text-muted-foreground mt-0.5 text-xs">
          Add regions manually with the draw tool, or <a
            href="/settings"
            class="text-primary hover:underline">OCR Settings</a
          >.
        </p>
      </div>
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground shrink-0 p-0.5 text-lg leading-none"
        onclick={handleDismiss}
        aria-label="Close"
      >
        &times;
      </button>
    </div>
  </div>
{:else if showAccept}
  <div
    class="mx-3 mt-3 rounded-lg border border-blue-200 bg-blue-50/80 p-3 shadow-sm dark:border-blue-800 dark:bg-blue-950/30"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0 flex-1">
        <p class="text-sm font-medium text-blue-900 dark:text-blue-200">
          Automatic extraction results available
        </p>
        <p class="mt-1 text-xs text-blue-700 dark:text-blue-300">
          Text {textCount}, images {imageCount} - total {totalCount} elements
        </p>
      </div>
      <button
        type="button"
        class="p-0.5 text-lg leading-none text-blue-400 hover:text-blue-600 dark:text-blue-500 dark:hover:text-blue-400"
        onclick={handleDismiss}
        aria-label="Close"
      >
        &times;
      </button>
    </div>
    <div class="mt-2.5 flex gap-2">
      <button
        type="button"
        class="rounded-md bg-blue-600 px-3 py-1.5 text-xs
          font-medium text-white transition-colors
          hover:bg-blue-700 disabled:cursor-not-allowed
          disabled:opacity-50"
        onclick={handleAccept}
        disabled={loading}
      >
        {loading ? 'Applying...' : 'Accept'}
      </button>
      <button
        type="button"
        class="bg-card text-muted-foreground border-border hover:bg-accent rounded-md
          border px-3 py-1.5 text-xs
          font-medium transition-colors"
        onclick={handleDismiss}
      >
        Ignore
      </button>
    </div>
  </div>
{:else if showForceAccept}
  <div
    class="mx-3 mt-3 rounded-lg border border-violet-200 bg-violet-50/80 p-3 shadow-sm dark:border-violet-800 dark:bg-violet-950/30"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0 flex-1">
        <p class="text-sm font-medium text-violet-900 dark:text-violet-200">
          New extraction results available
        </p>
        <p class="mt-1 text-xs text-violet-700 dark:text-violet-300">
          Text {textCount}, images {imageCount} - total {totalCount} elements
        </p>
        <p class="mt-1 text-xs font-medium text-violet-600 dark:text-violet-400">
          Accepting will replace existing annotations.
        </p>
      </div>
      <button
        type="button"
        class="p-0.5 text-lg leading-none text-violet-400 hover:text-violet-600 dark:text-violet-500 dark:hover:text-violet-400"
        onclick={handleDismiss}
        aria-label="Close"
      >
        &times;
      </button>
    </div>
    <div class="mt-2.5 flex gap-2">
      <button
        type="button"
        class="rounded-md bg-violet-600 px-3 py-1.5 text-xs
          font-medium text-white transition-colors
          hover:bg-violet-700 disabled:cursor-not-allowed
          disabled:opacity-50"
        onclick={handleForceAccept}
        disabled={loading}
      >
        {loading ? 'Applying...' : 'Accept (Replace)'}
      </button>
      <button
        type="button"
        class="bg-card text-muted-foreground border-border hover:bg-accent rounded-md
          border px-3 py-1.5 text-xs
          font-medium transition-colors"
        onclick={handleDismiss}
      >
        Ignore
      </button>
    </div>
  </div>
{/if}
