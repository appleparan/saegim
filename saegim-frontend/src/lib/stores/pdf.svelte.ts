/**
 * PDF document state management using Svelte 5 runes and pdfjs-dist.
 */

import {
  getDocument,
  GlobalWorkerOptions,
  type PDFDocumentProxy,
  type PDFPageProxy,
} from 'pdfjs-dist'

// Configure PDF.js worker.
// Use non-minified .mjs for better Vite/SvelteKit compatibility.
// See: https://github.com/mozilla/pdf.js/issues/20236
const workerSrc = new URL('pdfjs-dist/build/pdf.worker.mjs', import.meta.url).toString()
if (!GlobalWorkerOptions.workerSrc) {
  GlobalWorkerOptions.workerSrc = workerSrc
}

/** Base render scale matching pypdfium2 render(scale=2.0) for coordinate compatibility. */
export const PDF_BASE_SCALE = 2.0

class PdfStore {
  pdfDoc = $state<PDFDocumentProxy | null>(null)
  currentPageNo = $state(1)
  totalPages = $state(0)
  isLoading = $state(false)
  error = $state<string | null>(null)

  private currentUrl = ''
  private pageCache = new Map<number, PDFPageProxy>()

  /** Load a PDF document from a URL. */
  async loadDocument(url: string): Promise<void> {
    if (this.currentUrl === url && this.pdfDoc) return

    this.isLoading = true
    this.error = null

    try {
      if (this.pdfDoc) {
        this.pdfDoc.destroy()
        this.pageCache.clear()
      }

      const doc = await getDocument(url).promise
      this.pdfDoc = doc
      this.totalPages = doc.numPages
      this.currentPageNo = 1
      this.currentUrl = url
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'PDF 문서를 불러올 수 없습니다.'
      console.warn('[saegim] PDF store loadDocument failed:', msg, 'url:', url)
      this.error = msg
      this.pdfDoc = null
      this.totalPages = 0
    } finally {
      this.isLoading = false
    }
  }

  /** Get a PDFPageProxy for the given page number (1-based). Caches pages. */
  async getPage(pageNo: number): Promise<PDFPageProxy> {
    if (!this.pdfDoc) {
      throw new Error('PDF document not loaded')
    }
    if (pageNo < 1 || pageNo > this.totalPages) {
      throw new RangeError(`Page number ${pageNo} out of range [1, ${this.totalPages}]`)
    }

    const cached = this.pageCache.get(pageNo)
    if (cached) return cached

    const page = await this.pdfDoc.getPage(pageNo)
    this.pageCache.set(pageNo, page)
    return page
  }

  /** Set the current page number. */
  setCurrentPage(pageNo: number): void {
    if (pageNo >= 1 && pageNo <= this.totalPages) {
      this.currentPageNo = pageNo
    }
  }

  /** Go to next page if available. */
  nextPage(): void {
    if (this.currentPageNo < this.totalPages) {
      this.currentPageNo += 1
    }
  }

  /** Go to previous page if available. */
  prevPage(): void {
    if (this.currentPageNo > 1) {
      this.currentPageNo -= 1
    }
  }

  /** Clean up resources. */
  destroy(): void {
    this.pageCache.clear()
    if (this.pdfDoc) {
      this.pdfDoc.destroy()
      this.pdfDoc = null
    }
    this.totalPages = 0
    this.currentPageNo = 1
    this.currentUrl = ''
    this.error = null
  }
}

export const pdfStore = new PdfStore()
