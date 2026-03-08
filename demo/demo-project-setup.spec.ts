/**
 * Demo: Project Setup
 *
 * Shows: Create project → OCR engine settings → Upload PDF
 * Starts already logged in (dark mode) via storageState.
 */

import { test, expect } from '@playwright/test'
import {
  pause,
  PAUSE_SHORT,
  PAUSE_MEDIUM,
  PAUSE_LONG,
  PAUSE_EXTRA,
  SAMPLE_PDF,
  DEMO_PROJECT_NAME,
  DEMO_PROJECT_DESC,
} from './helpers'

test('Project setup: create, OCR config, upload', async ({ page }) => {
  // ─── Create Project ──────────────────────────────────────────
  await test.step('Create project', async () => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: '프로젝트' })).toBeVisible({ timeout: 15_000 })
    await pause(page, PAUSE_LONG)

    await page.getByRole('button', { name: /새 프로젝트/ }).click()
    await pause(page, PAUSE_MEDIUM)

    await page.getByLabel(/이름|프로젝트 이름/).fill(DEMO_PROJECT_NAME)
    await pause(page, PAUSE_SHORT)

    const descInput = page.getByLabel(/설명/)
    if (await descInput.isVisible()) {
      await descInput.fill(DEMO_PROJECT_DESC)
      await pause(page, PAUSE_SHORT)
    }

    await page.getByRole('button', { name: '생성', exact: true }).click()
    await pause(page, PAUSE_LONG)
  })

  // ─── Navigate to Project ─────────────────────────────────────
  await test.step('Navigate to project', async () => {
    const projectLink = page.getByRole('link', { name: new RegExp(DEMO_PROJECT_NAME) })
    await projectLink.click()
    await pause(page, PAUSE_LONG)
  })

  // ─── OCR Settings — Add Gemini Engine ────────────────────────
  await test.step('OCR Settings — Gemini', async () => {
    const settingsBtn = page.getByRole('link', { name: '프로젝트 설정' })
    await settingsBtn.click()
    await pause(page, PAUSE_LONG)

    await page.getByRole('button', { name: /엔진 추가/ }).click()
    await pause(page, PAUSE_MEDIUM)

    // Select Gemini API type
    const geminiOption = page.getByText('Gemini API').first()
    await geminiOption.click()
    await pause(page, PAUSE_SHORT)

    // Next step
    const nextBtn = page.getByRole('button', { name: /다음|계속/ })
    if (await nextBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await nextBtn.click()
      await pause(page, PAUSE_MEDIUM)
    }

    // Fill engine config
    const nameInput = page.locator('#add-name')
    if (await nameInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await nameInput.fill('Gemini Flash')
      await pause(page, PAUSE_SHORT)
    }

    // API Key (masked in recording)
    const apiKeyInput = page.locator('#add-apikey')
    if (await apiKeyInput.isVisible({ timeout: 2_000 }).catch(() => false)) {
      const currentVal = await apiKeyInput.inputValue()
      if (!currentVal) {
        await apiKeyInput.fill('••••••••••••••••••••')
      }
      await pause(page, PAUSE_MEDIUM)
    }

    // Model select
    const modelSelect = page.locator('#add-model')
    if (await modelSelect.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await pause(page, PAUSE_SHORT)
    }

    // Add engine
    const addBtn = page.getByRole('button', { name: '추가', exact: true })
    if (await addBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await addBtn.click()
      await pause(page, PAUSE_LONG)
    }

    // Blur API keys for recording
    await page.evaluate(() => {
      document.querySelectorAll('input[type="password"]').forEach((el) => {
        ;(el as HTMLInputElement).style.filter = 'blur(4px)'
      })
    })
    await pause(page, PAUSE_SHORT)

    // Set as default
    const defaultBtn = page.getByRole('button', { name: /기본|default/i }).first()
    if (await defaultBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await defaultBtn.click()
      await pause(page, PAUSE_MEDIUM)
    }

    await pause(page, PAUSE_LONG)
  })

  // ─── Upload PDF ──────────────────────────────────────────────
  await test.step('Upload PDF', async () => {
    await page.goBack()
    await pause(page, PAUSE_MEDIUM)

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

    // Wait for ready status
    await expect(page.getByText('준비됨')).toBeVisible({ timeout: 15_000 })
    await pause(page, PAUSE_LONG)

    // Expand document to show pages
    const docRow = page.getByText('1706.03762v7_7p_9p.pdf')
    await docRow.click()
    await pause(page, PAUSE_EXTRA)
  })
})
