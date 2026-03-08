import { defineConfig } from '@playwright/test'

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:13000'
const AUTH_STATE = '.auth/state.json'

const commonBrowser = {
  browserName: 'chromium' as const,
  channel: 'chromium' as const,
}

export default defineConfig({
  testDir: '.',
  timeout: 180_000,
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
    // Auth setup — no video, runs first
    {
      name: 'setup',
      testMatch: 'auth-setup.ts',
      use: {
        ...commonBrowser,
        video: 'off',
      },
    },

    // Legacy: full walkthrough (all-in-one)
    {
      name: 'demo',
      testMatch: 'record-demo.ts',
      use: commonBrowser,
    },

    // Feature demos — each produces its own video
    {
      name: 'demo-project-setup',
      testMatch: 'demo-project-setup.spec.ts',
      dependencies: ['setup'],
      use: {
        ...commonBrowser,
        storageState: AUTH_STATE,
      },
    },
    {
      name: 'demo-labeling',
      testMatch: 'demo-labeling.spec.ts',
      dependencies: ['setup'],
      use: {
        ...commonBrowser,
        storageState: AUTH_STATE,
      },
    },
    {
      name: 'demo-overview',
      testMatch: 'demo-overview.spec.ts',
      dependencies: ['setup'],
      use: {
        ...commonBrowser,
        storageState: AUTH_STATE,
      },
    },
  ],
  reporter: 'list',
})
