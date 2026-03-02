import { describe, test, expect, beforeAll } from "vitest";
import { waitForBackendReady, healthCheck, readinessCheck } from "../helpers/api";

describe("Health Checks", () => {
  beforeAll(async () => {
    await waitForBackendReady();
  });

  test("backend health endpoint returns 200", async () => {
    const { status } = await healthCheck();
    expect(status).toBe(200);
  });

  test("readiness endpoint returns 200 with ready status", async () => {
    const { data, status } = await readinessCheck();
    expect(status).toBe(200);
    expect(data.status).toBe("ready");
    expect(data.message).toBeTruthy();
    expect(data.version).toBeTruthy();
  });

  // Browser tests (frontend loads, empty state) are verified
  // manually via Chrome DevTools MCP in Claude Code.
});
