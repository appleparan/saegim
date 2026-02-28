import { describe, test, expect, beforeAll, afterAll } from "vitest";
import {
  waitForBackendReady,
  waitForVllmReady,
  createProject,
  updateOcrConfig,
  uploadPdf,
  listDocuments,
  listPages,
  getPage,
  acceptExtraction,
  deleteProject,
} from "../../helpers/api";
import { ensureTestPdf, getTestPdfPath } from "../../helpers/pdf";

const VLLM_HOST = "vllm";
const VLLM_PORT = 8000;
const VLLM_MODEL = "richarddavison/chandra-fp8";

const PROJECT_NAME = `GPU Hybrid Labeling E2E ${Date.now()}`;

let projectId: string;
let documentId: string;
let pageId: string;

describe("GPU Hybrid Labeling — API Verification", () => {
  beforeAll(async () => {
    await waitForBackendReady();
    await waitForVllmReady();
    await ensureTestPdf();

    // Create project and configure vLLM OCR
    const { data: project } = await createProject(PROJECT_NAME, "GPU hybrid labeling E2E test");
    projectId = project.id;

    await updateOcrConfig(projectId, {
      engine_type: "integrated_server",
      integrated_server: {
        host: VLLM_HOST,
        port: VLLM_PORT,
        model: VLLM_MODEL,
      },
    });

    // Upload PDF and wait for extraction (up to 5 min)
    const { data: doc } = await uploadPdf(projectId, getTestPdfPath());
    documentId = doc.id;

    const deadline = Date.now() + 300_000;
    let lastStatus = "unknown";
    while (Date.now() < deadline) {
      const { data: docs } = await listDocuments(projectId);
      if (docs.length > 0) {
        lastStatus = docs[0].status;
        if (lastStatus === "ready") {
          documentId = docs[0].id;
          break;
        }
        if (lastStatus === "extraction_failed") {
          throw new Error("OCR extraction failed");
        }
      }
      await new Promise((r) => setTimeout(r, 5_000));
    }
    expect(lastStatus).toBe("ready");

    // Get page IDs
    const { data: pages } = await listPages(documentId);
    expect(pages.length).toBeGreaterThan(0);
    pageId = pages[0].id;

    // Accept extraction so annotation_data is populated
    await acceptExtraction(pageId);
  });

  test("01 - extraction produces annotation elements", async () => {
    const { data: pageData } = await getPage(pageId);
    const annotation = pageData.annotation_data as Record<string, unknown>;
    const layoutDets = (annotation.layout_dets ?? []) as Array<Record<string, unknown>>;
    expect(layoutDets.length).toBeGreaterThan(0);
  });

  test("02 - extracted bbox poly coordinates are valid", async () => {
    const { data: pageData } = await getPage(pageId);
    const annotation = pageData.annotation_data as Record<string, unknown>;
    const layoutDets = (annotation.layout_dets ?? []) as Array<Record<string, unknown>>;

    for (const el of layoutDets) {
      const poly = el.poly as number[];
      expect(poly).toHaveLength(8);

      // All coordinates should be non-negative
      for (const coord of poly) {
        expect(coord).toBeGreaterThanOrEqual(0);
      }

      // Bounding box should have non-zero area (x2 > x1, y2 > y1)
      const [x1, y1, x2, , , , , y4] = poly;
      expect(x2).toBeGreaterThan(x1);
      expect(y4).toBeGreaterThan(y1);
    }
  });

  // Browser tests (3-layer structure, tool buttons, zoom, keyboard shortcuts,
  // text overlay selectability, element list, bbox alignment) are verified
  // manually via Chrome DevTools MCP in Claude Code.

  afterAll(async () => {
    try {
      await deleteProject(projectId);
    } catch {
      // Ignore cleanup errors
    }
  });
});
