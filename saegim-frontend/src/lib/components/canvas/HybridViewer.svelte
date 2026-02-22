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
  import BboxLayer from './BboxLayer.svelte'
  import BboxDrawTool from './BboxDrawTool.svelte'
  import TextOverlay from './TextOverlay.svelte'
  import PdfRenderer from './PdfRenderer.svelte'

  interface Props {
    pageProxy?: PDFPageProxy
    imageUrl?: string
    width: number
    height: number
  }

  let { pageProxy, imageUrl, width, height }: Props = $props()

  // --- DOM refs ---
  let containerEl: HTMLDivElement
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

  // --- Derived pointer-events ---
  let konvaPointerEvents = $derived(
    computeKonvaPointerEvents(
      canvasStore.toolMode,
      interactionMode,
      hoveredImageBlockId,
    ),
  )

  let textPointerEvents = $derived(
    computeTextPointerEvents(
      canvasStore.toolMode,
      interactionMode,
      hoveredImageBlockId,
    ),
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
      canvasStore.setOffset(
        e.clientX - panStart.x,
        e.clientY - panStart.y,
      )
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
        containerEl.style.cursor =
          canvasStore.toolMode === 'pan' ? 'grab' : 'default'
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
    <BboxLayer {stage} filter={(el) => isImageBlock(el) || el.anno_id === annotationStore.selectedElementId} {interactionMode} />
    {#if canvasStore.toolMode === 'draw'}
      <BboxDrawTool {stage} />
    {/if}
  {/if}

  <!-- Layer 3: Text overlay (z-index: 20) — only for image fallback mode -->
  {#if !pageProxy}
    <TextOverlay pointerEvents={textPointerEvents} />
  {/if}
</div>
