import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { PDF_BASE_SCALE } from '$lib/stores/pdf.svelte'

// Mock pdfjs-dist — must come before PdfRenderer import
vi.mock('pdfjs-dist', () => {
  class MockTextLayer {
    cancel = vi.fn()
    render = vi.fn(() => globalThis.Promise.resolve())
  }
  return {
    TextLayer: MockTextLayer,
    GlobalWorkerOptions: { workerSrc: '' },
  }
})

// Mock canvas context
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  clearRect: vi.fn(),
  drawImage: vi.fn(),
  fillRect: vi.fn(),
  scale: vi.fn(),
  translate: vi.fn(),
  transform: vi.fn(),
  setTransform: vi.fn(),
  save: vi.fn(),
  restore: vi.fn(),
})) as unknown as typeof HTMLCanvasElement.prototype.getContext

// Shared mock functions for matchMedia
let mockAddEventListener = vi.fn()
let mockRemoveEventListener = vi.fn()

function stubMatchMedia() {
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => ({
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener,
      matches: false,
    })),
  )
}

stubMatchMedia()

// Shared mock functions for page proxy
const mockRender = vi.fn(() => ({
  promise: Promise.resolve(),
  cancel: vi.fn(),
}))
const mockGetViewport = vi.fn((opts: { scale: number }) => ({
  width: 612 * opts.scale,
  height: 792 * opts.scale,
}))
const mockGetTextContent = vi.fn(() => Promise.resolve({ items: [], styles: {} }))

function createMockPageProxy() {
  return {
    getViewport: mockGetViewport,
    render: mockRender,
    getTextContent: mockGetTextContent,
    pageNumber: 1,
  } as unknown as import('pdfjs-dist').PDFPageProxy
}

describe('PdfRenderer', () => {
  // Lazy-import after mocks are set up
  let render: (typeof import('@testing-library/svelte'))['render']
  let cleanup: (typeof import('@testing-library/svelte'))['cleanup']
  let PdfRenderer: (typeof import('$lib/components/canvas/PdfRenderer.svelte'))['default']
  let canvasStore: (typeof import('$lib/stores/canvas.svelte'))['canvasStore']

  beforeEach(async () => {
    vi.clearAllMocks()
    mockAddEventListener = vi.fn()
    mockRemoveEventListener = vi.fn()
    stubMatchMedia()

    const testLib = await import('@testing-library/svelte')
    render = testLib.render
    cleanup = testLib.cleanup

    const pdfMod = await import('$lib/components/canvas/PdfRenderer.svelte')
    PdfRenderer = pdfMod.default

    const canvasMod = await import('$lib/stores/canvas.svelte')
    canvasStore = canvasMod.canvasStore

    canvasStore.setViewport(1, 0, 0)
    canvasStore.setImageDimensions(1224, 1584)
    vi.stubGlobal('devicePixelRatio', 1)
  })

  afterEach(() => {
    cleanup()
  })

  describe('initial render scale with DPR', () => {
    it('renders at PDF_BASE_SCALE * dpr on 1x display', async () => {
      vi.stubGlobal('devicePixelRatio', 1)
      render(PdfRenderer, { props: { pageProxy: createMockPageProxy() } })

      await vi.waitFor(() => {
        expect(mockRender).toHaveBeenCalled()
      })

      // On 1x display: initialScale = PDF_BASE_SCALE * 1 = 2.0
      const viewportCall = mockGetViewport.mock.calls[0]
      expect(viewportCall[0].scale).toBe(PDF_BASE_SCALE * 1)
    })

    it('renders at PDF_BASE_SCALE * dpr on 2x HiDPI display', async () => {
      vi.stubGlobal('devicePixelRatio', 2)
      render(PdfRenderer, { props: { pageProxy: createMockPageProxy() } })

      await vi.waitFor(() => {
        expect(mockRender).toHaveBeenCalled()
      })

      // On 2x display: initialScale = PDF_BASE_SCALE * 2 = 4.0
      const viewportCall = mockGetViewport.mock.calls[0]
      expect(viewportCall[0].scale).toBe(PDF_BASE_SCALE * 2)
    })

    it('caps initial render scale at MAX_RERENDER_SCALE (6.0)', async () => {
      vi.stubGlobal('devicePixelRatio', 4)
      render(PdfRenderer, { props: { pageProxy: createMockPageProxy() } })

      await vi.waitFor(() => {
        expect(mockRender).toHaveBeenCalled()
      })

      // PDF_BASE_SCALE * 4 = 8.0, capped at 6.0
      const viewportCall = mockGetViewport.mock.calls[0]
      expect(viewportCall[0].scale).toBe(6.0)
    })
  })

  describe('canvas dimensions reflect DPR-adjusted scale', () => {
    it('sets canvas size to viewport dimensions at DPR-adjusted scale', async () => {
      vi.stubGlobal('devicePixelRatio', 2)
      const { container } = render(PdfRenderer, {
        props: { pageProxy: createMockPageProxy() },
      })

      await vi.waitFor(() => {
        expect(mockRender).toHaveBeenCalled()
      })

      const canvas = container.querySelector('canvas[data-pdf-renderer]') as HTMLCanvasElement
      expect(canvas).toBeTruthy()
      // At scale 4.0 (2.0 * 2): width = 612 * 4 = 2448, height = 792 * 4 = 3168
      expect(canvas.width).toBe(612 * 4)
      expect(canvas.height).toBe(792 * 4)
    })
  })

  describe('DPR change detection', () => {
    it('registers matchMedia listener for DPR changes', async () => {
      render(PdfRenderer, { props: { pageProxy: createMockPageProxy() } })

      await vi.waitFor(() => {
        expect(mockAddEventListener).toHaveBeenCalledWith('change', expect.any(Function))
      })
    })
  })
})
