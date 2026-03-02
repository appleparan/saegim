import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  waitForBackendReady,
  createProject,
  uploadPdf,
  listDocuments,
  listPages,
  getPage,
  extractText,
  deleteProject,
} from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'

describe('Extract Text (On-demand OCR)', () => {
  let projectId: string
  let documentId: string
  let pageId: string

  beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()

    const { data: project } = await createProject(
      `ExtractText E2E ${Date.now()}`,
      'Extract-text test',
    )
    projectId = project.id

    const { data: doc } = await uploadPdf(projectId, getTestPdfPath())
    documentId = doc.id

    // Wait for processing
    const deadline = Date.now() + 120_000
    while (Date.now() < deadline) {
      const { data: docs } = await listDocuments(projectId)
      if (docs.length > 0 && docs[0].status === 'ready') {
        documentId = docs[0].id
        break
      }
      await new Promise((r) => setTimeout(r, 2_000))
    }

    const { data: pages } = await listPages(documentId)
    expect(pages.length).toBeGreaterThan(0)
    pageId = pages[0].id
  })

  afterAll(async () => {
    try {
      await deleteProject(projectId)
    } catch {
      // Ignore cleanup errors
    }
  })

  test('extract-text with non-existent page returns 404', async () => {
    const fakePageId = '00000000-0000-0000-0000-000000000000'
    const poly = [0, 0, 100, 0, 100, 50, 0, 50]
    const { status } = await extractText(fakePageId, poly)
    expect(status).toBe(404)
  })

  test('extract-text without OCR provider configured returns 503', async () => {
    // The test project has no OCR engine configured, so this should return 503
    const { data: page } = await getPage(pageId)
    const poly = [0, 0, page.width / 2, 0, page.width / 2, page.height / 2, 0, page.height / 2]
    const { status } = await extractText(pageId, poly)
    expect(status).toBe(503)
  })

  test('extract-text validates poly field requires exactly 8 values', async () => {
    // poly with wrong number of values should return 422 (validation error)
    const shortPoly = [0, 0, 100, 0]
    const { status } = await extractText(pageId, shortPoly)
    expect(status).toBe(422)
  })
})
