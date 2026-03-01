<script lang="ts">
  import Konva from 'konva'
  import { untrack } from 'svelte'
  import type { PDFPageProxy } from 'pdfjs-dist'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { isImageBlock } from '$lib/types/element-groups'
  import {
    computeKonvaPointerEvents,
    computeTextPointerEvents,
    findHoveredImageBlock,
    resolveInteractionMode,
  } from '$lib/utils/interaction'
  import type { InteractionMode } from '$lib/utils/interaction'
  import { polyToRect } from '$lib/utils/bbox'
  import BboxLayer from './BboxLayer.svelte'
  import BboxDrawTool from './BboxDrawTool.svelte'
  import TextOverlay from './TextOverlay.svelte'
  import ReadingOrderOverlay from './ReadingOrderOverlay.svelte'
  import PdfRenderer from './PdfRenderer.svelte'
  import RelationOverlay from './RelationOverlay.svelte'

  interface Props {
    pageProxy?: PDFPageProxy
    imageUrl?: string
    width: number
    height: number
    /** Called when OCR is requested for a drawn element. */
    onOcrRequest?: (annoId: number) => void
  }

  let { pageProxy, imageUrl, width, height, onOcrRequest }: Props = $props()

  // --- DOM refs ---
  // eslint-disable-next-line no-unassigned-vars -- Svelte bind:this
  let containerEl: HTMLDivElement
  // eslint-disable-next-line no-unassigned-vars -- Svelte bind:this
  let konvaContainerEl: HTMLDivElement

  // --- Konva ---
  let stage = $state<Konva.Stage | null>(null)

  // --- Interaction state machine ---
  let interactionMode = $state<InteractionMode>('browse')
  let hoveredImageBlockId = $state<number | null>(null)

  // --- Pan state ---
  let isPanning = $state(false)
  let panStart = $state({ x: 0, y: 0 })

  // --- Container size ---
  let containerWidth = $state(0)
  let containerHeight = $state(0)

  // --- OCR prompt for drawn elements ---
  let drawnAnnoId = $state<number | null>(null)

  let drawnElementScreenPos = $derived.by(() => {
    if (drawnAnnoId === null) return null
    const el = annotationStore.elements.find((e) => e.anno_id === drawnAnnoId)
    if (!el) return null
    const rect = polyToRect(el.poly)
    return {
      x: rect.x * canvasStore.scale + canvasStore.offsetX,
      y: (rect.y + rect.height) * canvasStore.scale + canvasStore.offsetY + 8,
    }
  })

  function handleDrawComplete(annoId: number): void {
    drawnAnnoId = annoId
  }

  function handleOcrRequest(): void {
    if (drawnAnnoId !== null) {
      onOcrRequest?.(drawnAnnoId)
      drawnAnnoId = null
    }
  }

  function dismissOcrPrompt(): void {
    drawnAnnoId = null
  }

  // --- Derived pointer-events ---
  let konvaPointerEvents = $derived(
    computeKonvaPointerEvents(canvasStore.toolMode, interactionMode, hoveredImageBlockId),
  )

  let textPointerEvents = $derived(
    computeTextPointerEvents(canvasStore.toolMode, interactionMode, hoveredImageBlockId),
  )

  // --- Zoom/Pan (container-level DOM events) ---

  function handleWheel(e: WheelEvent) {
    e.preventDefault()
    const scaleBy = 1.1
    const oldScale = canvasStore.scale
    const rect = containerEl.getBoundingClientRect()
    const pointerX = e.clientX - rect.left
    const pointerY = e.clientY - rect.top

    const newScale = e.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy
    const clampedScale = Math.max(0.1, Math.min(10, newScale))

    const mousePointTo = {
      x: (pointerX - canvasStore.offsetX) / oldScale,
      y: (pointerY - canvasStore.offsetY) / oldScale,
    }

    canvasStore.setViewport(
      clampedScale,
      pointerX - mousePointTo.x * clampedScale,
      pointerY - mousePointTo.y * clampedScale,
    )
  }

  function handleMouseDown(e: MouseEvent) {
    if (canvasStore.toolMode === 'pan' || e.button === 1) {
      e.preventDefault()
      isPanning = true
      panStart = {
        x: e.clientX - canvasStore.offsetX,
        y: e.clientY - canvasStore.offsetY,
      }
      if (containerEl) containerEl.style.cursor = 'grabbing'
    }
  }

  function handleMouseMove(e: MouseEvent) {
    if (isPanning) {
      canvasStore.setOffset(e.clientX - panStart.x, e.clientY - panStart.y)
      return
    }

    // In browse mode, detect if cursor is over an image block
    if (interactionMode === 'browse' && canvasStore.toolMode === 'select') {
      checkImageBlockHover(e.clientX, e.clientY)
    }
  }

  function handleMouseUp() {
    if (isPanning) {
      isPanning = false
      if (containerEl) {
        containerEl.style.cursor = canvasStore.toolMode === 'pan' ? 'grab' : 'default'
      }
    }
  }

  function checkImageBlockHover(clientX: number, clientY: number): void {
    const rect = containerEl.getBoundingClientRect()
    hoveredImageBlockId = findHoveredImageBlock(
      { x: clientX, y: clientY },
      { x: rect.left, y: rect.top, width: rect.width, height: rect.height },
      canvasStore.offsetX,
      canvasStore.offsetY,
      canvasStore.scale,
      annotationStore.elements,
    )
  }

  // --- Konva stage initialization ---

  function initStage(): void {
    if (!konvaContainerEl || stage) return

    const rect = containerEl.getBoundingClientRect()
    containerWidth = rect.width
    containerHeight = rect.height

    stage = new Konva.Stage({
      container: konvaContainerEl,
      width: containerWidth,
      height: containerHeight,
    })

    canvasStore.setImageDimensions(width, height)
    canvasStore.fitToContainer(containerWidth, containerHeight)
  }

  function handleResize(): void {
    if (!containerEl || !stage) return
    const rect = containerEl.getBoundingClientRect()
    containerWidth = rect.width
    containerHeight = rect.height
    stage.width(containerWidth)
    stage.height(containerHeight)
    canvasStore.fitToContainer(containerWidth, containerHeight)
  }

  /** Get image-space pointer position from current stage pointer. */
  export function getImagePointer(): { x: number; y: number } | null {
    if (!stage) return null
    const pointer = stage.getPointerPosition()
    if (!pointer) return null
    return {
      x: (pointer.x - canvasStore.offsetX) / canvasStore.scale,
      y: (pointer.y - canvasStore.offsetY) / canvasStore.scale,
    }
  }

  // --- Effects ---

  // Initialize Konva stage on mount
  $effect(() => {
    if (konvaContainerEl && containerEl) {
      untrack(() => initStage())
      const observer = new ResizeObserver(handleResize)
      observer.observe(containerEl)
      return () => {
        observer.disconnect()
        stage?.destroy()
        stage = null
      }
    }
  })

  // Re-fit viewport when image dimensions change (page navigation)
  $effect(() => {
    const _w = width
    const _h = height
    if (stage && _w > 0 && _h > 0) {
      canvasStore.setImageDimensions(_w, _h)
      untrack(() => canvasStore.fitToContainer(containerWidth, containerHeight))
    }
  })

  // Sync Konva layer transforms when viewport changes
  $effect(() => {
    if (!stage) return
    const _scale = canvasStore.scale
    const _ox = canvasStore.offsetX
    const _oy = canvasStore.offsetY
    const layers = stage.getLayers()
    for (const layer of layers) {
      layer.position({ x: canvasStore.offsetX, y: canvasStore.offsetY })
      layer.scale({ x: canvasStore.scale, y: canvasStore.scale })
      layer.batchDraw()
    }
  })

  // Update interaction mode based on selection state
  $effect(() => {
    const nextMode = resolveInteractionMode(
      interactionMode,
      annotationStore.selectedElement,
      annotationStore.selectedElementId,
    )
    if (nextMode !== interactionMode) {
      interactionMode = nextMode
    }
  })

  // Reset to browse when tool changes
  $effect(() => {
    const _tool = canvasStore.toolMode
    if (canvasStore.toolMode !== 'select') {
      interactionMode = 'browse'
      hoveredImageBlockId = null
    }
  })

  // Dismiss OCR prompt when selection changes away from drawn element
  $effect(() => {
    const selected = annotationStore.selectedElementId
    if (drawnAnnoId !== null && selected !== drawnAnnoId) {
      drawnAnnoId = null
    }
  })
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="absolute inset-0 overflow-hidden"
  bind:this={containerEl}
  onwheel={handleWheel}
  onmousedown={handleMouseDown}
  onmousemove={handleMouseMove}
  onmouseup={handleMouseUp}
