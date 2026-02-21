import { test, expect } from '@playwright/test'
import { waitForBackendReady, healthCheck } from '../helpers/api'

test.describe('Health Checks', () => {
  test.beforeAll(async () => {
    await waitForBackendReady()
  })

  test('backend health endpoint returns 200', async () => {
    const { status } = await healthCheck()
    expect(status).toBe(200)
  })

  test('frontend loads project list page', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: '프로젝트' })).toBeVisible()
  })

  test('frontend shows empty state initially or project list', async ({ page }) => {
    await page.goto('/')
    // Either shows empty state or existing projects
    const heading = page.locator('h1, h2').first()
    await expect(heading).toBeVisible()
  })
})
