import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    dir: "./tests/gpu",
    include: ["**/*.test.ts"],
    testTimeout: 600_000,
    hookTimeout: 300_000,
    teardownTimeout: 30_000,
    maxWorkers: 1,
    sequence: {
      concurrent: false,
    },
    reporters: ["default"],
  },
});