>
  <!-- Layer 1: Background (z-index: 0) — PDF.js canvas or fallback image -->
  {#if pageProxy}
    <PdfRenderer {pageProxy} />
  {:else if imageUrl}
    <img
      src={imageUrl}
      alt="page background"
      draggable="false"
      style="
        position: absolute;
        transform-origin: 0 0;
        transform: translate({canvasStore.offsetX}px, {canvasStore.offsetY}px) scale({canvasStore.scale});
        width: {width}px;
        height: {height}px;
        pointer-events: none;
        user-select: none;
      "
    />
  {/if}

  <!-- Layer 2: Konva canvas for image blocks (z-index: 10) -->
  <div
    bind:this={konvaContainerEl}
    style="
      position: absolute;
      inset: 0;
      z-index: 10;
      pointer-events: {konvaPointerEvents};
    "
  ></div>

  {#if stage}
    <BboxLayer
      {stage}
      filter={(el) => isImageBlock(el) || el.anno_id === annotationStore.selectedElementId}
      {interactionMode}
    />
    {#if canvasStore.toolMode === 'draw'}
      <BboxDrawTool {stage} onDrawComplete={handleDrawComplete} />
    {/if}
  {/if}

  <!-- Layer 3: Text overlay (z-index: 20) — only for image fallback mode -->
  {#if !pageProxy}
    <TextOverlay pointerEvents={textPointerEvents} />
  {/if}

  <!-- Layer 3.5: Reading order overlay (z-index: 25) -->
  <ReadingOrderOverlay />

  <!-- Layer 4: Relation arrows overlay (z-index: 30) -->
  <RelationOverlay />

  <!-- OCR prompt after drawing a new bbox -->
  {#if drawnAnnoId !== null && drawnElementScreenPos}
    <div
      class="absolute z-40 flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/95 px-3 py-2 shadow-lg backdrop-blur-sm dark:border-blue-800 dark:bg-blue-950/95"
      style="left: {drawnElementScreenPos.x}px; top: {drawnElementScreenPos.y}px;"
    >
      <svg
        class="h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
        />
      </svg>
      <span class="text-xs font-medium text-blue-900 dark:text-blue-200">
        이 영역에서 텍스트를 추출하시겠습니까?
      </span>
      <button
        type="button"
        class="rounded-md bg-blue-600 px-2.5 py-1 text-xs font-medium text-white transition-colors hover:bg-blue-700"
        onclick={handleOcrRequest}
      >
        OCR 실행
      </button>
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground px-1 text-lg leading-none"
        onclick={dismissOcrPrompt}
        aria-label="닫기"
      >
        &times;
      </button>
    </div>
  {/if}
</div>
