import { test, expect } from '@playwright/test'
import {
  waitForBackendReady,
  waitForVllmReady,
  createProject,
  updateOcrConfig,
  testOcrConnection,
  uploadPdf,
  listDocuments,
  listPages,
  getPage,
  deleteProject,
} from '../../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../../helpers/pdf'

const VLLM_HOST = 'vllm'
const VLLM_PORT = 8000
const VLLM_MODEL = 'datalab-to/chandra'

let projectId: string
let documentId: string
let pageId: string

test.describe.serial('vLLM + Chandra OCR Extraction (GPU)', () => {
  test.beforeAll(async () => {
    await waitForBackendReady()
    await waitForVllmReady()
    await ensureTestPdf()
  })

  test('01 - create project and configure vLLM engine', async () => {
    const { data: project } = await createProject(
      `vLLM E2E ${Date.now()}`,
      'vLLM chandra extraction test',
    )
    projectId = project.id

    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: 'commercial_api',
      commercial_api: {
        provider: 'vllm',
        host: VLLM_HOST,
        port: VLLM_PORT,
        model: VLLM_MODEL,
      },
    })
    expect(status).toBe(200)
    expect(data.engine_type).toBe('commercial_api')
  })

  test('02 - vLLM connection test succeeds', async () => {
    const { data, status } = await testOcrConnection(projectId, {
      engine_type: 'commercial_api',
      commercial_api: {
        provider: 'vllm',
        host: VLLM_HOST,
        port: VLLM_PORT,
        model: VLLM_MODEL,
      },
    })
    expect(status).toBe(200)
    expect(data.success).toBe(true)
    expect(data.message).toContain('chandra')
  })

  test('03 - upload PDF and wait for extraction', async () => {
    const { data: doc } = await uploadPdf(projectId, getTestPdfPath())
    documentId = doc.id

    // Wait for Celery worker to complete OCR extraction (up to 5 min)
    const deadline = Date.now() + 300_000
    let lastStatus = 'unknown'
    while (Date.now() < deadline) {
      const { data: docs } = await listDocuments(projectId)
      if (docs.length > 0) {
        lastStatus = docs[0].status
        if (lastStatus === 'ready') {
          documentId = docs[0].id
          break
        }
        if (lastStatus === 'extraction_failed') {
          throw new Error('OCR extraction failed')
        }
      }
      await new Promise((r) => setTimeout(r, 5_000))
    }
    expect(lastStatus).toBe('ready')
  })

  test('04 - auto_extracted_data has layout elements', async () => {
    const { data: pages } = await listPages(documentId)
    expect(pages.length).toBeGreaterThan(0)
    pageId = pages[0].id

    const { data: page } = await getPage(pageId)
    expect(page.auto_extracted_data).toBeTruthy()

    const autoData = page.auto_extracted_data as Record<string, unknown>
    const layoutDets = autoData.layout_dets as Array<Record<string, unknown>>
    expect(layoutDets.length).toBeGreaterThan(0)

    // Should have text blocks with actual text content
    const textBlocks = layoutDets.filter(
      (el) => el.category_type === 'text_block' || el.category_type === 'title',
    )
    expect(textBlocks.length).toBeGreaterThan(0)

    const withText = textBlocks.filter((el) => {
      const text = (el.text as string) ?? ''
      return text.length > 0
    })
    expect(withText.length).toBeGreaterThan(0)
  })

  test('05 - extracted elements have valid poly coordinates', async () => {
    const { data: page } = await getPage(pageId)
    const autoData = page.auto_extracted_data as Record<string, unknown>
    const layoutDets = autoData.layout_dets as Array<Record<string, unknown>>

    for (const el of layoutDets) {
      const poly = el.poly as number[]
      expect(poly).toHaveLength(8)

      for (const coord of poly) {
        expect(coord).toBeGreaterThanOrEqual(0)
      }
    }
  })

  test('06 - extraction covers multiple category types', async () => {
    const { data: page } = await getPage(pageId)
    const autoData = page.auto_extracted_data as Record<string, unknown>
    const layoutDets = autoData.layout_dets as Array<Record<string, unknown>>

    const categories = new Set(layoutDets.map((el) => el.category_type as string))

    // Attention paper should have at least title and text blocks
    expect(categories.size).toBeGreaterThanOrEqual(2)
    expect(categories.has('text_block') || categories.has('title')).toBe(true)
  })

  test('07 - multiple pages extracted successfully', async () => {
    const { data: pages } = await listPages(documentId)

    // Check a few pages have extraction data
    const pagesToCheck = pages.slice(0, Math.min(3, pages.length))
    for (const pageSummary of pagesToCheck) {
      const { data: pageData } = await getPage(pageSummary.id)
      expect(pageData.auto_extracted_data).toBeTruthy()

      const autoData = pageData.auto_extracted_data as Record<string, unknown>
      const layoutDets = autoData.layout_dets as Array<Record<string, unknown>>
      expect(layoutDets.length).toBeGreaterThan(0)
    }
  })

  test.afterAll(async () => {
    try {
      await deleteProject(projectId)
    } catch {
      // Ignore cleanup errors
    }
  })
})
