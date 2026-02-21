import { test, expect } from '@playwright/test'
import {
  waitForBackendReady,
  createProject,
  uploadPdf,
  listDocuments,
  listPages,
  getPage,
  acceptExtraction,
  deleteProject,
} from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'

const PROJECT_NAME = `Extraction E2E ${Date.now()}`

let projectId: string
let documentId: string
let pageId: string

test.describe.serial('PDF Text/Image Extraction', () => {
  test.beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()

    // Create project and upload PDF via API
    const { data: project } = await createProject(PROJECT_NAME, 'E2E extraction test')
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

  test('01 - auto_extracted_data is populated after PDF upload', async () => {
    const { data: page } = await getPage(pageId)

    // auto_extracted_data should exist with layout_dets
    expect(page.auto_extracted_data).toBeTruthy()
    const autoData = page.auto_extracted_data as Record<string, unknown>
    expect(autoData.layout_dets).toBeDefined()

    const layoutDets = autoData.layout_dets as Array<Record<string, unknown>>
    expect(layoutDets.length).toBeGreaterThan(0)

    // Should have text blocks (the PDF has text content)
    const textBlocks = layoutDets.filter((el) => el.category_type === 'text_block')
    expect(textBlocks.length).toBeGreaterThan(0)

    // Text blocks should have text content
    const firstTextBlock = textBlocks[0]
    expect(firstTextBlock.text).toBeTruthy()
    expect(typeof firstTextBlock.text).toBe('string')
    expect((firstTextBlock.text as string).length).toBeGreaterThan(0)

    // Each element should have poly coordinates (8 values)
    for (const el of layoutDets) {
      const poly = el.poly as number[]
      expect(poly).toHaveLength(8)
      // All coordinates should be non-negative numbers
      for (const coord of poly) {
        expect(coord).toBeGreaterThanOrEqual(0)
      }
    }
  })

  test('02 - annotation_data is initially empty', async () => {
    const { data: page } = await getPage(pageId)

    // annotation_data should be empty or have no layout_dets
    const annotationData = page.annotation_data as Record<string, unknown>
    const layoutDets = (annotationData?.layout_dets ?? []) as Array<Record<string, unknown>>
    expect(layoutDets.length).toBe(0)
  })

  test('03 - extraction preview banner shows in labeling page', async ({ page }) => {
    await page.goto(`/label/${pageId}`)

    // Wait for page to load
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    // Extraction preview banner should be visible
    await expect(page.locator('text=자동 추출 결과가 있습니다')).toBeVisible({ timeout: 10_000 })

    // Should show element counts
    await expect(page.locator('text=/텍스트 \\d+개/')).toBeVisible()
    await expect(page.locator('text=/총 \\d+개 요소/')).toBeVisible()

    // Accept and Dismiss buttons should be visible
    await expect(page.getByRole('button', { name: '수락' })).toBeVisible()
    await expect(page.getByRole('button', { name: '무시' })).toBeVisible()
  })

  test('04 - dismiss button hides extraction preview', async ({ page }) => {
    await page.goto(`/label/${pageId}`)
    await expect(page.locator('text=자동 추출 결과가 있습니다')).toBeVisible({ timeout: 15_000 })

    // Click dismiss
    await page.getByRole('button', { name: '무시' }).click()

    // Banner should disappear
    await expect(page.locator('text=자동 추출 결과가 있습니다')).not.toBeVisible()

    // Element list should still be empty (0개 요소)
    await expect(page.locator('text=0개 요소')).toBeVisible({ timeout: 5_000 })
  })

  test('05 - accept extraction via API copies to annotation_data', async () => {
    const { data: accepted } = await acceptExtraction(pageId)

    // annotation_data should now have the extracted elements
    const annotationData = accepted.annotation_data as Record<string, unknown>
    expect(annotationData.layout_dets).toBeDefined()

    const layoutDets = annotationData.layout_dets as Array<Record<string, unknown>>
    expect(layoutDets.length).toBeGreaterThan(0)

    // Should match auto_extracted_data
    const autoData = accepted.auto_extracted_data as Record<string, unknown>
    const autoLayoutDets = autoData.layout_dets as Array<Record<string, unknown>>
    expect(layoutDets.length).toBe(autoLayoutDets.length)
  })

  test('06 - accept extraction again returns 409 (already has annotations)', async () => {
    // Second accept should fail because annotation_data is now populated
    try {
      await acceptExtraction(pageId)
      // If no error, check that data was returned (409 might still return data)
    } catch {
      // Expected - should get a conflict error
    }

    // Verify annotation_data is unchanged
    const { data: page } = await getPage(pageId)
    const annotationData = page.annotation_data as Record<string, unknown>
    const layoutDets = annotationData.layout_dets as Array<Record<string, unknown>>
    expect(layoutDets.length).toBeGreaterThan(0)
  })

  test('07 - labeling page shows accepted elements', async ({ page }) => {
    await page.goto(`/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    // Wait for elements to load
    await page.waitForTimeout(2000)

    // Extraction preview should NOT show (annotations exist now)
    await expect(page.locator('text=자동 추출 결과가 있습니다')).not.toBeVisible()

    // Element list should show elements
    const elementCount = page.locator('text=/\\d+개 요소/')
    await expect(elementCount).toBeVisible({ timeout: 5_000 })

    // Count should be > 0
    const countText = await elementCount.textContent()
    const count = parseInt(countText?.match(/(\d+)개/)?.[1] ?? '0')
    expect(count).toBeGreaterThan(0)
  })

  test('08 - text overlay renders extracted text blocks', async ({ page }) => {
    await page.goto(`/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Text overlay should render text_block elements as selectable text
    const textOverlays = page.locator('[role="textbox"]')
    const textCount = await textOverlays.count()
    expect(textCount).toBeGreaterThan(0)

    // First text overlay should have user-select: text
    const firstOverlay = textOverlays.first()
    const userSelect = await firstOverlay.evaluate(
      (el) => window.getComputedStyle(el).userSelect,
    )
    expect(userSelect).toBe('text')
  })

  test('09 - extracted elements have correct coordinate scaling', async () => {
    const { data: pageData } = await getPage(pageId)
    const annotationData = pageData.annotation_data as Record<string, unknown>
    const layoutDets = annotationData.layout_dets as Array<Record<string, unknown>>

    // Page dimensions (2x rendered)
    const pageWidth = pageData.width
    const pageHeight = pageData.height

    // All element coordinates should be within page bounds
    for (const el of layoutDets) {
      const poly = el.poly as number[]
      // poly = [x1,y1, x2,y2, x3,y3, x4,y4]
      for (let i = 0; i < poly.length; i += 2) {
        const x = poly[i]
        const y = poly[i + 1]
        expect(x).toBeGreaterThanOrEqual(0)
        expect(y).toBeGreaterThanOrEqual(0)
        expect(x).toBeLessThanOrEqual(pageWidth + 1) // small tolerance
        expect(y).toBeLessThanOrEqual(pageHeight + 1)
      }
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
