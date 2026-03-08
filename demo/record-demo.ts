/**
 * saegim Demo Recording Script
 *
 * Records a demo walkthrough of key features:
 * 1. Login → Dark mode
 * 2. Create project
 * 3. OCR settings (Gemini engine)
 * 4. Upload PDF
 * 5. Label editor — figure/table recognition with Gemini OCR
 * 6. Reading order, save, export
 *
 * Prerequisites:
 *   - Docker Compose services running (make up)
 *   - GEMINI_API_KEY set in .env
 *   - Default admin/admin account available
 *
 * Usage:
 *   cd demo && bunx playwright test --project=demo
 */

import { test, expect, type Page } from '@playwright/test'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SAMPLE_PDF = path.resolve(__dirname, '../e2e/sample_data/1706.03762v7_7p_9p.pdf')
const PAUSE_SHORT = 800
const PAUSE_MEDIUM = 1500
const PAUSE_LONG = 2500
const PAUSE_EXTRA = 4000

async function pause(page: Page, ms: number = PAUSE_MEDIUM) {
  await page.waitForTimeout(ms)
}

const API_URL = process.env.API_URL ?? 'http://localhost:15000'
const PASSWORDS_TO_TRY = ['admin', 'DemoPass2025']
const NEW_PASSWORD = 'DemoPass2025'

async function findWorkingPassword(): Promise<string> {
  for (const pw of PASSWORDS_TO_TRY) {
    const res = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login_id: 'admin', password: pw }),
    })
    if (res.ok) return pw
  }
  throw new Error('Cannot login with any known password. Reset DB or set ADMIN_PASSWORD env var.')
}

