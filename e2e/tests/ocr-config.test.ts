import { describe, test, expect, beforeAll, afterAll } from "vitest";
import {
  waitForBackendReady,
  createProject,
  getOcrConfig,
  updateOcrConfig,
  testOcrConnection,
  getAvailableEngines,
  deleteProject,
} from "../helpers/api";

let projectId: string;

describe("OCR Config API (engine_type based)", () => {
  beforeAll(async () => {
    await waitForBackendReady();
    const { data } = await createProject(`OCR Config E2E ${Date.now()}`, "OCR config test");
    projectId = data.id;
  });

  test("01 - default OCR config is pdfminer", async () => {
    const { data, status } = await getOcrConfig(projectId);
    expect(status).toBe(200);
    expect(data.engine_type).toBe("pdfminer");
  });

  test("02 - update to commercial_api with gemini", async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: "commercial_api",
      commercial_api: {
        provider: "gemini",
        api_key: "test-key",
        model: "gemini-3-flash-preview",
      },
    });
    expect(status).toBe(200);
    expect(data.engine_type).toBe("commercial_api");
    expect(data.commercial_api).toEqual({
      provider: "gemini",
      api_key: "test-key",
      model: "gemini-3-flash-preview",
    });
  });

  test("03 - update to vllm with model", async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: "vllm",
      vllm: { host: "localhost", port: 8000, model: "datalab-to/chandra" },
    });
    expect(status).toBe(200);
    expect(data.engine_type).toBe("vllm");
    expect(data.vllm).toEqual({
      host: "localhost",
      port: 8000,
      model: "datalab-to/chandra",
    });
  });

  test("04 - update to split_pipeline with gemini OCR", async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: "split_pipeline",
      split_pipeline: {
        docling_model_name: "ibm-granite/granite-docling-258M",
        ocr_provider: "gemini",
        ocr_api_key: "test-key",
        ocr_model: "gemini-3-flash-preview",
      },
    });
    expect(status).toBe(200);
    expect(data.engine_type).toBe("split_pipeline");
    expect(data.split_pipeline?.ocr_provider).toBe("gemini");
    expect(data.split_pipeline?.ocr_api_key).toBe("test-key");
    expect(data.split_pipeline?.ocr_model).toBe("gemini-3-flash-preview");
  });

  test("05 - revert to pdfminer", async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: "pdfminer",
    });
    expect(status).toBe(200);
    expect(data.engine_type).toBe("pdfminer");
  });

  test("06 - get config reflects last update", async () => {
    const { data } = await getOcrConfig(projectId);
    expect(data.engine_type).toBe("pdfminer");
  });

  test("07 - validation: commercial_api without sub-config is 422", async () => {
    const { status } = await updateOcrConfig(projectId, {
      engine_type: "commercial_api",
    });
    expect(status).toBe(422);
  });

  test("08 - validation: vllm without sub-config is 422", async () => {
    const { status } = await updateOcrConfig(projectId, {
      engine_type: "vllm",
    });
    expect(status).toBe(422);
  });

  test("09 - validation: split_pipeline without sub-config is 422", async () => {
    const { status } = await updateOcrConfig(projectId, {
      engine_type: "split_pipeline",
    });
    expect(status).toBe(422);
  });

  test("10 - connection test for pdfminer always succeeds", async () => {
    const { data, status } = await testOcrConnection(projectId, {
      engine_type: "pdfminer",
    });
    expect(status).toBe(200);
    expect(data.success).toBe(true);
  });

  test("11 - connection test for unreachable vllm fails", async () => {
    const { data, status } = await testOcrConnection(projectId, {
      engine_type: "vllm",
      vllm: { host: "nonexistent-host", port: 18811 },
    });
    expect(status).toBe(200);
    expect(data.success).toBe(false);
    expect(data.message).toBeTruthy();
  });

  test("12 - update with enabled_engines saves multiple engines", async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: "commercial_api",
      commercial_api: {
        provider: "gemini",
        api_key: "test-key",
        model: "gemini-3-flash-preview",
      },
      vllm: { host: "localhost", port: 8000, model: "datalab-to/chandra" },
      enabled_engines: ["commercial_api", "vllm"],
    });
    expect(status).toBe(200);
    expect(data.engine_type).toBe("commercial_api");
    expect((data as Record<string, unknown>).enabled_engines).toEqual(
      expect.arrayContaining(["commercial_api", "vllm"]),
    );
  });

  test("13 - available-engines returns configured engines excluding pdfminer", async () => {
    const { data, status } = await getAvailableEngines(projectId);
    expect(status).toBe(200);
    const engineTypes = data.engines.map((e) => e.engine_type);
    expect(engineTypes).toContain("commercial_api");
    expect(engineTypes).toContain("vllm");
    expect(engineTypes).not.toContain("pdfminer");
  });

  test("14 - available-engines returns correct labels", async () => {
    const { data } = await getAvailableEngines(projectId);
    const labelsMap = Object.fromEntries(
      data.engines.map((e) => [e.engine_type, e.label]),
    );
    expect(labelsMap["commercial_api"]).toBe("Gemini API");
    expect(labelsMap["vllm"]).toBe("vLLM");
  });

  test("15 - enabled_engines with missing sub-config is rejected (422)", async () => {
    const { status } = await updateOcrConfig(projectId, {
      engine_type: "commercial_api",
      commercial_api: {
        provider: "gemini",
        api_key: "test-key",
        model: "gemini-3-flash-preview",
      },
      enabled_engines: ["commercial_api", "vllm"],
      // Note: no vllm sub-config → validation rejects
    });
    expect(status).toBe(422);
  });

  test("16 - enabled_engines validation: missing sub-config is 422", async () => {
    const { status } = await updateOcrConfig(projectId, {
      engine_type: "pdfminer",
      enabled_engines: ["pdfminer", "vllm"],
    });
    expect(status).toBe(422);
  });

  test("17 - available-engines empty for pdfminer-only project", async () => {
    await updateOcrConfig(projectId, {
      engine_type: "pdfminer",
    });
    const { data, status } = await getAvailableEngines(projectId);
    expect(status).toBe(200);
    expect(data.engines).toHaveLength(0);
  });

  test("18 - available-engines fallback to default engine when no enabled_engines", async () => {
    await updateOcrConfig(projectId, {
      engine_type: "commercial_api",
      commercial_api: {
        provider: "gemini",
        api_key: "test-key",
        model: "gemini-3-flash-preview",
      },
    });
    const { data, status } = await getAvailableEngines(projectId);
    expect(status).toBe(200);
    expect(data.engines).toHaveLength(1);
    expect(data.engines[0].engine_type).toBe("commercial_api");
    expect(data.engines[0].label).toBe("Gemini API");
  });

  afterAll(async () => {
    try {
      await deleteProject(projectId);
    } catch {
      // Ignore cleanup errors
    }
  });
});
