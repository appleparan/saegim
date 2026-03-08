/**
 * Demo: Project Overview
 *
 * Shows: Project page → progress dashboard → export
 *
 * Data setup via API (invisible in video):
 *   - Ensures project and document exist
 */

import { test, expect } from '@playwright/test'
import {
  pause,
  apiLogin,
  apiEnsureFullSetup,
  PAUSE_MEDIUM,
  PAUSE_LONG,
  PAUSE_EXTRA,
} from './helpers'

const PROJECT_NAME = 'Demo: Overview'

test.beforeAll(async () => {
  const { token } = await apiLogin()
  await apiEnsureFullSetup(token, PROJECT_NAME)
})

test('Project overview: dashboard and export', async ({ page }) => {
  // ─── Navigate to project ─────────────────────────────────────
  await test.step('Navigate to project', async () => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: '프로젝트' })).toBeVisible({ timeout: 15_000 })
    await pause(page, PAUSE_LONG)

    const projectLink = page.getByRole('link', { name: PROJECT_NAME })
    await projectLink.click()
    await pause(page, PAUSE_LONG)
  })

  // ─── Progress dashboard ──────────────────────────────────────
  await test.step('Progress dashboard', async () => {
    const progressBtn = page.getByRole('button', { name: /작업 현황/ }).or(
      page.getByRole('link', { name: /작업 현황/ }),
    )
    if (await progressBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await progressBtn.click()
      await pause(page, PAUSE_EXTRA)
      await page.goBack()
      await pause(page, PAUSE_MEDIUM)
    }
  })

  // ─── Export ──────────────────────────────────────────────────
  await test.step('Show export', async () => {
    const exportBtn = page.getByRole('button', { name: /전체 내보내기|내보내기|Export/ })
    if (await exportBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await exportBtn.hover()
      await pause(page, PAUSE_LONG)
    }
  })

  // ─── Final ───────────────────────────────────────────────────
  await test.step('Final — home', async () => {
    await page.goto('/')
    await pause(page, PAUSE_EXTRA)
  })
})
