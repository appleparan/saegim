import { describe, test, expect, beforeAll, afterAll } from "vitest";
import {
  waitForBackendReady,
  createProject,
  uploadPdf,
  listDocuments,
  listPages,
  getPage,
  deleteProject,
} from "../helpers/api";
import { ensureTestPdf, getTestPdfPath } from "../helpers/pdf";

const PROJECT_NAME = `Attribute Classifier E2E ${Date.now()}`;

let projectId: string;
let documentId: string;
let pageId: string;

describe("Auto Attribute Classifier (pdfminer fallback)", () => {
  beforeAll(async () => {
    await waitForBackendReady();
    await ensureTestPdf();

    const { data: project } = await createProject(PROJECT_NAME, "E2E attribute classifier test");
    projectId = project.id;

    const { data: doc } = await uploadPdf(projectId, getTestPdfPath());
    documentId = doc.id;

    // Wait for processing to complete
    const deadline = Date.now() + 120_000;
    while (Date.now() < deadline) {
      const { data: docs } = await listDocuments(projectId);
      if (docs.length > 0 && docs[0].status === "ready") {
        documentId = docs[0].id;
        break;
      }
      await new Promise((r) => setTimeout(r, 2_000));
    }

    const { data: pages } = await listPages(documentId);
    expect(pages.length).toBeGreaterThan(0);
    pageId = pages[0].id;
  });

  test("01 - page_attribute is populated in auto_extracted_data", async () => {
    const { data: page } = await getPage(pageId);

    expect(page.auto_extracted_data).toBeTruthy();
    const autoData = page.auto_extracted_data as Record<string, unknown>;

    // page_attribute should exist and not be empty
    const pageAttr = autoData.page_attribute as Record<string, unknown>;
    expect(pageAttr).toBeTruthy();

    // language should be detected (sample PDF is English academic paper)
    expect(pageAttr.language).toBeTruthy();
    expect(typeof pageAttr.language).toBe("string");
    expect((pageAttr.language as string).length).toBeGreaterThan(0);

    // layout should be detected
    expect(pageAttr.layout).toBeTruthy();
    expect(typeof pageAttr.layout).toBe("string");

    // Boolean fields should be set
    expect(typeof pageAttr.watermark).toBe("boolean");
    expect(typeof pageAttr.fuzzy_scan).toBe("boolean");
    expect(typeof pageAttr.colorful_background).toBe("boolean");
  });

  test("02 - English academic paper detected as language=en", async () => {
    const { data: page } = await getPage(pageId);
    const autoData = page.auto_extracted_data as Record<string, unknown>;
    const pageAttr = autoData.page_attribute as Record<string, unknown>;

    // "Attention Is All You Need" is English
    expect(pageAttr.language).toBe("en");
  });

  test("03 - academic paper detected as data_source=academic_literature", async () => {
    const { data: page } = await getPage(pageId);
    const autoData = page.auto_extracted_data as Record<string, unknown>;
    const pageAttr = autoData.page_attribute as Record<string, unknown>;

    // Paper contains "Abstract", "Introduction", "References" keywords
    expect(pageAttr.data_source).toBe("academic_literature");
  });

  test("04 - text blocks have element-level attributes", async () => {
    const { data: page } = await getPage(pageId);
    const autoData = page.auto_extracted_data as Record<string, unknown>;
    const layoutDets = autoData.layout_dets as Array<Record<string, unknown>>;

    const textBlocks = layoutDets.filter((el) => el.category_type === "text_block");
    expect(textBlocks.length).toBeGreaterThan(0);

    // Each text block should have an attribute dict
    for (const block of textBlocks) {
      const attr = block.attribute as Record<string, unknown>;
      expect(attr).toBeTruthy();

      // text_language should be set (English paper)
      if (attr.text_language) {
        expect(["text_en", "text_ko", "text_ko_en_mixed"]).toContain(attr.text_language);
      }

      // text_background and text_rotate should have defaults
      expect(attr.text_background).toBe("white");
      expect(attr.text_rotate).toBe("normal");
    }
  });

  test("05 - layout is classified as valid layout type", async () => {
    const { data: page } = await getPage(pageId);
    const autoData = page.auto_extracted_data as Record<string, unknown>;
    const pageAttr = autoData.page_attribute as Record<string, unknown>;

    const validLayouts = [
      "single_column",
      "double_column",
      "three_column",
      "1andmore_column",
      "other_layout",
    ];
    expect(validLayouts).toContain(pageAttr.layout);
  });

  test("06 - all elements with attributes have valid attribute keys", async () => {
    const { data: page } = await getPage(pageId);
    const autoData = page.auto_extracted_data as Record<string, unknown>;
    const layoutDets = autoData.layout_dets as Array<Record<string, unknown>>;

    for (const el of layoutDets) {
      const attr = el.attribute as Record<string, unknown> | undefined;
      if (!attr || Object.keys(attr).length === 0) continue;

      const category = el.category_type as string;

      if (category === "text_block" || category === "title") {
        // Should have text-specific attributes
        expect(attr).toHaveProperty("text_background");
        expect(attr).toHaveProperty("text_rotate");
      }

      if (category === "table") {
        expect(attr).toHaveProperty("table_layout");
        expect(attr).toHaveProperty("with_span");
      }

      if (category === "equation_isolated") {
        expect(attr).toHaveProperty("formula_type");
        expect(attr).toHaveProperty("equation_language");
      }
    }
  });

  afterAll(async () => {
    try {
      await deleteProject(projectId);
    } catch {
      // Ignore cleanup errors
    }
  });
});
