import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock pdfjs-dist before importing the store
vi.mock("pdfjs-dist", () => {
  const mockPage = {
    getViewport: vi.fn(() => ({ width: 1190, height: 1684 })),
    render: vi.fn(() => ({
      promise: Promise.resolve(),
      cancel: vi.fn(),
    })),
  };

  const mockDoc = {
    numPages: 5,
    getPage: vi.fn((pageNo: number) => {
      if (pageNo < 1 || pageNo > 5)
        return Promise.reject(new Error("Invalid page"));
      return Promise.resolve({ ...mockPage, pageNumber: pageNo });
    }),
    destroy: vi.fn(),
  };

  return {
    getDocument: vi.fn(() => ({
      promise: Promise.resolve(mockDoc),
    })),
    GlobalWorkerOptions: { workerSrc: "" },
  };
});

// Import after mock setup
const { pdfStore } = await import("$lib/stores/pdf.svelte");

describe("PdfStore", () => {
  beforeEach(() => {
    pdfStore.destroy();
  });

  describe("initial state", () => {
    it("starts with no document loaded", () => {
      expect(pdfStore.pdfDoc).toBeNull();
      expect(pdfStore.totalPages).toBe(0);
      expect(pdfStore.currentPageNo).toBe(1);
      expect(pdfStore.isLoading).toBe(false);
      expect(pdfStore.error).toBeNull();
    });
  });

  describe("loadDocument", () => {
    it("loads a PDF and sets totalPages", async () => {
      await pdfStore.loadDocument("/test.pdf");
      expect(pdfStore.pdfDoc).not.toBeNull();
      expect(pdfStore.totalPages).toBe(5);
      expect(pdfStore.currentPageNo).toBe(1);
      expect(pdfStore.isLoading).toBe(false);
      expect(pdfStore.error).toBeNull();
    });

    it("skips reload if same URL", async () => {
      await pdfStore.loadDocument("/test.pdf");
      const firstDoc = pdfStore.pdfDoc;
      await pdfStore.loadDocument("/test.pdf");
      expect(pdfStore.pdfDoc).toBe(firstDoc);
    });
  });

  describe("getPage", () => {
    it("returns a page proxy", async () => {
      await pdfStore.loadDocument("/test.pdf");
      const page = await pdfStore.getPage(1);
      expect(page).toBeDefined();
      expect(page.pageNumber).toBe(1);
    });

    it("throws when no document loaded", async () => {
      await expect(pdfStore.getPage(1)).rejects.toThrow(
        "PDF document not loaded",
      );
    });

    it("throws for out-of-range page", async () => {
      await pdfStore.loadDocument("/test.pdf");
      await expect(pdfStore.getPage(0)).rejects.toThrow("out of range");
      await expect(pdfStore.getPage(6)).rejects.toThrow("out of range");
    });

    it("caches pages", async () => {
      await pdfStore.loadDocument("/test.pdf");
      const page1 = await pdfStore.getPage(2);
      const page2 = await pdfStore.getPage(2);
      expect(page1).toBe(page2);
    });
  });

  describe("navigation", () => {
    it("setCurrentPage updates currentPageNo within bounds", async () => {
      await pdfStore.loadDocument("/test.pdf");
      pdfStore.setCurrentPage(3);
      expect(pdfStore.currentPageNo).toBe(3);
    });

    it("setCurrentPage ignores out-of-range values", async () => {
      await pdfStore.loadDocument("/test.pdf");
      pdfStore.setCurrentPage(0);
      expect(pdfStore.currentPageNo).toBe(1);
      pdfStore.setCurrentPage(10);
      expect(pdfStore.currentPageNo).toBe(1);
    });

    it("nextPage increments", async () => {
      await pdfStore.loadDocument("/test.pdf");
      pdfStore.nextPage();
      expect(pdfStore.currentPageNo).toBe(2);
    });

    it("nextPage does not exceed totalPages", async () => {
      await pdfStore.loadDocument("/test.pdf");
      pdfStore.setCurrentPage(5);
      pdfStore.nextPage();
      expect(pdfStore.currentPageNo).toBe(5);
    });

    it("prevPage decrements", async () => {
      await pdfStore.loadDocument("/test.pdf");
      pdfStore.setCurrentPage(3);
      pdfStore.prevPage();
      expect(pdfStore.currentPageNo).toBe(2);
    });

    it("prevPage does not go below 1", async () => {
      await pdfStore.loadDocument("/test.pdf");
      pdfStore.prevPage();
      expect(pdfStore.currentPageNo).toBe(1);
    });
  });

  describe("error handling", () => {
    it("logs a warning when loadDocument fails", async () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      const { getDocument } = await import("pdfjs-dist");
      const mockedGetDocument = vi.mocked(getDocument);
      mockedGetDocument.mockReturnValueOnce({
        promise: Promise.reject(new Error("Network error")),
      } as ReturnType<typeof getDocument>);

      await pdfStore.loadDocument("/fail.pdf");

      expect(pdfStore.error).toBe("Network error");
      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining("[saegim]"),
        expect.stringContaining("Network error"),
        expect.any(String),
        "/fail.pdf",
      );
      warnSpy.mockRestore();
    });
  });

  describe("destroy", () => {
    it("resets all state", async () => {
      await pdfStore.loadDocument("/test.pdf");
      pdfStore.setCurrentPage(3);
      pdfStore.destroy();

      expect(pdfStore.pdfDoc).toBeNull();
      expect(pdfStore.totalPages).toBe(0);
      expect(pdfStore.currentPageNo).toBe(1);
      expect(pdfStore.error).toBeNull();
    });
  });
});
