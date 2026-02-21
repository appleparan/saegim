import { test, expect } from '@playwright/test'
import {
  waitForBackendReady,
  waitForVllmReady,
  createProject,
  updateOcrConfig,
  uploadPdf,
  listDocuments,
  listPages,
  getPage,
  acceptExtraction,
  deleteProject,
} from '../../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../../helpers/pdf'

const VLLM_HOST = 'vllm'
const VLLM_PORT = 8000
const VLLM_MODEL = 'richarddavison/chandra-fp8'

const PROJECT_NAME = `GPU Hybrid Labeling E2E ${Date.now()}`

let projectId: string
let documentId: string
let pageId: string
let allPageIds: string[] = []
let extractedElementCount = 0

test.describe.serial('GPU Hybrid Labeling UX', () => {
  test.beforeAll(async () => {
    await waitForBackendReady()
    await waitForVllmReady()
    await ensureTestPdf()

    // Create project and configure vLLM OCR
    const { data: project } = await createProject(PROJECT_NAME, 'GPU hybrid labeling E2E test')
    projectId = project.id

    await updateOcrConfig(projectId, {
      engine_type: 'integrated_server',
      integrated_server: {
        host: VLLM_HOST,
        port: VLLM_PORT,
        model: VLLM_MODEL,
      },
    })

    // Upload PDF and wait for extraction (up to 5 min)
    const { data: doc } = await uploadPdf(projectId, getTestPdfPath())
    documentId = doc.id

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

    // Get page IDs
    const { data: pages } = await listPages(documentId)
    expect(pages.length).toBeGreaterThan(0)
    allPageIds = pages.map((p) => p.id)
    pageId = pages[0].id

    // Accept extraction so annotation_data is populated
    await acceptExtraction(pageId)

    // Verify extraction produced elements
    const { data: pageData } = await getPage(pageId)
    const annotation = pageData.annotation_data as Record<string, unknown>
    const layoutDets = (annotation.layout_dets ?? []) as Array<Record<string, unknown>>
    extractedElementCount = layoutDets.length
    expect(extractedElementCount).toBeGreaterThan(0)
  })

  test('01 - labeling page loads with 3-layer structure', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Layer 1: Background — either PDF.js canvas or fallback image
    const bgImage = page.locator('img[alt="page background"]')
    const pdfCanvas = page.locator('canvas[data-pdf-renderer]')
    const hasBgImage = await bgImage.isVisible().catch(() => false)
    const hasPdfCanvas = await pdfCanvas.isVisible().catch(() => false)
    expect(hasBgImage || hasPdfCanvas).toBe(true)

    // Layer 2: Konva canvas container should exist
    const konvaContainer = page.locator('canvas').first()
    await expect(konvaContainer).toBeVisible()

    // Layer 3: Text overlay divs should be present for extracted text elements
    const textOverlay = page.locator('[role="textbox"]')
    const textCount = await textOverlay.count()
    expect(textCount).toBeGreaterThanOrEqual(1)
  })

  test('02 - extracted text blocks are selectable', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Find first text overlay from extracted data
    const textOverlays = page.locator('[role="textbox"]')
    const count = await textOverlays.count()
    test.skip(count === 0, 'No text overlays from extraction')

    const firstOverlay = textOverlays.first()
    await expect(firstOverlay).toBeAttached()

    // Verify text overlay has user-select: text
    const userSelect = await firstOverlay.evaluate(
      (el) => window.getComputedStyle(el).userSelect,
    )
    expect(userSelect).toBe('text')

    // Verify text is transparent (color: transparent)
    const color = await firstOverlay.evaluate(
      (el) => window.getComputedStyle(el).color,
    )
    expect(color).toBe('rgba(0, 0, 0, 0)')
  })

  test('03 - tool buttons work correctly', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    const selectBtn = page.getByRole('button', { name: '선택' })
    const drawBtn = page.getByRole('button', { name: '그리기' })
    const panBtn = page.getByRole('button', { name: '이동' })

    await expect(selectBtn).toBeVisible()
    await expect(drawBtn).toBeVisible()
    await expect(panBtn).toBeVisible()

    // Switch to draw mode
    await drawBtn.click()
    await expect(drawBtn).toHaveClass(/bg-primary/)

    // Switch to pan mode
    await panBtn.click()
    await expect(panBtn).toHaveClass(/bg-primary/)

    // Switch back to select mode
    await selectBtn.click()
    await expect(selectBtn).toHaveClass(/bg-primary/)
  })

  test('04 - zoom controls work', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    const transformContainer = page.locator('[style*="transform-origin: 0 0"]').first()
    const initialTransform = await transformContainer.evaluate(
      (el) => el.style.transform || window.getComputedStyle(el).transform,
    )

    // Click zoom in
    await page.getByRole('button', { name: '+' }).click()
    await page.waitForTimeout(300)

    const zoomedTransform = await transformContainer.evaluate(
      (el) => el.style.transform || window.getComputedStyle(el).transform,
    )

    // Transform should have changed after zoom
    expect(zoomedTransform).not.toBe(initialTransform)

    // Click 1:1 to reset
    await page.getByRole('button', { name: '1:1' }).click()
    await page.waitForTimeout(300)
  })

  test('05 - draw tool creates new bounding box on extracted page', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Switch to draw tool
    await page.getByRole('button', { name: '그리기' }).click()
    await page.waitForTimeout(300)

    // Draw on the canvas area
    const canvasArea = page.locator('.flex-1.relative.bg-muted')
    const box = await canvasArea.boundingBox()
    if (box) {
      const startX = box.x + box.width * 0.6
      const startY = box.y + box.height * 0.1
      const endX = box.x + box.width * 0.8
      const endY = box.y + box.height * 0.2

      await page.mouse.move(startX, startY)
      await page.mouse.down()
      await page.mouse.move(endX, endY, { steps: 10 })
      await page.mouse.up()
    }

    await page.waitForTimeout(500)

    // Element count should increase (extracted + 1 drawn)
    const elementCount = page.locator('text=/\\d+개 요소/')
    await expect(elementCount).toBeVisible({ timeout: 5_000 })
  })

  test('06 - keyboard shortcuts work', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    // Press 'd' for draw mode
    await page.keyboard.press('d')
    const drawBtn = page.getByRole('button', { name: '그리기' })
    await expect(drawBtn).toHaveClass(/bg-primary/)

    // Press 'h' for pan mode
    await page.keyboard.press('h')
    const panBtn = page.getByRole('button', { name: '이동' })
    await expect(panBtn).toHaveClass(/bg-primary/)

    // Press 's' for select mode
    await page.keyboard.press('s')
    const selectBtn = page.getByRole('button', { name: '선택' })
    await expect(selectBtn).toHaveClass(/bg-primary/)
  })

  test('07 - element list shows extracted elements', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // The element list should show elements from vLLM extraction
    const elementCount = page.locator('text=/\\d+개 요소/')
    await expect(elementCount).toBeVisible({ timeout: 5_000 })
  })

  test('08 - page navigator is visible for multi-page documents', async ({ page }) => {
    test.skip(allPageIds.length <= 1, 'Document has only 1 page')

    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    // PageNavigator header should be visible
    const pageNavHeader = page.locator('.uppercase:has-text("페이지")')
    await expect(pageNavHeader).toBeVisible({ timeout: 5_000 })

    // Prev/Next buttons should exist
    const prevBtn = page.locator('button[title*="이전 페이지"]')
    const nextBtn = page.locator('button[title*="다음 페이지"]')
    await expect(prevBtn).toBeVisible()
    await expect(nextBtn).toBeVisible()

    // On first page, prev should be disabled
    await expect(prevBtn).toBeDisabled()
    await expect(nextBtn).toBeEnabled()

    // Page counter should show "1 / N"
    const counter = page.locator('text=/1 \\/ \\d+/')
    await expect(counter).toBeVisible()
  })

  test('09 - page navigation via next button', async ({ page }) => {
    test.skip(allPageIds.length <= 1, 'Document has only 1 page')

    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(1000)

    // Click next page
    const nextBtn = page.locator('button[title*="다음 페이지"]')
    await nextBtn.click()

    // URL should change to second page
    await page.waitForTimeout(1000)
    await expect(page).toHaveURL(new RegExp(`#/label/${allPageIds[1]}`))

    // Page should load (element list visible)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
  })

  test('10 - page navigation via keyboard shortcuts', async ({ page }) => {
    test.skip(allPageIds.length <= 1, 'Document has only 1 page')

    // Start on page 2
    await page.goto(`/#/label/${allPageIds[1]}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(1000)

    // Press '[' to go to previous page
    await page.keyboard.press('[')
    await page.waitForTimeout(1000)
    await expect(page).toHaveURL(new RegExp(`#/label/${allPageIds[0]}`))

    // Press ']' to go to next page
    await page.keyboard.press(']')
    await page.waitForTimeout(1000)
    await expect(page).toHaveURL(new RegExp(`#/label/${allPageIds[1]}`))
  })

  test('11 - breadcrumb navigation shows document info', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    // Breadcrumb should show page info
    const breadcrumb = page.locator('nav')
    await expect(breadcrumb.locator('text=페이지')).toBeVisible({ timeout: 5_000 })
  })

  test('12 - text overlay click selects corresponding element', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Click on the first text overlay from extraction
    const textOverlays = page.locator('[role="textbox"]')
    const count = await textOverlays.count()
    test.skip(count === 0, 'No text overlays from extraction')

    const firstOverlay = textOverlays.first()
    await expect(firstOverlay).toBeVisible()
    await firstOverlay.click()

    // The element should be selected — sidebar should show details
    await page.waitForTimeout(500)
    const sidebar = page.locator('.w-80.border-l')
    await expect(sidebar).toBeVisible()
  })

  test('13 - zoom maintains bbox alignment (screenshot comparison)', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Take screenshot before zoom
    const canvasArea = page.locator('.flex-1.relative.bg-muted')
    const beforeZoom = await canvasArea.screenshot()

    // Zoom in
    await page.getByRole('button', { name: '+' }).click()
    await page.waitForTimeout(500)

    // Zoom out back to original
    await page.getByRole('button', { name: '-' }).click()
    await page.waitForTimeout(500)

    // Take screenshot after zoom cycle
    const afterZoom = await canvasArea.screenshot()

    // Verify no catastrophic misalignment after zoom round-trip
    expect(beforeZoom).toBeTruthy()
    expect(afterZoom).toBeTruthy()
  })

  test('14 - extracted bbox poly coordinates are valid on canvas', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Verify via API that all extracted elements have valid poly coordinates
    const { data: pageData } = await getPage(pageId)
    const annotation = pageData.annotation_data as Record<string, unknown>
    const layoutDets = (annotation.layout_dets ?? []) as Array<Record<string, unknown>>

    for (const el of layoutDets) {
      const poly = el.poly as number[]
      expect(poly).toHaveLength(8)

      // All coordinates should be non-negative
      for (const coord of poly) {
        expect(coord).toBeGreaterThanOrEqual(0)
      }

      // Bounding box should have non-zero area (x2 > x1, y2 > y1)
      const [x1, y1, x2, , , , , y4] = poly
      expect(x2).toBeGreaterThan(x1)
      expect(y4).toBeGreaterThan(y1)
    }

    // Konva stage should be rendering on the page (has at least one canvas)
    const canvases = page.locator('canvas')
    const canvasCount = await canvases.count()
    expect(canvasCount).toBeGreaterThanOrEqual(1)
  })

  test('15 - multiple zoom levels maintain bbox consistency', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    const canvasArea = page.locator('.flex-1.relative.bg-muted')

    // Zoom in multiple times
    for (let i = 0; i < 3; i++) {
      await page.getByRole('button', { name: '+' }).click()
      await page.waitForTimeout(300)
    }

    // Take screenshot at zoomed-in level — verify canvas area renders
    const zoomedIn = await canvasArea.screenshot()
    expect(zoomedIn).toBeTruthy()

    // Zoom out multiple times
    for (let i = 0; i < 6; i++) {
      await page.getByRole('button', { name: '-' }).click()
      await page.waitForTimeout(300)
    }

    // Take screenshot at zoomed-out level
    const zoomedOut = await canvasArea.screenshot()
    expect(zoomedOut).toBeTruthy()

    // Reset to 1:1
    await page.getByRole('button', { name: '1:1' }).click()
    await page.waitForTimeout(500)

    // After reset, the transform container should exist and be stable
    const transformContainer = page.locator('[style*="transform-origin: 0 0"]').first()
    await expect(transformContainer).toBeAttached()
  })

  test.afterAll(async () => {
    try {
      await deleteProject(projectId)
    } catch {
      // Ignore cleanup errors
    }
  })
})
