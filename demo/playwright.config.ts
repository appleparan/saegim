import { defineConfig } from '@playwright/test'

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:13000'
const API_URL = process.env.API_URL ?? 'http://localhost:15000'

export default defineConfig({
  testDir: '.',
  testMatch: 'record-demo.ts',
  timeout: 120_000,
  use: {
    baseURL: BASE_URL,
    viewport: { width: 1920, height: 1080 },
    video: {
      mode: 'on',
      size: { width: 1920, height: 1080 },
    },
    launchOptions: {
      slowMo: 400,
    },
    actionTimeout: 15_000,
  },
  projects: [
    {
      name: 'demo',
      use: {
        browserName: 'chromium',
        channel: 'chromium',
      },
    },
  ],
  reporter: 'list',
})