test('saegim demo walkthrough', async ({ page }) => {
  // ─── Scene 1: Login ───────────────────────────────────────
  await test.step('Login', async () => {
    const adminPassword = process.env.ADMIN_PASSWORD ?? await findWorkingPassword()

    await page.goto('/login')
    await pause(page, PAUSE_LONG)

    await page.getByPlaceholder('admin').fill('admin')
    await pause(page, PAUSE_SHORT)
    await page.locator('input[type="password"]').fill(adminPassword)
    await pause(page, PAUSE_SHORT)

    await page.getByRole('button', { name: /로그인/ }).click()
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10_000 })
    await pause(page, PAUSE_MEDIUM)

    // Handle must_change_password redirect
    if (page.url().includes('security') || page.url().includes('change-password')) {
      const pwInputs = page.locator('input[type="password"]')
      const count = await pwInputs.count()
      if (count >= 3) {
        await pwInputs.nth(0).fill(adminPassword)
        await pause(page, PAUSE_SHORT)
        await pwInputs.nth(1).fill(NEW_PASSWORD)
        await pause(page, PAUSE_SHORT)
        await pwInputs.nth(2).fill(NEW_PASSWORD)
        await pause(page, PAUSE_SHORT)
      } else if (count >= 2) {
        await pwInputs.nth(0).fill(NEW_PASSWORD)
        await pause(page, PAUSE_SHORT)
        await pwInputs.nth(1).fill(NEW_PASSWORD)
        await pause(page, PAUSE_SHORT)
      }
      const submitBtn = page.getByRole('button', { name: /변경|저장|확인/ })
      if (await submitBtn.isVisible()) {
        await submitBtn.click()
        await pause(page, PAUSE_MEDIUM)
      }
    }

    await expect(page.getByRole('heading', { name: '프로젝트' })).toBeVisible({ timeout: 15_000 })
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 2: Switch to Dark Mode ─────────────────────────
  await test.step('Dark mode', async () => {
    const themeBtn = page.getByRole('button', { name: /테마 전환/ })
    await themeBtn.click()
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 3: Create Project ──────────────────────────────
  await test.step('Create Project', async () => {
    await page.getByRole('button', { name: /새 프로젝트/ }).click()
    await pause(page, PAUSE_MEDIUM)

    await page.getByLabel(/이름|프로젝트 이름/).fill('Attention Is All You Need')
    await pause(page, PAUSE_SHORT)

    const descInput = page.getByLabel(/설명/)
    if (await descInput.isVisible()) {
      await descInput.fill('논문 PDF 레이블링 데모 프로젝트')
      await pause(page, PAUSE_SHORT)
    }

    await page.getByRole('button', { name: '생성', exact: true }).click()
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 4: OCR Settings — Add Gemini Engine ────────────
  await test.step('Navigate to project', async () => {
    const projectLink = page.getByRole('link', { name: /Attention Is All You Need/ })
    await projectLink.click()
    await pause(page, PAUSE_LONG)
  })

  await test.step('OCR Settings — Gemini', async () => {
    // Go to settings (gear icon link)
    const settingsBtn = page.getByRole('link', { name: '프로젝트 설정' })
    await settingsBtn.click()
    await pause(page, PAUSE_LONG)

    // Click "엔진 추가"
    await page.getByRole('button', { name: /엔진 추가/ }).click()
    await pause(page, PAUSE_MEDIUM)

    // Step 1: Select Gemini API type
    const geminiOption = page.getByText('Gemini API').first()
    await geminiOption.click()
    await pause(page, PAUSE_SHORT)

    // Click next/continue to step 2
    const nextBtn = page.getByRole('button', { name: /다음|계속/ })
    if (await nextBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await nextBtn.click()
      await pause(page, PAUSE_MEDIUM)
    }

    // Step 2: Fill engine config
    const nameInput = page.locator('#add-name')
    if (await nameInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await nameInput.fill('Gemini Flash')
      await pause(page, PAUSE_SHORT)
    }

    // API Key field — type="password" so it's already masked in recording
    const apiKeyInput = page.locator('#add-apikey')
    if (await apiKeyInput.isVisible({ timeout: 2_000 }).catch(() => false)) {
      // Check if pre-filled from env
      const currentVal = await apiKeyInput.inputValue()
      if (!currentVal) {
        await apiKeyInput.fill('••••••••••••••••••••')
      }
      await pause(page, PAUSE_MEDIUM)
    }

    // Select model
    const modelSelect = page.locator('#add-model')
    if (await modelSelect.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await pause(page, PAUSE_SHORT)
    }

    // Click "추가" to add the engine
    const addBtn = page.getByRole('button', { name: '추가', exact: true })
    if (await addBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await addBtn.click()
      await pause(page, PAUSE_LONG)
    }

    // Mask API key in the engine card with CSS overlay (for the recording)
    await page.evaluate(() => {
      document.querySelectorAll('input[type="password"]').forEach((el) => {
        (el as HTMLInputElement).style.filter = 'blur(4px)'
      })
    })
    await pause(page, PAUSE_SHORT)

    // Set as default engine (click star)
    const defaultBtn = page.getByRole('button', { name: /기본|default/i }).first()
    if (await defaultBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await defaultBtn.click()
      await pause(page, PAUSE_MEDIUM)
    }

    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 5: Upload PDF ──────────────────────────────────
  await test.step('Back to project & Upload PDF', async () => {
    // Navigate back to project page
    await page.goBack()
    await pause(page, PAUSE_MEDIUM)

    // Click upload button
    const uploadBtn = page.getByRole('button', { name: 'PDF 업로드' }).first()
    await expect(uploadBtn).toBeVisible({ timeout: 5_000 })

    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      uploadBtn.click(),
    ])
    await fileChooser.setFiles(SAMPLE_PDF)
    await pause(page, PAUSE_LONG)

    // Wait for document to appear
    await expect(page.getByText('1706.03762v7_7p_9p.pdf')).toBeVisible({ timeout: 30_000 })
    await pause(page, PAUSE_LONG)

    // Wait for processing to complete (3 pages — should be fast)
    await expect(page.getByText('준비됨')).toBeVisible({ timeout: 15_000 })
    await pause(page, PAUSE_LONG)

    // Expand document to show pages
    const docRow = page.getByText('1706.03762v7_7p_9p.pdf')
    await docRow.click()
    await pause(page, PAUSE_EXTRA)
  })

  // ─── Scene 6: Label Editor — Figure page ──────────────────
  await test.step('Open page with Figure', async () => {
    // Open page 3 (Figure 1: Transformer architecture) or first available
    const pageTiles = page.locator('[data-page-tile]')
    const tileCount = await pageTiles.count()

    if (tileCount >= 3) {
      // Page 3 has Figure 1 (Transformer architecture diagram)
      await pageTiles.nth(2).click()
    } else if (tileCount > 0) {
      await pageTiles.first().click()
    }
    await pause(page, PAUSE_EXTRA)

    await page.waitForSelector('canvas', { timeout: 15_000 })
    await pause(page, PAUSE_LONG)
  })

  await test.step('Accept Gemini OCR extraction — Figure', async () => {
    const acceptBtn = page.getByRole('button', { name: /수락/ })
    await expect(acceptBtn).toBeVisible({ timeout: 10_000 })
    await pause(page, PAUSE_MEDIUM)

    await acceptBtn.click()
    await pause(page, PAUSE_EXTRA)
  })

  await test.step('Inspect figure element', async () => {
    // Click on an element in the element list (left panel)
    // Look for figure category in the element list
    const figureEl = page.getByText(/그림|figure/i).first()
    if (await figureEl.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await figureEl.click()
      await pause(page, PAUSE_LONG)
    }

    // Show the right sidebar with category info
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 7: Navigate to Table page ──────────────────────
  await test.step('Navigate to page with Table', async () => {
    // Navigate forward to find a table page (Tables are around pages 5-7)
    // Press E multiple times to advance pages
    await page.keyboard.press('e')
    await pause(page, PAUSE_LONG)
    await page.keyboard.press('e')
    await pause(page, PAUSE_LONG)

    // Wait for canvas
    await page.waitForSelector('canvas', { timeout: 15_000 })
    await pause(page, PAUSE_MEDIUM)
  })

  await test.step('Accept Gemini OCR extraction — Table', async () => {
    const acceptBtn = page.getByRole('button', { name: /수락/ })
    if (await acceptBtn.isVisible({ timeout: 10_000 }).catch(() => false)) {
      await acceptBtn.click()
      await pause(page, PAUSE_EXTRA)
    }
  })

  await test.step('Inspect table element', async () => {
    // Click on a table element in the element list
    const tableEl = page.getByText(/테이블|table/i).first()
    if (await tableEl.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await tableEl.click()
      await pause(page, PAUSE_LONG)
    }

    // Show table attributes in the right sidebar
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 8: Draw bounding box ───────────────────────────
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

  // ─── Scene 9: Reading order ───────────────────────────────
  await test.step('Toggle reading order', async () => {
    await page.keyboard.press('r')
    await pause(page, PAUSE_LONG)

    await page.keyboard.press('r')
    await pause(page, PAUSE_MEDIUM)
  })

  // ─── Scene 10: Save ───────────────────────────────────────
  await test.step('Save annotations', async () => {
    await page.keyboard.press('Control+s')
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 11: Back to project overview ───────────────────
  await test.step('Back to project', async () => {
    const breadcrumb = page.getByText('Attention Is All You Need').first()
    if (await breadcrumb.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await breadcrumb.click()
    } else {
      await page.goBack()
    }
    await pause(page, PAUSE_LONG)
  })

  // ─── Scene 12: Progress dashboard ─────────────────────────
  await test.step('Progress dashboard', async () => {
    const progressBtn = page.getByRole('button', { name: /작업 현황/ }).or(
      page.getByRole('link', { name: /작업 현황/ })
    )
    if (await progressBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await progressBtn.click()
      await pause(page, PAUSE_EXTRA)
      await page.goBack()
      await pause(page, PAUSE_MEDIUM)
    }
  })

  // ─── Scene 13: Export ─────────────────────────────────────
  await test.step('Show export', async () => {
    const exportBtn = page.getByRole('button', { name: /전체 내보내기|내보내기|Export/ })
    if (await exportBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await exportBtn.hover()
      await pause(page, PAUSE_LONG)
    }
  })

  // ─── Final ────────────────────────────────────────────────
  await test.step('Final - home', async () => {
    await page.goto('/')
    await pause(page, PAUSE_EXTRA)
  })
})
