/**
 * Demo: Label Editor
 *
 * Shows: OCR extraction → element inspection → element index overlay
 *        → bounding box drawing → reading order → save
 *
 * Data setup via API (invisible in video):
 *   - Ensures project, OCR engine, and uploaded document exist
 */

import { test, expect } from '@playwright/test'
import {
  pause,
  apiLogin,
  apiEnsureFullSetup,
  apiGetPages,
  PAUSE_SHORT,
  PAUSE_MEDIUM,
  PAUSE_LONG,
  PAUSE_EXTRA,
  DEMO_PROJECT_NAME,
} from './helpers'

let projectId: string
let documentId: string
let pages: Array<{ id: string; page_no: number }>

test.beforeAll(async () => {
  const { token } = await apiLogin()
  const setup = await apiEnsureFullSetup(token)
  projectId = setup.projectId
  documentId = setup.documentId
  pages = await apiGetPages(token, documentId)
})

test('Label editor: extraction, annotation, overlays', async ({ page }) => {
  // ─── Navigate to project and open page ───────────────────────
  await test.step('Navigate to label editor', async () => {
    await page.goto('/')
    await pause(page, PAUSE_MEDIUM)

    const projectLink = page.getByRole('link', { name: new RegExp(DEMO_PROJECT_NAME) })
    await projectLink.click()
    await pause(page, PAUSE_LONG)

    // Expand document
    const docRow = page.getByText('1706.03762v7_7p_9p.pdf')
    await expect(docRow).toBeVisible({ timeout: 10_000 })
    await docRow.click()
    await pause(page, PAUSE_MEDIUM)

    // Open page 3 (Figure 1: Transformer architecture)
    const pageTiles = page.locator('[data-page-tile]')
    const tileCount = await pageTiles.count()
    if (tileCount >= 3) {
      await pageTiles.nth(2).click()
    } else if (tileCount > 0) {
      await pageTiles.first().click()
    }
    await pause(page, PAUSE_EXTRA)

    await page.waitForSelector('canvas', { timeout: 15_000 })
    await pause(page, PAUSE_LONG)
  })

  // ─── Accept extraction — Figure page ─────────────────────────
  await test.step('Accept Gemini OCR extraction — Figure', async () => {
    const acceptBtn = page.getByRole('button', { name: /수락/ })
    await expect(acceptBtn).toBeVisible({ timeout: 60_000 })
    await pause(page, PAUSE_MEDIUM)

    await acceptBtn.click()
    await pause(page, PAUSE_EXTRA)
  })

  await test.step('Inspect figure element', async () => {
    const figureEl = page.getByText(/그림|figure/i).first()
    if (await figureEl.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await figureEl.click()
      await pause(page, PAUSE_LONG)
    }
    await pause(page, PAUSE_LONG)
  })

  // ─── Navigate to table page ──────────────────────────────────
  await test.step('Navigate to page with Table', async () => {
    await page.keyboard.press('e')
    await pause(page, PAUSE_LONG)
    await page.keyboard.press('e')
    await pause(page, PAUSE_LONG)

    await page.waitForSelector('canvas', { timeout: 15_000 })
    await pause(page, PAUSE_MEDIUM)
  })

  await test.step('Accept Gemini OCR extraction — Table', async () => {
    const acceptBtn = page.getByRole('button', { name: /수락/ })
    if (await acceptBtn.isVisible({ timeout: 60_000 }).catch(() => false)) {
      await acceptBtn.click()
      await pause(page, PAUSE_EXTRA)
    }
  })

  await test.step('Inspect table element', async () => {
    const tableEl = page.getByText(/테이블|table/i).first()
    if (await tableEl.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await tableEl.click()
      await pause(page, PAUSE_LONG)
    }
    await pause(page, PAUSE_LONG)
  })

  // ─── Element index overlay ───────────────────────────────────
  await test.step('Toggle element index overlay', async () => {
    await page.keyboard.press('i')
    await pause(page, PAUSE_LONG)
    await pause(page, PAUSE_EXTRA)

    await page.keyboard.press('i')
    await pause(page, PAUSE_MEDIUM)
  })

  // ─── Draw bounding box ──────────────────────────────────────
  await test.step('Draw bounding box', async () => {
    await page.keyboard.press('2')
    await pause(page, PAUSE_MEDIUM)

    const canvas = page.locator('canvas').first()
    const box = await canvas.boundingBox()
    if (box) {
      const startX = box.x + box.width * 0.1
      const startY = box.y + box.height * 0.7
      const endX = box.x + box.width * 0.9
      const endY = box.y + box.height * 0.85

      await page.mouse.move(startX, startY)
      await pause(page, PAUSE_SHORT)
      await page.mouse.down()
      await page.mouse.move(endX, endY, { steps: 20 })
      await page.mouse.up()
      await pause(page, PAUSE_LONG)
    }

    await page.keyboard.press('1')
    await pause(page, PAUSE_MEDIUM)
  })

  // ─── Reading order ───────────────────────────────────────────
  await test.step('Toggle reading order', async () => {
    await page.keyboard.press('r')
    await pause(page, PAUSE_LONG)

    await page.keyboard.press('r')
    await pause(page, PAUSE_MEDIUM)
  })

  // ─── Save ────────────────────────────────────────────────────
  await test.step('Save annotations', async () => {
    await page.keyboard.press('Control+s')
    await pause(page, PAUSE_LONG)
  })
})
