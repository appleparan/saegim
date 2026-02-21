<script lang="ts">
  import { untrack } from 'svelte'
  import type { PDFPageProxy } from 'pdfjs-dist'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { PDF_BASE_SCALE } from '$lib/stores/pdf.svelte'

  interface Props {
    pageProxy: PDFPageProxy
  }

  let { pageProxy }: Props = $props()

  let canvasEl: HTMLCanvasElement
  let renderingScale = $state(PDF_BASE_SCALE)
  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let renderTask: ReturnType<PDFPageProxy['render']> | null = null

  /** Render the PDF page to canvas at the given scale. */
  async function renderPage(page: PDFPageProxy, scale: number): Promise<void> {
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

  /** Schedule a high-resolution re-render after zoom settles. */
  function scheduleRerender(): void {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      const targetScale = PDF_BASE_SCALE * canvasStore.scale
      if (Math.abs(targetScale - renderingScale) > 0.01) {
        renderPage(pageProxy, targetScale)
      }
      debounceTimer = null
    }, 300)
  }

  // Initial render when pageProxy changes
  $effect(() => {
    const page = pageProxy
    if (page && canvasEl) {
      untrack(() => renderPage(page, PDF_BASE_SCALE))
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
    }
  })

  /** CSS transform scale factor: viewport scale relative to current rendering scale. */
  let cssScale = $derived((canvasStore.scale * PDF_BASE_SCALE) / renderingScale)
</script>

<canvas
  bind:this={canvasEl}
  data-pdf-renderer
  style="
    position: absolute;
    transform-origin: 0 0;
    transform: translate({canvasStore.offsetX}px, {canvasStore.offsetY}px) scale({cssScale});
    pointer-events: none;
    user-select: none;
  "
></canvas>
