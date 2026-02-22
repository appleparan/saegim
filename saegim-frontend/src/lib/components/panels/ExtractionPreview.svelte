<script lang="ts">
  import { acceptExtraction } from '$lib/api/pages'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import type { AnnotationData } from '$lib/types/omnidocbench'
  import { isImageBlock, isTextBlock } from '$lib/types/element-groups'

  import type { DocumentStatus } from '$lib/api/types'

  interface Props {
    pageId: string
    autoExtractedData: AnnotationData | null
    documentStatus?: DocumentStatus
    onAccepted: (data: AnnotationData) => void
  }

  let { pageId, autoExtractedData, documentStatus, onAccepted }: Props = $props()

  let dismissed = $state(false)
  let loading = $state(false)

  let isExtracting = $derived(documentStatus === 'extracting')

  let hasAutoData = $derived(
    autoExtractedData !== null &&
      autoExtractedData.layout_dets &&
      autoExtractedData.layout_dets.length > 0,
  )

  let annotationEmpty = $derived(annotationStore.elements.length === 0)

  let visible = $derived((hasAutoData && annotationEmpty && !dismissed) || isExtracting)

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
      uiStore.showNotification('자동 추출 결과가 반영되었습니다', 'success')
    } catch {
      uiStore.showNotification('자동 추출 수락에 실패했습니다', 'error')
    } finally {
      loading = false
    }
  }

  function handleDismiss() {
    dismissed = true
  }
</script>

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
        <p class="text-sm font-medium text-amber-900 dark:text-amber-200">OCR 추출 진행 중...</p>
        <p class="mt-0.5 text-xs text-amber-700 dark:text-amber-300">
          구조 분석이 완료되면 자동으로 결과가 표시됩니다.
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
        <p class="text-muted-foreground text-xs">자동 추출 결과가 없습니다.</p>
        <p class="text-muted-foreground mt-0.5 text-xs">
          그리기 도구로 직접 영역을 추가하거나, <a
            href="/settings"
            class="text-primary hover:underline">OCR 설정</a
          >을 확인하세요.
        </p>
      </div>
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground shrink-0 p-0.5 text-lg leading-none"
        onclick={handleDismiss}
        aria-label="닫기"
      >
        &times;
      </button>
    </div>
  </div>
{:else if visible}
  <div
    class="mx-3 mt-3 rounded-lg border border-blue-200 bg-blue-50/80 p-3 shadow-sm dark:border-blue-800 dark:bg-blue-950/30"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0 flex-1">
        <p class="text-sm font-medium text-blue-900 dark:text-blue-200">
          자동 추출 결과가 있습니다
        </p>
        <p class="mt-1 text-xs text-blue-700 dark:text-blue-300">
          텍스트 {textCount}개, 이미지 {imageCount}개 — 총 {totalCount}개 요소
        </p>
      </div>
      <button
        type="button"
        class="p-0.5 text-lg leading-none text-blue-400 hover:text-blue-600 dark:text-blue-500 dark:hover:text-blue-400"
        onclick={handleDismiss}
        aria-label="닫기"
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
        {loading ? '반영 중...' : '수락'}
      </button>
      <button
        type="button"
        class="bg-card text-muted-foreground border-border hover:bg-accent rounded-md
          border px-3 py-1.5 text-xs
          font-medium transition-colors"
        onclick={handleDismiss}
      >
        무시
      </button>
    </div>
  </div>
{/if}
