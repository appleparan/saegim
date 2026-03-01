import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, cleanup } from '@testing-library/svelte'
import ProjectPage from '../../../src/routes/projects/[id]/+page.svelte'
import type { DocumentResponse, ProjectResponse } from '$lib/api/types'

const mockProject: ProjectResponse = {
  id: 'proj-1',
  name: 'Test Project',
  description: 'A test project',
  created_at: '2025-01-01T00:00:00Z',
}

const mockDocument: DocumentResponse = {
  id: 'doc-1',
  project_id: 'proj-1',
  filename: 'test.pdf',
  total_pages: 3,
  status: 'ready',
  created_at: '2025-01-01T00:00:00Z',
}

const mockGetProject = vi.fn()
const mockGetOcrConfig = vi.fn()
const mockListDocuments = vi.fn()
const mockUploadDocument = vi.fn()
const mockDeleteDocument = vi.fn()
const mockListPages = vi.fn()

vi.mock('$app/state', () => ({
  page: {
    params: { id: 'proj-1' },
    url: new URL('http://localhost'),
    route: { id: '/projects/[id]' },
  },
}))

vi.mock('$lib/api/projects', () => ({
  getProject: (...args: unknown[]) => mockGetProject(...args),
  getOcrConfig: (...args: unknown[]) => mockGetOcrConfig(...args),
}))

vi.mock('$lib/api/documents', () => ({
  listDocuments: (...args: unknown[]) => mockListDocuments(...args),
  uploadDocument: (...args: unknown[]) => mockUploadDocument(...args),
  deleteDocument: (...args: unknown[]) => mockDeleteDocument(...args),
  listPages: (...args: unknown[]) => mockListPages(...args),
}))

vi.mock('$lib/api/client', () => ({
  NetworkError: class NetworkError extends Error {},
}))

function createDragEvent(type: string, files: File[] = []) {
  const event = new Event(type, { bubbles: true, cancelable: true })

  Object.defineProperty(event, 'dataTransfer', {
    value: {
      files,
      types: files.length > 0 ? ['Files'] : [],
      dropEffect: 'none',
    },
  })

  return event
}

function getDropZone(container: HTMLElement): HTMLElement {
  const zone = container.querySelector('[data-dropzone]') as HTMLElement
  expect(zone).toBeTruthy()
  return zone
}

describe('Project page drag-and-drop upload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetProject.mockResolvedValue(mockProject)
    mockGetOcrConfig.mockResolvedValue({ engine_type: 'pdfminer' })
    mockListDocuments.mockResolvedValue([])
    mockUploadDocument.mockResolvedValue(mockDocument)
  })

  afterEach(() => {
    cleanup()
  })

  it('renders the drop zone with data-dropzone attribute', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => {
      expect(getDropZone(container)).toBeTruthy()
    })
  })

  it('shows drag overlay on dragenter with files', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })
    const event = createDragEvent('dragenter', [pdfFile])

    dropZone.dispatchEvent(event)
    await vi.waitFor(() => {
      expect(screen.getByText('PDF 파일을 여기에 놓으세요')).toBeTruthy()
    })
  })

  it('hides drag overlay on dragleave', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })

    // Enter then leave
    dropZone.dispatchEvent(createDragEvent('dragenter', [pdfFile]))
    await vi.waitFor(() => {
      expect(screen.getByText('PDF 파일을 여기에 놓으세요')).toBeTruthy()
    })

    dropZone.dispatchEvent(createDragEvent('dragleave'))
    await vi.waitFor(() => {
      expect(screen.queryByText('PDF 파일을 여기에 놓으세요')).toBeNull()
    })
  })

  it('does not show overlay when dragging non-file content', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    // No files, types is empty
    const event = createDragEvent('dragenter')
    dropZone.dispatchEvent(event)

    // Overlay should not appear
    expect(screen.queryByText('PDF 파일을 여기에 놓으세요')).toBeNull()
  })

  it('uploads PDF on drop', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })

    // Enter and drop
    dropZone.dispatchEvent(createDragEvent('dragenter', [pdfFile]))
    dropZone.dispatchEvent(createDragEvent('drop', [pdfFile]))

    await vi.waitFor(() => {
      expect(mockUploadDocument).toHaveBeenCalledWith('proj-1', pdfFile)
    })
  })

  it('rejects non-PDF files on drop', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    const imageFile = new File(['image content'], 'photo.png', { type: 'image/png' })

    dropZone.dispatchEvent(createDragEvent('dragenter', [imageFile]))
    dropZone.dispatchEvent(createDragEvent('drop', [imageFile]))

    await vi.waitFor(() => {
      expect(screen.getByText('PDF 파일만 업로드할 수 있습니다.')).toBeTruthy()
    })
    expect(mockUploadDocument).not.toHaveBeenCalled()
  })

  it('accepts PDF by file extension even without correct MIME type', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    // File with wrong MIME but correct extension
    const pdfFile = new File(['pdf content'], 'document.pdf', {
      type: 'application/octet-stream',
    })

    dropZone.dispatchEvent(createDragEvent('dragenter', [pdfFile]))
    dropZone.dispatchEvent(createDragEvent('drop', [pdfFile]))

    await vi.waitFor(() => {
      expect(mockUploadDocument).toHaveBeenCalledWith('proj-1', pdfFile)
    })
  })

  it('shows error on upload failure', async () => {
    mockUploadDocument.mockRejectedValue(new Error('upload failed'))
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })

    dropZone.dispatchEvent(createDragEvent('dragenter', [pdfFile]))
    dropZone.dispatchEvent(createDragEvent('drop', [pdfFile]))

    await vi.waitFor(() => {
      expect(screen.getByText('PDF 업로드에 실패했습니다.')).toBeTruthy()
    })
  })

  it('hides overlay after drop', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })

    dropZone.dispatchEvent(createDragEvent('dragenter', [pdfFile]))
    await vi.waitFor(() => {
      expect(screen.getByText('PDF 파일을 여기에 놓으세요')).toBeTruthy()
    })

    dropZone.dispatchEvent(createDragEvent('drop', [pdfFile]))
    await vi.waitFor(() => {
      expect(screen.queryByText('PDF 파일을 여기에 놓으세요')).toBeNull()
    })
  })

  it('works with existing documents present', async () => {
    mockListDocuments.mockResolvedValue([mockDocument])
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    // Verify document is shown
    await vi.waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeTruthy()
    })

    // Drag and drop should still work
    const dropZone = getDropZone(container)
    const newPdf = new File(['new pdf'], 'new.pdf', { type: 'application/pdf' })

    dropZone.dispatchEvent(createDragEvent('dragenter', [newPdf]))
    await vi.waitFor(() => {
      expect(screen.getByText('PDF 파일을 여기에 놓으세요')).toBeTruthy()
    })
  })

  it('drops only the first file when multiple files are dropped', async () => {
    const { container } = render(ProjectPage)
    await vi.waitFor(() => getDropZone(container))

    const dropZone = getDropZone(container)
    const file1 = new File(['pdf1'], 'first.pdf', { type: 'application/pdf' })
    const file2 = new File(['pdf2'], 'second.pdf', { type: 'application/pdf' })

    dropZone.dispatchEvent(createDragEvent('dragenter', [file1, file2]))
    dropZone.dispatchEvent(createDragEvent('drop', [file1, file2]))

    await vi.waitFor(() => {
      expect(mockUploadDocument).toHaveBeenCalledTimes(1)
      expect(mockUploadDocument).toHaveBeenCalledWith('proj-1', file1)
    })
  })
})
