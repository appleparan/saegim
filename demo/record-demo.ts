/**
 * saegim Demo Recording Script
 *
 * Records a demo walkthrough of key features:
 * 1. Login
 * 2. Create project
 * 3. Upload PDF
 * 4. Label editor (draw bounding boxes, navigate tools)
 * 5. Task dashboard
 * 6. Export
 *
 * Prerequisites:
 *   - Docker Compose services running (make up)
 *   - Default admin/admin account available
 *
 * Usage:
 *   cd demo && npx playwright test --project=demo
 */

import { test, expect, type Page } from '@playwright/test'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SAMPLE_PDF = path.resolve(__dirname, '../e2e/sample_data/1706.03762v7.pdf')
const PAUSE_SHORT = 800
const PAUSE_MEDIUM = 1500
const PAUSE_LONG = 2500
const PAUSE_EXTRA = 4000

/** Utility: wait for a visual pause so the recording looks natural */
async function pause(page: Page, ms: number = PAUSE_MEDIUM) {
  await page.waitForTimeout(ms)
}

test('saegim demo walkthrough', async ({ page }) => {
  // ─── Scene 1: Login ───────────────────────────────────────
  await test.step('Login', async () => {
    await page.goto('/login')
    await pause(page, PAUSE_LONG)

    // Fill credentials
    await page.getByPlaceholder('admin').fill('admin')
    await pause(page, PAUSE_SHORT)
    await page.locator('input[type="password"]').fill('admin')
    await pause(page, PAUSE_SHORT)

    // If must_change_password is required, handle it
    await page.getByRole('button', { name: /로그인/ }).click()
    await pause(page, PAUSE_MEDIUM)

    // Handle password change if redirected
    const currentUrl = page.url()
    if (currentUrl.includes('security') || currentUrl.includes('change-password')) {
      // Change password flow
      const newPassword = 'DemoPass123!'
      const currentPwInput = page.locator('input[type="password"]').first()
      if (await currentPwInput.isVisible()) {
        await currentPwInput.fill('admin')
        await pause(page, PAUSE_SHORT)
      }
      const pwInputs = page.locator('input[type="password"]')
      const count = await pwInputs.count()
      if (count >= 2) {
        await pwInputs.nth(count - 2).fill(newPassword)
        await pause(page, PAUSE_SHORT)
        await pwInputs.nth(count - 1).fill(newPassword)
        await pause(page, PAUSE_SHORT)
        const submitBtn = page.getByRole('button', { name: /변경|저장|확인/ })
        if (await submitBtn.isVisible()) {
          await submitBtn.click()
          await pause(page, PAUSE_MEDIUM)
        }
      }
    }

    // Should be on home/projects page now
    await expect(page.getByText('프로젝트')).toBeVisible({ timeout: 10_000 })
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 2: Create Project ──────────────────────────────
  let projectCreated = false
  await test.step('Create Project', async () => {
    await page.getByRole('button', { name: /새 프로젝트/ }).click()
    await pause(page, PAUSE_MEDIUM)

    // Fill project form
    await page.getByLabel(/이름|프로젝트 이름/).fill('Attention Is All You Need')
    await pause(page, PAUSE_SHORT)

    const descInput = page.getByLabel(/설명/)
    if (await descInput.isVisible()) {
      await descInput.fill('논문 PDF 레이블링 데모 프로젝트')
      await pause(page, PAUSE_SHORT)
    }

    await page.getByRole('button', { name: /생성|만들기|확인/ }).click()
    await pause(page, PAUSE_LONG)
    projectCreated = true
  })

  // ─── Scene 3: Upload PDF ──────────────────────────────────
  await test.step('Upload PDF', async () => {
    // Navigate into the project if not already there
    if (!projectCreated) {
      const projectCard = page.getByText('Attention Is All You Need')
      if (await projectCard.isVisible()) {
        await projectCard.click()
        await pause(page, PAUSE_MEDIUM)
      }
    }

    // Click upload button
    const uploadBtn = page.getByRole('button', { name: /PDF 업로드|업로드/ })
    await expect(uploadBtn).toBeVisible({ timeout: 5_000 })

    // Use file chooser
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      uploadBtn.click(),
    ])
    await fileChooser.setFiles(SAMPLE_PDF)
    await pause(page, PAUSE_LONG)

    // Wait for document to appear in the list
    await expect(page.getByText('1706.03762v7_4p.pdf')).toBeVisible({ timeout: 30_000 })
    await pause(page, PAUSE_LONG)

    // Wait for processing to complete (status badge changes)
    // Poll until we see "준비됨" or page thumbnails appear
    await page.waitForTimeout(3000)

    // Expand document to show pages
    const docRow = page.getByText('1706.03762v7_4p.pdf')
    await docRow.click()
    await pause(page, PAUSE_EXTRA)
  })

  // ─── Scene 4: Label Editor ────────────────────────────────
  await test.step('Open Label Editor', async () => {
    // Click first page thumbnail to open editor
    const pageTile = page.locator('[data-page-tile]').first()
    if (await pageTile.isVisible({ timeout: 5_000 })) {
      await pageTile.click()
    } else {
      // Fallback: look for page 1 link
      const page1 = page.getByText(/페이지 1|Page 1|^1$/).first()
      if (await page1.isVisible()) {
        await page1.click()
      }
    }
    await pause(page, PAUSE_EXTRA)

    // Wait for canvas to load
    await page.waitForSelector('canvas', { timeout: 15_000 })
    await pause(page, PAUSE_LONG)
  })

  await test.step('Accept OCR extraction', async () => {
    // If extraction preview has an accept button, click it
    const acceptBtn = page.getByRole('button', { name: /수락/ })
    if (await acceptBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await acceptBtn.click()
      await pause(page, PAUSE_EXTRA)
    }
  })

  await test.step('Draw bounding box', async () => {
    // Switch to draw tool (press 2 or click draw button)
    await page.keyboard.press('2')
    await pause(page, PAUSE_MEDIUM)

    // Draw a bounding box on the canvas
    const canvas = page.locator('canvas').first()
    const box = await canvas.boundingBox()
    if (box) {
      const startX = box.x + box.width * 0.1
      const startY = box.y + box.height * 0.15
      const endX = box.x + box.width * 0.9
      const endY = box.y + box.height * 0.25

      await page.mouse.move(startX, startY)
      await pause(page, PAUSE_SHORT)
      await page.mouse.down()
      await page.mouse.move(endX, endY, { steps: 20 })
      await page.mouse.up()
      await pause(page, PAUSE_LONG)
    }

    // Switch back to select tool
    await page.keyboard.press('1')
    await pause(page, PAUSE_MEDIUM)
  })

  await test.step('Show zoom controls', async () => {
    // Zoom in
    const zoomIn = page.getByRole('button', { name: '+' })
    if (await zoomIn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await zoomIn.click()
      await pause(page, PAUSE_SHORT)
      await zoomIn.click()
      await pause(page, PAUSE_MEDIUM)

      // Zoom back out
      const zoomOut = page.getByRole('button', { name: '-' })
      await zoomOut.click()
      await pause(page, PAUSE_SHORT)
      await zoomOut.click()
      await pause(page, PAUSE_MEDIUM)
    }
  })

  await test.step('Toggle reading order', async () => {
    // Press R to show reading order overlay
    await page.keyboard.press('r')
    await pause(page, PAUSE_LONG)

    // Toggle off
    await page.keyboard.press('r')
    await pause(page, PAUSE_MEDIUM)
  })

  await test.step('Save annotations', async () => {
    // Ctrl+S to save
    await page.keyboard.press('Control+s')
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 5: Navigate to next page ──────────────────────
  await test.step('Navigate pages', async () => {
    // Press E to go to next page
    await page.keyboard.press('e')
    await pause(page, PAUSE_LONG)

    // Go back
    await page.keyboard.press('q')
    await pause(page, PAUSE_MEDIUM)
  })

  // ─── Scene 6: Go back and show project overview ──────────
  await test.step('Back to project', async () => {
    // Navigate back using breadcrumb or browser back
    const breadcrumb = page.getByText('Attention Is All You Need').first()
    if (await breadcrumb.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await breadcrumb.click()
    } else {
      await page.goBack()
    }
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 7: Show progress dashboard ────────────────────
  await test.step('Progress dashboard', async () => {
    const progressBtn = page.getByRole('button', { name: /작업 현황/ }).or(
      page.getByRole('link', { name: /작업 현황/ })
    )
    if (await progressBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await progressBtn.click()
      await pause(page, PAUSE_EXTRA)

      // Go back
      await page.goBack()
      await pause(page, PAUSE_MEDIUM)
    }
  })

  // ─── Scene 8: Export ──────────────────────────────────────
  await test.step('Show export', async () => {
    const exportBtn = page.getByRole('button', { name: /전체 내보내기|내보내기|Export/ })
    if (await exportBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      // Hover to show it's there
      await exportBtn.hover()
      await pause(page, PAUSE_LONG)
    }
  })

  // ─── Scene 9: Task dashboard ──────────────────────────────
  await test.step('Task dashboard', async () => {
    const tasksLink = page.getByRole('link', { name: /내 작업|작업/ })
    if (await tasksLink.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await tasksLink.click()
      await pause(page, PAUSE_LONG)
    }
  })

  // ─── Final: Back to home ──────────────────────────────────
  await test.step('Final - home', async () => {
    await page.goto('/')
    await pause(page, PAUSE_EXTRA)
  })
})
