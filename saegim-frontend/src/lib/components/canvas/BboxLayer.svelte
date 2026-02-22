<script lang="ts">
  import Konva from 'konva'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { polyToRect, rectToPoly, clampRect } from '$lib/utils/bbox'
  import { getCategoryColor } from '$lib/utils/color'
  import { SvelteMap } from 'svelte/reactivity'
  import type { LayoutElement } from '$lib/types/omnidocbench'

  interface Props {
    stage: Konva.Stage
    /** Optional filter to render only a subset of elements. */
    filter?: (el: LayoutElement) => boolean
    /** Interaction mode from HybridViewer. Controls bbox visibility. */
    interactionMode?: 'browse' | 'edit'
  }

  let { stage, filter, interactionMode }: Props = $props()

  let bboxLayer: Konva.Layer | null = null
  let transformer: Konva.Transformer | null = null
  let rects = new SvelteMap<number, Konva.Rect>()

  function init() {
    if (bboxLayer) return
    bboxLayer = new Konva.Layer()
    stage.add(bboxLayer)

    // Apply current viewport transform so bboxes align immediately
    bboxLayer.position({ x: canvasStore.offsetX, y: canvasStore.offsetY })
    bboxLayer.scale({ x: canvasStore.scale, y: canvasStore.scale })

    transformer = new Konva.Transformer({
      rotateEnabled: false,
      keepRatio: false,
      enabledAnchors: [
        'top-left',
        'top-center',
        'top-right',
        'middle-left',
        'middle-right',
        'bottom-left',
        'bottom-center',
        'bottom-right',
      ],
      borderStroke: '#2563eb',
      borderStrokeWidth: 2,
      anchorStroke: '#2563eb',
      anchorFill: '#ffffff',
      anchorSize: 8,
      anchorCornerRadius: 2,
    })
    bboxLayer.add(transformer)

    // Click on empty area deselects
    stage.on('click tap', (e: Konva.KonvaEventObject<MouseEvent>) => {
      if (canvasStore.toolMode !== 'select') return
      if (e.target === stage) {
        annotationStore.selectElement(null)
      }
    })
  }

  function computeRectStyle(
    el: LayoutElement,
    isSelected: boolean,
    mode: 'browse' | 'edit' | undefined,
  ): { opacity: number; stroke: string; strokeWidth: number; fill: string } {
    const color = getCategoryColor(el.category_type)

    // In browse mode (hybrid), rects are invisible unless selected
    if (mode === 'browse' && !isSelected) {
      return { opacity: 0, stroke: '#2563eb', strokeWidth: 2, fill: 'transparent' }
    }

    const opacity = el.ignore ? 0.3 : 0.5
    return {
      opacity,
      stroke: color,
      strokeWidth: isSelected ? 3 : 2,
      fill: color,
    }
  }

  function addHoverHandlers(konvaRect: Konva.Rect): void {
    konvaRect.on('mouseenter', () => {
      if (interactionMode !== 'browse') return
      konvaRect.setAttrs({
        opacity: 0.2,
        stroke: '#2563eb',
        strokeWidth: 2,
      })
      bboxLayer?.batchDraw()
    })

    konvaRect.on('mouseleave', () => {
      if (interactionMode !== 'browse') return
      const isSelected = annotationStore.selectedElementId === konvaRect.getAttr('annoId')
      if (!isSelected) {
        konvaRect.setAttrs({ opacity: 0, stroke: '#2563eb', strokeWidth: 2 })
        bboxLayer?.batchDraw()
      }
    })
  }

  function syncRects(elements: readonly LayoutElement[]) {
    if (!bboxLayer || !transformer) return

    const filtered = filter ? elements.filter(filter) : elements
    const currentIds = new Set(filtered.map((el) => el.anno_id))

    // Remove rects for deleted elements
    for (const [id, rect] of rects) {
      if (!currentIds.has(id)) {
        rect.destroy()
        rects.delete(id)
      }
    }

    // Add or update rects
    for (const el of filtered) {
      const rect = polyToRect(el.poly)
      const isSelected = annotationStore.selectedElementId === el.anno_id
      const style = computeRectStyle(el, isSelected, interactionMode)

      let konvaRect = rects.get(el.anno_id)
      if (!konvaRect) {
        konvaRect = new Konva.Rect({
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          stroke: style.stroke,
          strokeWidth: style.strokeWidth,
          fill: style.fill,
          opacity: style.opacity,
          draggable: canvasStore.toolMode === 'select',
          name: `bbox-${el.anno_id}`,
        })

        // Store anno_id as custom attribute for hover handler
        konvaRect.setAttr('annoId', el.anno_id)

        konvaRect.on('click tap', () => {
          if (canvasStore.toolMode !== 'select') return
          annotationStore.selectElement(el.anno_id)
        })

        konvaRect.on('dragend', () => {
          const newRect = clampRect(
            {
              x: konvaRect!.x(),
              y: konvaRect!.y(),
              width: konvaRect!.width(),
              height: konvaRect!.height(),
            },
            canvasStore.imageWidth,
            canvasStore.imageHeight,
          )
          konvaRect!.position({ x: newRect.x, y: newRect.y })
          annotationStore.updateElement(el.anno_id, {
            poly: rectToPoly(newRect),
          })
        })

        konvaRect.on('transformend', () => {
          const scaleX = konvaRect!.scaleX()
          const scaleY = konvaRect!.scaleY()
          konvaRect!.scaleX(1)
          konvaRect!.scaleY(1)
          const newRect = clampRect(
            {
              x: konvaRect!.x(),
              y: konvaRect!.y(),
              width: Math.max(5, konvaRect!.width() * scaleX),
              height: Math.max(5, konvaRect!.height() * scaleY),
            },
            canvasStore.imageWidth,
            canvasStore.imageHeight,
          )
          konvaRect!.setAttrs({
            x: newRect.x,
            y: newRect.y,
            width: newRect.width,
            height: newRect.height,
          })
          annotationStore.updateElement(el.anno_id, {
            poly: rectToPoly(newRect),
          })
        })

        // Add hover handlers for hybrid browse mode
        if (interactionMode !== undefined) {
          addHoverHandlers(konvaRect)
        }

        bboxLayer!.add(konvaRect)
        rects.set(el.anno_id, konvaRect)
      } else {
        konvaRect.setAttrs({
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          stroke: style.stroke,
          strokeWidth: style.strokeWidth,
          fill: style.fill,
          opacity: style.opacity,
          draggable: canvasStore.toolMode === 'select',
        })
      }
    }

    // Update transformer selection
    const selectedRect =
      annotationStore.selectedElementId !== null
        ? rects.get(annotationStore.selectedElementId)
        : null

    if (selectedRect && canvasStore.toolMode === 'select') {
      transformer.nodes([selectedRect])
    } else {
      transformer.nodes([])
    }

    // Ensure transformer is on top
    transformer.moveToTop()
    bboxLayer.batchDraw()
  }

  $effect(() => {
    init()
    return () => {
      bboxLayer?.destroy()
      bboxLayer = null
      transformer = null
      rects.clear()
    }
  })

  $effect(() => {
    const _elements = annotationStore.elements
    const _selected = annotationStore.selectedElementId
    const _tool = canvasStore.toolMode
    const _mode = interactionMode
    syncRects(_elements)
  })
</script>
