import { describe, test, expect, beforeAll } from "vitest";
import { waitForBackendReady, healthCheck } from "../helpers/api";

describe("Health Checks", () => {
  beforeAll(async () => {
    await waitForBackendReady();
  });

  test("backend health endpoint returns 200", async () => {
    const { status } = await healthCheck();
    expect(status).toBe(200);
  });

  // Browser tests (frontend loads, empty state) are verified
  // manually via Chrome DevTools MCP in Claude Code.
});
