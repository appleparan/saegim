import { describe, test, expect, beforeAll, afterAll } from "vitest";
import {
  waitForBackendReady,
  createProject,
  getOcrConfig,
  updateOcrConfig,
  testOcrConnection,
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

  afterAll(async () => {
    try {
      await deleteProject(projectId);
    } catch {
      // Ignore cleanup errors
    }
  });
});
