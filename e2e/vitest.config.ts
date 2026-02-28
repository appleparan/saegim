import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    dir: './tests',
    include: ['**/*.test.ts'],
    exclude: ['gpu/**'],
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
