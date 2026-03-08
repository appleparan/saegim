/**
 * Authentication setup — runs before demo specs (no video).
 *
 * Logs in via UI, handles password change, enables dark mode,
 * and saves browser state to .auth/state.json for reuse.
 */

import { test as setup, expect } from '@playwright/test'
import { AUTH_STATE_PATH, PASSWORDS_TO_TRY, NEW_PASSWORD } from './helpers'

async function findWorkingPassword(apiUrl: string): Promise<string> {
  for (const pw of PASSWORDS_TO_TRY) {
    const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login_id: 'admin', password: pw }),
    })
    if (res.ok) return pw
  }
  throw new Error('Cannot login with any known password.')
}

setup('authenticate and save state', async ({ page }) => {
  const apiUrl = process.env.API_URL ?? 'http://localhost:15000'
  const adminPassword = process.env.ADMIN_PASSWORD ?? (await findWorkingPassword(apiUrl))

  // Login via UI
  await page.goto('/login')
  await page.getByPlaceholder('admin').fill('admin')
  await page.locator('input[type="password"]').fill(adminPassword)
  await page.getByRole('button', { name: /로그인/ }).click()
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10_000 })

  // Handle must_change_password redirect
  if (page.url().includes('security') || page.url().includes('change-password')) {
    const pwInputs = page.locator('input[type="password"]')
    const count = await pwInputs.count()
    if (count >= 3) {
      await pwInputs.nth(0).fill(adminPassword)
      await pwInputs.nth(1).fill(NEW_PASSWORD)
      await pwInputs.nth(2).fill(NEW_PASSWORD)
    } else if (count >= 2) {
      await pwInputs.nth(0).fill(NEW_PASSWORD)
      await pwInputs.nth(1).fill(NEW_PASSWORD)
    }
    const submitBtn = page.getByRole('button', { name: /변경|저장|확인/ })
    if (await submitBtn.isVisible()) {
      await submitBtn.click()
      await page.waitForTimeout(1_000)
    }
  }

  await expect(page.getByRole('heading', { name: '프로젝트' })).toBeVisible({ timeout: 15_000 })

  // Enable dark mode
  const themeBtn = page.getByRole('button', { name: /테마 전환/ })
  await themeBtn.click()
  await page.waitForTimeout(500)

  // Save authenticated state (cookies + localStorage)
  await page.context().storageState({ path: AUTH_STATE_PATH })
})
