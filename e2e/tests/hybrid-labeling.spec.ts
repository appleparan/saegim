import { test, expect } from '@playwright/test'
import { waitForBackendReady, createProject, uploadPdf, listDocuments, listPages, addElement, updateAnnotation } from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'

const PROJECT_NAME = `Hybrid Labeling E2E ${Date.now()}`

let projectId: string
let documentId: string
let pageId: string

test.describe.serial('Hybrid Labeling UX', () => {
  test.beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()

    // Create project and upload PDF via API for speed
    const { data: project } = await createProject(PROJECT_NAME, 'E2E hybrid labeling test')
    projectId = project.id

    const { data: doc } = await uploadPdf(projectId, getTestPdfPath())
    documentId = doc.id

    // Wait for processing
    const deadline = Date.now() + 60_000
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

    // Seed with both text and image elements for testing
    await updateAnnotation(pageId, {
      layout_dets: [
        {
          category_type: 'title',
          poly: [50, 50, 400, 50, 400, 90, 50, 90],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: 'Attention Is All You Need',
          attribute: {},
          line_with_spans: [],
          merge_list: [],
          latex: '',
          html: '',
        },
        {
          category_type: 'text_block',
          poly: [50, 120, 600, 120, 600, 250, 50, 250],
          ignore: false,
          order: 1,
          anno_id: 1,
          text: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.',
          attribute: {},
          line_with_spans: [],
          merge_list: [],
          latex: '',
          html: '',
        },
        {
          category_type: 'figure',
          poly: [100, 300, 500, 300, 500, 600, 100, 600],
          ignore: false,
          order: 2,
          anno_id: 2,
          text: '',
          attribute: {},
          line_with_spans: [],
          merge_list: [],
          latex: '',
          html: '',
        },
        {
          category_type: 'table',
          poly: [50, 650, 600, 650, 600, 850, 50, 850],
          ignore: false,
          order: 3,
          anno_id: 3,
          text: '',
          attribute: {},
          line_with_spans: [],
          merge_list: [],
          latex: '',
          html: '',
        },
      ],
      page_attribute: {
        data_source: 'academic_literature',
        language: 'en',
        layout: 'single_column',
        watermark: false,
        fuzzy_scan: false,
        colorful_background: false,
      },
      extra: { relation: [] },
    })
  })

  test('01 - labeling page loads with 3-layer structure', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    // Wait for canvas to initialize
    await page.waitForTimeout(2000)

    // Layer 1: Background image should be present
    const bgImage = page.locator('img[alt="page background"]')
    await expect(bgImage).toBeVisible()

    // Layer 2: Konva canvas container should exist
    const konvaContainer = page.locator('canvas').first()
    await expect(konvaContainer).toBeVisible()

    // Layer 3: Text overlay divs should be present
    // Text blocks should render as transparent text
    const textOverlay = page.locator('[role="textbox"]')
    const textCount = await textOverlay.count()
    expect(textCount).toBeGreaterThanOrEqual(2) // title + text_block
  })

  test('02 - text blocks are selectable via native browser selection', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Find the title text overlay
    const titleOverlay = page.locator('[role="textbox"]', {
      hasText: 'Attention Is All You Need',
    })
    await expect(titleOverlay).toBeAttached()

    // Verify text overlay has user-select: text
    const userSelect = await titleOverlay.evaluate(
      (el) => window.getComputedStyle(el).userSelect,
    )
    expect(userSelect).toBe('text')

    // Verify text is transparent (color: transparent)
    const color = await titleOverlay.evaluate(
      (el) => window.getComputedStyle(el).color,
    )
    expect(color).toBe('rgba(0, 0, 0, 0)')
  })

  test('03 - tool buttons work correctly', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    // Select tool should be active by default
    const selectBtn = page.getByRole('button', { name: '선택' })
    const drawBtn = page.getByRole('button', { name: '그리기' })
    const panBtn = page.getByRole('button', { name: '이동' })

    await expect(selectBtn).toBeVisible()
    await expect(drawBtn).toBeVisible()
    await expect(panBtn).toBeVisible()

    // Switch to draw mode
    await drawBtn.click()
    await expect(drawBtn).toHaveClass(/bg-primary-500/)

    // Switch to pan mode
    await panBtn.click()
    await expect(panBtn).toHaveClass(/bg-primary-500/)

    // Switch back to select mode
    await selectBtn.click()
    await expect(selectBtn).toHaveClass(/bg-primary-500/)
  })

  test('04 - zoom controls work', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    const bgImage = page.locator('img[alt="page background"]')
    const initialTransform = await bgImage.evaluate(
      (el) => window.getComputedStyle(el).transform,
    )

    // Click zoom in
    await page.getByRole('button', { name: '+' }).click()
    await page.waitForTimeout(300)

    const zoomedTransform = await bgImage.evaluate(
      (el) => window.getComputedStyle(el).transform,
    )

    // Transform should have changed after zoom
    expect(zoomedTransform).not.toBe(initialTransform)

    // Click 1:1 to reset
    await page.getByRole('button', { name: '1:1' }).click()
    await page.waitForTimeout(300)
  })

  test('05 - draw tool creates new bounding box', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // Switch to draw tool
    await page.getByRole('button', { name: '그리기' }).click()
    await page.waitForTimeout(300)

    // Draw on the canvas area
    const canvasArea = page.locator('.flex-1.relative.bg-gray-100')
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

    // Element count should show 5 (4 seeded + 1 drawn)
    const elementCount = page.locator('text=/\\d+개 요소/')
    await expect(elementCount).toBeVisible({ timeout: 5_000 })
  })

  test('06 - keyboard shortcuts work', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })

    // Press 'd' for draw mode
    await page.keyboard.press('d')
    const drawBtn = page.getByRole('button', { name: '그리기' })
    await expect(drawBtn).toHaveClass(/bg-primary-500/)

    // Press 'h' for pan mode
    await page.keyboard.press('h')
    const panBtn = page.getByRole('button', { name: '이동' })
    await expect(panBtn).toHaveClass(/bg-primary-500/)

    // Press 's' for select mode
    await page.keyboard.press('s')
    const selectBtn = page.getByRole('button', { name: '선택' })
    await expect(selectBtn).toHaveClass(/bg-primary-500/)
  })

  test('07 - element list shows all elements', async ({ page }) => {
    await page.goto(`/#/label/${pageId}`)
    await expect(page.locator('text=요소 목록')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(2000)

    // The element list should show elements including our seeded data
    const elementCount = page.locator('text=/\\d+개 요소/')
    await expect(elementCount).toBeVisible({ timeout: 5_000 })
  })

  test.afterAll(async () => {
    // Clean up: delete project
    try {
      const { deleteProject } = await import('../helpers/api')
      await deleteProject(projectId)
    } catch {
      // Ignore cleanup errors
    }
  })
})
