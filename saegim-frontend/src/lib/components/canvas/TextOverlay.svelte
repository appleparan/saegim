<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { isTextBlock } from '$lib/types/element-groups'
  import { polyToRect, rectToPoly } from '$lib/utils/bbox'
  import { estimateFontSize } from '$lib/utils/text-layout'
  import { findOverlappingBbox, selectionToImageRect } from '$lib/utils/text-selection'

  interface Props {
    /** Controls whether the text overlay accepts pointer events. */
    pointerEvents: 'auto' | 'none'
  }

  let { pointerEvents }: Props = $props()

  let textElements = $derived(annotationStore.elements.filter(isTextBlock))

  // --- Text selection → bbox mapping ---
  let transformContainerEl: HTMLDivElement
  let showCreateBbox = $state(false)
  let createBboxRect = $state<{ x: number; y: number; width: number; height: number } | null>(null)

  function handleSelectionChange(): void {
    const selection = document.getSelection()
    if (!selection || !transformContainerEl) {
      showCreateBbox = false
      createBboxRect = null
      return
    }

    const imageRect = selectionToImageRect(
      selection,
      transformContainerEl,
      canvasStore.offsetX,
      canvasStore.offsetY,
      canvasStore.scale,
    )

    if (!imageRect) {
      showCreateBbox = false
      createBboxRect = null
      return
    }

    // Try to find an overlapping existing bbox
    const matchedId = findOverlappingBbox(imageRect, annotationStore.elements)
    if (matchedId !== null) {
      annotationStore.selectElement(matchedId)
      showCreateBbox = false
      createBboxRect = null
    } else {
      // Show "create bbox" option
      createBboxRect = imageRect
      showCreateBbox = true
    }
  }

  function handleCreateBbox(): void {
    if (!createBboxRect) return
    const poly = rectToPoly(createBboxRect)
    const selectedText = document.getSelection()?.toString() ?? ''
    const annoId = annotationStore.addElement('text_block', poly)
    if (annoId >= 0 && selectedText) {
      annotationStore.updateElement(annoId, { text: selectedText })
    }
    showCreateBbox = false
    createBboxRect = null
    document.getSelection()?.removeAllRanges()
  }

  function dismissCreateBbox(): void {
    showCreateBbox = false
    createBboxRect = null
  }

  $effect(() => {
    document.addEventListener('selectionchange', handleSelectionChange)
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange)
    }
  })
</script>

<div class="absolute inset-0 overflow-hidden" style="z-index: 20; pointer-events: {pointerEvents};">
  <div
    bind:this={transformContainerEl}
    style="
      transform-origin: 0 0;
      transform: translate({canvasStore.offsetX}px, {canvasStore.offsetY}px) scale({canvasStore.scale});
      position: absolute;
      width: {canvasStore.imageWidth}px;
      height: {canvasStore.imageHeight}px;
    "
  >
    {#each textElements as el (el.anno_id)}
      {@const rect = polyToRect(el.poly)}
      {@const fontSize = estimateFontSize(el.poly)}
      <div
        role="textbox"
        tabindex="-1"
        style="
          position: absolute;
          left: {rect.x}px;
          top: {rect.y}px;
          width: {rect.width}px;
          height: {rect.height}px;
          font-size: {fontSize}px;
          line-height: 1.2;
          color: transparent;
          user-select: text;
          cursor: text;
          overflow: hidden;
          border: 1px solid transparent;
          transition: border-color 0.15s, background-color 0.15s;
        "
        class="hover:border-primary/50 hover:bg-primary/10"
        onclick={() => annotationStore.selectElement(el.anno_id)}
        onkeydown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            annotationStore.selectElement(el.anno_id)
          }
        }}
      >
        {el.text ?? ''}
      </div>
    {/each}
  </div>

  <!-- Floating "create bbox" button when text is selected without matching bbox -->
  {#if showCreateBbox && createBboxRect}
    {@const screenX = createBboxRect.x * canvasStore.scale + canvasStore.offsetX}
    {@const screenY =
      (createBboxRect.y + createBboxRect.height) * canvasStore.scale + canvasStore.offsetY}
    <div class="absolute z-30 flex gap-1" style="left: {screenX}px; top: {screenY + 4}px;">
      <button
        class="bg-primary-500 hover:bg-primary-600 rounded px-2 py-1 text-xs font-medium text-white
          shadow-lg transition-colors"
        onclick={handleCreateBbox}
      >
        새 bbox 생성
      </button>
      <button
        class="rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600 shadow-lg
          transition-colors hover:bg-gray-200"
        onclick={dismissCreateBbox}
      >
        취소
      </button>
    </div>
  {/if}
</div>
