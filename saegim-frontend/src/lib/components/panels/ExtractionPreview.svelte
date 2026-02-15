<script lang="ts">
  import { acceptExtraction } from '$lib/api/pages'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import type { AnnotationData } from '$lib/types/omnidocbench'
  import { isImageBlock, isTextBlock } from '$lib/types/element-groups'

  interface Props {
    pageId: string
    autoExtractedData: AnnotationData | null
    onAccepted: (data: AnnotationData) => void
  }

  let { pageId, autoExtractedData, onAccepted }: Props = $props()

  let dismissed = $state(false)
  let loading = $state(false)

  let hasAutoData = $derived(
    autoExtractedData !== null &&
      autoExtractedData.layout_dets &&
      autoExtractedData.layout_dets.length > 0,
  )

  let annotationEmpty = $derived(annotationStore.elements.length === 0)

  let visible = $derived(hasAutoData && annotationEmpty && !dismissed)

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

{#if visible}
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
