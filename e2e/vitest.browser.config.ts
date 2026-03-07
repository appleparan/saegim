import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    dir: './tests/browser',
    include: ['**/*.test.ts'],
    testTimeout: 120_000,
    hookTimeout: 120_000,
    teardownTimeout: 30_000,
    maxWorkers: 1,
    sequence: {
      concurrent: false,
    },
    reporters: ['default'],
  },
})
