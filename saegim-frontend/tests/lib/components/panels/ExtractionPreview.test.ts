import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/svelte'
import ExtractionPreview from '$lib/components/panels/ExtractionPreview.svelte'
import { annotationStore } from '$lib/stores/annotation.svelte'
import type { AnnotationData } from '$lib/types/omnidocbench'

// Mock the pages API
vi.mock('$lib/api/pages', () => ({
  acceptExtraction: vi.fn(() =>
    Promise.resolve({
      annotation_data: { layout_dets: [], page_info: {}, page_attribute: {} },
    }),
  ),
  forceAcceptExtraction: vi.fn(() =>
    Promise.resolve({
      annotation_data: { layout_dets: [], page_info: {}, page_attribute: {} },
    }),
  ),
}))

// Mock the UI store
vi.mock('$lib/stores/ui.svelte', () => ({
  uiStore: {
    showNotification: vi.fn(),
  },
}))

function makeAutoData(count: number): AnnotationData {
  return {
    layout_dets: Array.from({ length: count }, (_, i) => ({
      category_type: i % 2 === 0 ? 'text_block' : 'figure',
      poly: [0, 0, 100, 0, 100, 100, 0, 100],
      anno_id: i + 1,
      text: `element ${i + 1}`,
    })),
    page_info: {},
    page_attribute: {},
  } as unknown as AnnotationData
}

describe('ExtractionPreview', () => {
  beforeEach(() => {
    annotationStore.clear()
  })

  afterEach(() => {
    cleanup()
  })

  it("shows extracting spinner when documentStatus is 'extracting'", () => {
    render(ExtractionPreview, {
      props: {
        pageId: 'page-1',
        documentId: 'doc-1',
        autoExtractedData: null,
        documentStatus: 'extracting',
        onAccepted: vi.fn(),
        onReExtract: vi.fn(),
      },
    })

    expect(screen.getByText('OCR extraction in progress...')).toBeTruthy()
  })

  it('shows auto-extracted data summary when data is available', () => {
    const autoData = makeAutoData(4)
    render(ExtractionPreview, {
      props: {
        pageId: 'page-1',
        documentId: 'doc-1',
        autoExtractedData: autoData,
        documentStatus: 'ready',
        onAccepted: vi.fn(),
        onReExtract: vi.fn(),
      },
    })

    expect(screen.getByText('Automatic extraction results available')).toBeTruthy()
    // 4 total elements: 2 text, 2 figure
    expect(screen.getByText(/Text 2, images 2 - total 4 elements/)).toBeTruthy()
  })

  it('shows accept and dismiss buttons when data is available', () => {
    const autoData = makeAutoData(2)
    render(ExtractionPreview, {
      props: {
        pageId: 'page-1',
        documentId: 'doc-1',
        autoExtractedData: autoData,
        documentStatus: 'ready',
        onAccepted: vi.fn(),
        onReExtract: vi.fn(),
      },
    })

    expect(screen.getByText('Accept')).toBeTruthy()
    expect(screen.getByText('Ignore')).toBeTruthy()
  })

  it('hides after dismiss is clicked', async () => {
    const autoData = makeAutoData(2)
    render(ExtractionPreview, {
      props: {
        pageId: 'page-1',
        documentId: 'doc-1',
        autoExtractedData: autoData,
        documentStatus: 'ready',
        onAccepted: vi.fn(),
        onReExtract: vi.fn(),
      },
    })

    expect(screen.getByText('Accept')).toBeTruthy()

    const dismissBtn = screen.getByText('Ignore')
    await fireEvent.click(dismissBtn)

    expect(screen.queryByText('Accept')).toBeNull()
  })

  it('shows no-data hint when auto_extracted_data is null and documentStatus is ready', () => {
    render(ExtractionPreview, {
      props: {
        pageId: 'page-1',
        documentId: 'doc-1',
        autoExtractedData: null,
        documentStatus: 'ready',
        onAccepted: vi.fn(),
        onReExtract: vi.fn(),
      },
    })

    expect(screen.getByText('No automatic extraction results.')).toBeTruthy()
    expect(screen.getByText(/OCR Settings/)).toBeTruthy()
  })

  it('does not show no-data hint when documentStatus is undefined (still loading)', () => {
    render(ExtractionPreview, {
      props: {
        pageId: 'page-1',
        documentId: 'doc-1',
        autoExtractedData: null,
        onAccepted: vi.fn(),
        onReExtract: vi.fn(),
      },
    })

    expect(screen.queryByText('No automatic extraction results.')).toBeNull()
  })

  it('does not show data summary when annotations already exist', () => {
    annotationStore.load('page-1', makeAutoData(3))
    const autoData = makeAutoData(2)

    render(ExtractionPreview, {
      props: {
        pageId: 'page-1',
        documentId: 'doc-1',
        autoExtractedData: autoData,
        documentStatus: 'ready',
        onAccepted: vi.fn(),
        onReExtract: vi.fn(),
      },
    })

    // Since annotationStore has elements, ExtractionPreview should not show
    expect(screen.queryByText('Automatic extraction results available')).toBeNull()
  })

  it('does not show no-data hint when annotations already exist', () => {
    annotationStore.load('page-1', makeAutoData(3))

    render(ExtractionPreview, {
      props: {
        pageId: 'page-1',
        documentId: 'doc-1',
        autoExtractedData: null,
        documentStatus: 'ready',
        onAccepted: vi.fn(),
        onReExtract: vi.fn(),
      },
    })

    expect(screen.queryByText('No automatic extraction results.')).toBeNull()
  })
})
