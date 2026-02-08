<script lang="ts">
  import Konva from 'konva'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import BboxLayer from './BboxLayer.svelte'
  import BboxDrawTool from './BboxDrawTool.svelte'

  interface Props {
    imageUrl: string
    width: number
    height: number
  }

  let { imageUrl, width, height }: Props = $props()

  let containerEl: HTMLDivElement
  let stage = $state<Konva.Stage | null>(null)
  let imageLayer: Konva.Layer | null = null
  let containerWidth = $state(0)
  let containerHeight = $state(0)

  function initStage() {
    if (!containerEl || stage) return

    const rect = containerEl.getBoundingClientRect()
    containerWidth = rect.width
    containerHeight = rect.height

    stage = new Konva.Stage({
      container: containerEl,
      width: containerWidth,
      height: containerHeight,
    })

    imageLayer = new Konva.Layer()
    stage.add(imageLayer)

    const img = new window.Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      if (!imageLayer || !stage) return
      const konvaImage = new Konva.Image({
        image: img,
        x: 0,
        y: 0,
        width,
        height,
      })
      imageLayer.add(konvaImage)
      imageLayer.batchDraw()
      canvasStore.setImageDimensions(width, height)
      canvasStore.fitToContainer(containerWidth, containerHeight)
      applyTransform()
    }
    img.src = imageUrl

    stage.on('wheel', handleWheel)
    stage.on('mousedown', handleMouseDown)
    stage.on('mousemove', handleMouseMove)
    stage.on('mouseup', handleMouseUp)
  }

  let isPanning = $state(false)
  let panStart = $state({ x: 0, y: 0 })

  function handleWheel(e: Konva.KonvaEventObject<WheelEvent>) {
    e.evt.preventDefault()
    const scaleBy = 1.1
    const oldScale = canvasStore.scale
    const pointer = stage!.getPointerPosition()
    if (!pointer) return

    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy
    canvasStore.setScale(newScale)

    const mousePointTo = {
      x: (pointer.x - canvasStore.offsetX) / oldScale,
      y: (pointer.y - canvasStore.offsetY) / oldScale,
    }
    const newPos = {
      x: pointer.x - mousePointTo.x * canvasStore.scale,
      y: pointer.y - mousePointTo.y * canvasStore.scale,
    }
    canvasStore.setOffset(newPos.x, newPos.y)
    applyTransform()
  }

  function handleMouseDown(e: Konva.KonvaEventObject<MouseEvent>) {
    if (canvasStore.toolMode === 'pan' || e.evt.button === 1) {
      isPanning = true
      panStart = { x: e.evt.clientX - canvasStore.offsetX, y: e.evt.clientY - canvasStore.offsetY }
      if (containerEl) containerEl.style.cursor = 'grabbing'
    }
  }

  function handleMouseMove(e: Konva.KonvaEventObject<MouseEvent>) {
    if (isPanning) {
      canvasStore.setOffset(e.evt.clientX - panStart.x, e.evt.clientY - panStart.y)
      applyTransform()
    }
  }

  function handleMouseUp() {
    if (isPanning) {
      isPanning = false
      if (containerEl) containerEl.style.cursor = canvasStore.toolMode === 'pan' ? 'grab' : 'default'
    }
  }

  function applyTransform() {
    if (!stage) return
    const layers = stage.getLayers()
    for (const layer of layers) {
      layer.position({ x: canvasStore.offsetX, y: canvasStore.offsetY })
      layer.scale({ x: canvasStore.scale, y: canvasStore.scale })
      layer.batchDraw()
    }
  }

  function handleResize() {
    if (!containerEl || !stage) return
    const rect = containerEl.getBoundingClientRect()
    containerWidth = rect.width
    containerHeight = rect.height
    stage.width(containerWidth)
    stage.height(containerHeight)
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

  $effect(() => {
    if (containerEl) {
      initStage()
      const observer = new ResizeObserver(handleResize)
      observer.observe(containerEl)
      return () => {
        observer.disconnect()
        stage?.destroy()
        stage = null
        imageLayer = null
      }
    }
  })

  // React to external scale/offset changes (toolbar buttons)
  $effect(() => {
    const _scale = canvasStore.scale
    const _ox = canvasStore.offsetX
    const _oy = canvasStore.offsetY
    applyTransform()
  })
</script>

<div class="absolute inset-0 overflow-hidden" bind:this={containerEl}>
</div>

{#if stage}
  <BboxLayer {stage} />
  {#if canvasStore.toolMode === 'draw'}
    <BboxDrawTool {stage} />
  {/if}
{/if}
