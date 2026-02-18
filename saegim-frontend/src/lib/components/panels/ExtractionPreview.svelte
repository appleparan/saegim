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

  let textCount = $derived(
    autoExtractedData?.layout_dets?.filter((el) => isTextBlock(el)) .length ?? 0,
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
    class="mx-3 mt-3 p-3 rounded-lg border border-amber-200 bg-amber-50/80 shadow-sm"
  >
    <div class="flex items-center gap-2">
      <svg class="w-4 h-4 text-amber-600 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      <div>
        <p class="text-sm font-medium text-amber-900">OCR 추출 진행 중...</p>
        <p class="text-xs text-amber-700 mt-0.5">구조 분석이 완료되면 자동으로 결과가 표시됩니다.</p>
      </div>
    </div>
  </div>
{:else if visible}
  <div
    class="mx-3 mt-3 p-3 rounded-lg border border-blue-200 bg-blue-50/80 shadow-sm"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-blue-900">
          자동 추출 결과가 있습니다
        </p>
        <p class="text-xs text-blue-700 mt-1">
          텍스트 {textCount}개, 이미지 {imageCount}개 — 총 {totalCount}개 요소
        </p>
      </div>
      <button
        type="button"
        class="text-blue-400 hover:text-blue-600 text-lg leading-none p-0.5"
        onclick={handleDismiss}
        aria-label="닫기"
      >
        &times;
      </button>
    </div>
    <div class="flex gap-2 mt-2.5">
      <button
        type="button"
        class="px-3 py-1.5 text-xs font-medium rounded-md
          bg-blue-600 text-white hover:bg-blue-700
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-colors"
        onclick={handleAccept}
        disabled={loading}
      >
        {loading ? '반영 중...' : '수락'}
      </button>
      <button
        type="button"
        class="px-3 py-1.5 text-xs font-medium rounded-md
          bg-white text-gray-600 border border-gray-200
          hover:bg-gray-50 transition-colors"
        onclick={handleDismiss}
      >
        무시
      </button>
    </div>
  </div>
{/if}
