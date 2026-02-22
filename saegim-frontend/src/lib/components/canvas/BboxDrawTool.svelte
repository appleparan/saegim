<script lang="ts">
  import Konva from 'konva'
  import { untrack } from 'svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { rectToPoly, normalizeRect, clampRect } from '$lib/utils/bbox'

  interface Props {
    stage: Konva.Stage
    /** Called after a new element is drawn with its anno_id. */
    onDrawComplete?: (annoId: number) => void
  }

  let { stage, onDrawComplete }: Props = $props()

  let drawLayer: Konva.Layer | null = null
  let drawRect: Konva.Rect | null = null
  let isDrawing = $state(false)
  let startPoint = $state({ x: 0, y: 0 })

  function init() {
    if (drawLayer) return
    drawLayer = new Konva.Layer()
    stage.add(drawLayer)

    // Apply current transform
    drawLayer.position({ x: canvasStore.offsetX, y: canvasStore.offsetY })
    drawLayer.scale({ x: canvasStore.scale, y: canvasStore.scale })

    stage.on('mousedown.draw', handleMouseDown)
    stage.on('mousemove.draw', handleMouseMove)
    stage.on('mouseup.draw', handleMouseUp)
  }

  function getImagePoint(_e: Konva.KonvaEventObject<MouseEvent>): { x: number; y: number } {
    const pointer = stage.getPointerPosition()
    if (!pointer) return { x: 0, y: 0 }
    return {
      x: (pointer.x - canvasStore.offsetX) / canvasStore.scale,
      y: (pointer.y - canvasStore.offsetY) / canvasStore.scale,
    }
  }

  function handleMouseDown(e: Konva.KonvaEventObject<MouseEvent>) {
    if (canvasStore.toolMode !== 'draw') return
    if (e.evt.button !== 0) return

    const point = getImagePoint(e)
    startPoint = point
    isDrawing = true

    drawRect = new Konva.Rect({
      x: point.x,
      y: point.y,
      width: 0,
      height: 0,
      stroke: '#2563eb',
      strokeWidth: 2 / canvasStore.scale,
      dash: [6 / canvasStore.scale, 3 / canvasStore.scale],
      fill: 'rgba(37, 99, 235, 0.1)',
    })
    drawLayer?.add(drawRect)
    drawLayer?.batchDraw()
  }

  function handleMouseMove(e: Konva.KonvaEventObject<MouseEvent>) {
    if (!isDrawing || !drawRect) return

    const point = getImagePoint(e)
    drawRect.setAttrs({
      width: point.x - startPoint.x,
      height: point.y - startPoint.y,
    })
    drawLayer?.batchDraw()
  }

  function handleMouseUp() {
    if (!isDrawing || !drawRect) return
    isDrawing = false

    const raw = {
      x: drawRect.x(),
      y: drawRect.y(),
      width: drawRect.width(),
      height: drawRect.height(),
    }
    drawRect.destroy()
    drawRect = null
    drawLayer?.batchDraw()

    const normalized = normalizeRect(raw)

    // Ignore tiny accidental clicks
    if (normalized.width < 5 || normalized.height < 5) return

    const clamped = clampRect(normalized, canvasStore.imageWidth, canvasStore.imageHeight)
    const poly = rectToPoly(clamped)
    const annoId = annotationStore.addElement('text_block', poly)
    if (annoId >= 0) {
      annotationStore.selectElement(annoId)
      canvasStore.setTool('select')
      onDrawComplete?.(annoId)
    }
  }

  $effect(() => {
    // untrack: init() reads canvasStore values for initial layer transform.
    // Without untrack, every zoom/pan would destroy and recreate the layer.
    // The transform sync effect below handles subsequent updates.
    untrack(() => init())
    return () => {
      stage.off('mousedown.draw')
      stage.off('mousemove.draw')
      stage.off('mouseup.draw')
      drawLayer?.destroy()
      drawLayer = null
      drawRect = null
    }
  })

  // Sync draw layer transform
  $effect(() => {
    if (drawLayer) {
      drawLayer.position({ x: canvasStore.offsetX, y: canvasStore.offsetY })
      drawLayer.scale({ x: canvasStore.scale, y: canvasStore.scale })
    }
  })
</script>
