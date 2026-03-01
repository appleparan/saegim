import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  waitForBackendReady,
  createProject,
  uploadPdf,
  listDocuments,
  listPages,
  getPage,
  acceptExtraction,
  forceAcceptExtraction,
  reExtractDocument,
  getDocumentStatus,
  deleteProject,
  updateAnnotation,
} from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'

const PROJECT_NAME = `Re-extract E2E ${Date.now()}`

let projectId: string
let documentId: string
let pageId: string

describe('Document Re-extract', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()

    // Create project and upload PDF (pdfminer default)
    const { data: project } = await createProject(PROJECT_NAME, 'E2E re-extract test')
    projectId = project.id

    const { data: doc } = await uploadPdf(projectId, getTestPdfPath())
    documentId = doc.id

    // Wait for processing to complete
    const deadline = Date.now() + 120_000
    while (Date.now() < deadline) {
      const { data: docs } = await listDocuments(projectId)
      if (docs.length > 0 && docs[0].status === 'ready') {
        documentId = docs[0].id
        break
      }
      await new Promise((r) => setTimeout(r, 2_000))
    }

    // Get first page ID
    const { data: pages } = await listPages(documentId)
    expect(pages.length).toBeGreaterThan(0)
    pageId = pages[0].id
  })

  test('01 - re-extract returns 200 with DocumentStatusResponse', async () => {
    const { data, status } = await reExtractDocument(documentId)

    expect(status).toBe(200)
    expect(data.id).toBe(documentId)
    // pdfminer is synchronous, so status should be ready immediately
    expect(data.status).toBe('ready')
    expect(data.total_pages).toBeGreaterThan(0)
  })

  test('02 - auto_extracted_data is refreshed after re-extract', async () => {
    const { data: page } = await getPage(pageId)

    expect(page.auto_extracted_data).toBeTruthy()
    const autoData = page.auto_extracted_data as Record<string, unknown>
    expect(autoData.layout_dets).toBeDefined()

    const layoutDets = autoData.layout_dets as Array<Record<string, unknown>>
    expect(layoutDets.length).toBeGreaterThan(0)

    // Text blocks should have text content
    const textBlocks = layoutDets.filter((el) => el.category_type === 'text_block')
    expect(textBlocks.length).toBeGreaterThan(0)
  })

  test('03 - re-extract preserves existing annotation_data', async () => {
    // First accept the extraction
    await acceptExtraction(pageId)

    // Add custom annotation
    const { data: before } = await getPage(pageId)
    const annotationData = before.annotation_data as Record<string, unknown>
    const layoutDets = annotationData.layout_dets as Array<Record<string, unknown>>
    const originalCount = layoutDets.length
    expect(originalCount).toBeGreaterThan(0)

    // Re-extract (should NOT touch annotation_data)
    const { status } = await reExtractDocument(documentId)
    expect(status).toBe(200)

    // Verify annotation_data is unchanged
    const { data: after } = await getPage(pageId)
    const afterAnnotation = after.annotation_data as Record<string, unknown>
    const afterLayoutDets = afterAnnotation.layout_dets as Array<Record<string, unknown>>
    expect(afterLayoutDets.length).toBe(originalCount)
  })

  test('04 - force-accept-extraction overwrites existing annotations', async () => {
    // annotation_data already has elements from test 03
    const { data: before } = await getPage(pageId)
    const beforeAnnotation = before.annotation_data as Record<string, unknown>
    const beforeDets = beforeAnnotation.layout_dets as Array<Record<string, unknown>>
    expect(beforeDets.length).toBeGreaterThan(0)

    // Force accept should overwrite with auto_extracted_data
    const { data: accepted, status } = await forceAcceptExtraction(pageId)
    expect(status).toBe(200)

    const acceptedAnnotation = accepted.annotation_data as Record<string, unknown>
    const acceptedDets = acceptedAnnotation.layout_dets as Array<Record<string, unknown>>
    expect(acceptedDets.length).toBeGreaterThan(0)

    // annotation_data should match auto_extracted_data
    const autoData = accepted.auto_extracted_data as Record<string, unknown>
    const autoDets = autoData.layout_dets as Array<Record<string, unknown>>
    expect(acceptedDets.length).toBe(autoDets.length)
  })

  test('05 - document status endpoint returns correct state', async () => {
    const { data, status } = await getDocumentStatus(documentId)

    expect(status).toBe(200)
    expect(data.id).toBe(documentId)
    expect(data.status).toBe('ready')
    expect(data.total_pages).toBeGreaterThan(0)
    expect(data.processed_pages).toBe(data.total_pages)
  })

  test('06 - re-extract with custom annotation shows both data', async () => {
    // Set a custom annotation that differs from auto-extracted
    const customAnnotation = {
      layout_dets: [
        {
          category_type: 'title',
          poly: [10, 10, 200, 10, 200, 50, 10, 50],
          text: 'Custom title element',
          anno_id: 0,
          order: 0,
        },
      ],
      page_attribute: {},
      extra: { relation: [] },
    }
    await updateAnnotation(pageId, customAnnotation)

    // Re-extract
    const { status } = await reExtractDocument(documentId)
    expect(status).toBe(200)

    // Verify: annotation_data has custom data, auto_extracted_data has fresh extraction
    const { data: page } = await getPage(pageId)
    const annotation = page.annotation_data as Record<string, unknown>
    const annotationDets = annotation.layout_dets as Array<Record<string, unknown>>
    expect(annotationDets.length).toBe(1)
    expect(annotationDets[0].text).toBe('Custom title element')

    const autoData = page.auto_extracted_data as Record<string, unknown>
    const autoDets = autoData.layout_dets as Array<Record<string, unknown>>
    expect(autoDets.length).toBeGreaterThan(1) // pdfminer extracts multiple elements
  })

  test('07 - force-accept after re-extract replaces custom annotation', async () => {
    // page now has custom annotation + fresh auto_extracted_data (from test 06)
    const { data: accepted, status } = await forceAcceptExtraction(pageId)
    expect(status).toBe(200)

    const annotation = accepted.annotation_data as Record<string, unknown>
    const layoutDets = annotation.layout_dets as Array<Record<string, unknown>>
    // Should have multiple elements from pdfminer, not the single custom one
    expect(layoutDets.length).toBeGreaterThan(1)

    // Verify it matches auto_extracted_data
    const autoData = accepted.auto_extracted_data as Record<string, unknown>
    const autoDets = autoData.layout_dets as Array<Record<string, unknown>>
    expect(layoutDets.length).toBe(autoDets.length)
  })

  test('08 - re-extract on non-existent document returns 404', async () => {
    const fakeId = '00000000-0000-0000-0000-000000000000'
    const { status } = await reExtractDocument(fakeId)
    expect(status).toBe(404)
  })

  // Browser tests (re-extract button, extraction preview banner with
  // force-accept UI, polling during extracting state) are verified
  // manually via Chrome DevTools MCP in Claude Code.

  afterAll(async () => {
    try {
      await deleteProject(projectId)
    } catch {
      // Ignore cleanup errors
    }
  })
})
