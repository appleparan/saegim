import { defineConfig } from '@playwright/test'

const FRONTEND_URL = process.env.E2E_FRONTEND_URL ?? 'http://localhost:23000'
const BACKEND_URL = process.env.E2E_BACKEND_URL ?? 'http://localhost:25000'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: true,
  retries: 1,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 120_000,
  expect: {
    timeout: 15_000,
  },
  use: {
    baseURL: FRONTEND_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        viewport: { width: 1920, height: 1080 },
      },
      testIgnore: /gpu\//,
    },
    {
      name: 'gpu',
      use: {
        browserName: 'chromium',
        viewport: { width: 1920, height: 1080 },
      },
      testMatch: /gpu\/.*\.spec\.ts/,
      timeout: 600_000,
    },
  ],
  metadata: {
    backendUrl: BACKEND_URL,
    frontendUrl: FRONTEND_URL,
  },
})
