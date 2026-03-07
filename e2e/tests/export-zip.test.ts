import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  waitForBackendReady,
  createProject,
  uploadPdf,
  listDocuments,
  listPages,
  acceptExtraction,
  exportProject,
  exportProjectZip,
  exportDocumentZip,
  deleteProject,
  setAuthToken,
  register,
} from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'

const ts = Date.now().toString().slice(-6)
const PROJECT_NAME = `Export ZIP E2E ${ts}`

let projectId: string
let documentId: string

describe('Export ZIP API', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()

    // Register and authenticate
    const { data: authData } = await register(`Export User ${ts}`, `export-${ts}`, `Pass${ts}!`)
    setAuthToken(authData.access_token)

    // Create project and upload PDF
    const { data: project } = await createProject(PROJECT_NAME, 'E2E export test')
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

    // Accept extraction for first page
    const { data: pages } = await listPages(documentId)
    if (pages.length > 0) {
      await acceptExtraction(pages[0].id)
    }
  }, 180_000)

  afterAll(async () => {
    if (projectId) {
      await deleteProject(projectId).catch(() => {})
    }
  })

  test('01 - JSON export returns valid data', async () => {
    const { data } = await exportProject(projectId)

    expect(data.project_name).toBe(PROJECT_NAME)
    expect(data.total_pages).toBeGreaterThan(0)
    expect(data.data.length).toBeGreaterThan(0)

    const entry = data.data[0] as Record<string, unknown>
    expect(entry.page_info).toBeDefined()
  })

  test('02 - project ZIP export returns valid ZIP file', async () => {
    const { blob, filename, status } = await exportProjectZip(projectId)

    expect(status).toBe(200)
    expect(blob.size).toBeGreaterThan(0)
    expect(blob.type).toBe('application/zip')
    expect(filename).toMatch(/^Export_ZIP_E2E_.*\.zip$/)
  })

  test('03 - document ZIP export returns valid ZIP file', async () => {
    const { blob, filename, status } = await exportDocumentZip(projectId, documentId)

    expect(status).toBe(200)
    expect(blob.size).toBeGreaterThan(0)
    expect(blob.type).toBe('application/zip')
    expect(filename).toMatch(/\.zip$/)
  })

  test('04 - project ZIP export 404 for non-existent project', async () => {
    const { status } = await exportProjectZip('00000000-0000-0000-0000-000000000000')
    expect(status).toBe(404)
  })

  test('05 - document ZIP export 404 for non-existent document', async () => {
    const { status } = await exportDocumentZip(
      projectId,
      '00000000-0000-0000-0000-000000000000',
    )
    expect(status).toBe(404)
  })
})
