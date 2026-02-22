<script lang="ts">
  import { untrack } from 'svelte'
  import type { PDFPageProxy } from 'pdfjs-dist'
  import { TextLayer } from 'pdfjs-dist'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { PDF_BASE_SCALE } from '$lib/stores/pdf.svelte'

  interface Props {
    pageProxy: PDFPageProxy
  }

  let { pageProxy }: Props = $props()

  let canvasEl: HTMLCanvasElement
  let textLayerEl: HTMLDivElement
  let renderingScale = $state(PDF_BASE_SCALE)
  const TEXT_LAYER_SCALE = PDF_BASE_SCALE
  const MAX_RERENDER_SCALE = 6.0
  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let renderTask: ReturnType<PDFPageProxy['render']> | null = null
  let textLayerInstance: TextLayer | null = null

  /** Render the PDF page to canvas at the given scale. */
  async function renderCanvas(page: PDFPageProxy, scale: number): Promise<void> {
    if (!canvasEl) return

    // Cancel any in-progress render
    if (renderTask) {
      renderTask.cancel()
      renderTask = null
    }

    const viewport = page.getViewport({ scale })
    canvasEl.width = viewport.width
    canvasEl.height = viewport.height

    const ctx = canvasEl.getContext('2d')
    if (!ctx) return

    try {
      renderTask = page.render({ canvasContext: ctx, viewport, canvas: canvasEl })
      await renderTask.promise
      renderingScale = scale
    } catch (e) {
      // RenderingCancelledException is expected when re-rendering during zoom
      if (e instanceof Error && e.message.includes('cancelled')) return
      throw e
    } finally {
      renderTask = null
    }
  }

  /** Render the PDF.js TextLayer for native text selection. */
  async function renderTextLayer(page: PDFPageProxy): Promise<void> {
    if (!textLayerEl) return

    const viewport = page.getViewport({ scale: TEXT_LAYER_SCALE })

    // Cancel previous text layer
    if (textLayerInstance) {
      textLayerInstance.cancel()
      textLayerInstance = null
    }

    // Clear previous text layer content — intentional DOM manipulation for PDF.js
    // eslint-disable-next-line svelte/no-dom-manipulating
    textLayerEl.innerHTML = ''
    textLayerEl.style.width = `${viewport.width}px`
    textLayerEl.style.height = `${viewport.height}px`

    try {
      const textContent = await page.getTextContent()
      textLayerInstance = new TextLayer({
        textContentSource: textContent,
        container: textLayerEl,
        viewport,
      })
      await textLayerInstance.render()
    } catch (e) {
      if (e instanceof Error && e.message.includes('cancelled')) return
      console.warn('[saegim] TextLayer render failed:', e)
    }
  }

  /** Schedule a high-resolution re-render after zoom settles. */
  function scheduleRerender(): void {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      const targetScale = Math.min(PDF_BASE_SCALE * canvasStore.scale, MAX_RERENDER_SCALE)
      if (Math.abs(targetScale - renderingScale) > 0.25) {
        void renderCanvas(pageProxy, targetScale)
      }
      debounceTimer = null
    }, 220)
  }

  // Initial render when pageProxy changes
  $effect(() => {
    const page = pageProxy
    if (page && canvasEl) {
      untrack(() => {
        void renderCanvas(page, PDF_BASE_SCALE)
        void renderTextLayer(page)
      })
    }
  })

  // Watch for zoom changes and schedule re-render
  $effect(() => {
    const _scale = canvasStore.scale
    scheduleRerender()
  })

  // Cleanup on unmount
  $effect(() => {
    return () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      if (renderTask) renderTask.cancel()
      if (textLayerInstance) textLayerInstance.cancel()
    }
  })

  /** CSS transform scale factor for raster canvas. */
  let canvasCssScale = $derived((canvasStore.scale * PDF_BASE_SCALE) / renderingScale)

  /** Keep text layer at base viewport and only apply UI zoom via CSS. */
  let textLayerCssScale = $derived(canvasStore.scale)
</script>

<!-- PDF canvas layer -->
<canvas
  bind:this={canvasEl}
  data-pdf-renderer
  style="
    position: absolute;
    transform-origin: 0 0;
    transform: translate({canvasStore.offsetX}px, {canvasStore.offsetY}px) scale({canvasCssScale});
    pointer-events: none;
    user-select: none;
  "
></canvas>

<!-- Text layer for native text selection -->
<div
  bind:this={textLayerEl}
  data-text-layer
  class="textLayer"
  style="
    position: absolute;
    transform-origin: 0 0;
    transform: translate({canvasStore.offsetX}px, {canvasStore.offsetY}px) scale({textLayerCssScale});
    z-index: 1;
  "
></div>

<style>
  /* PDF.js TextLayer styles for text selection */
  :global(.textLayer) {
    opacity: 0.3;
    line-height: 1;
    pointer-events: auto;
  }

  :global(.textLayer span),
  :global(.textLayer br) {
    color: transparent;
    position: absolute;
    white-space: pre;
    transform-origin: 0% 0%;
    pointer-events: all;
  }

  :global(.textLayer span::selection) {
    background: rgba(0, 0, 255, 0.3);
  }

  :global(.textLayer .markedContent) {
    top: 0;
    height: 0;
  }

  :global(.textLayer .endOfContent) {
    display: block;
    position: absolute;
    inset: 100% 0 0;
    z-index: -1;
    cursor: default;
    user-select: none;
  }

  :global(.textLayer .endOfContent.active) {
    top: 0;
  }
</style>
