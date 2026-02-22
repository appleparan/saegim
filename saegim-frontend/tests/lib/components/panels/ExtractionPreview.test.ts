import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/svelte";
import ExtractionPreview from "$lib/components/panels/ExtractionPreview.svelte";
import { annotationStore } from "$lib/stores/annotation.svelte";
import type { AnnotationData } from "$lib/types/omnidocbench";

// Mock the pages API
vi.mock("$lib/api/pages", () => ({
  acceptExtraction: vi.fn(() =>
    Promise.resolve({
      annotation_data: { layout_dets: [], page_info: {}, page_attribute: {} },
    }),
  ),
}));

// Mock the UI store
vi.mock("$lib/stores/ui.svelte", () => ({
  uiStore: {
    showNotification: vi.fn(),
  },
}));

function makeAutoData(count: number): AnnotationData {
  return {
    layout_dets: Array.from({ length: count }, (_, i) => ({
      category_type: i % 2 === 0 ? "text_block" : "figure",
      poly: [0, 0, 100, 0, 100, 100, 0, 100],
      anno_id: i + 1,
      text: `element ${i + 1}`,
    })),
    page_info: {},
    page_attribute: {},
  } as unknown as AnnotationData;
}

describe("ExtractionPreview", () => {
  beforeEach(() => {
    annotationStore.clear();
  });

  afterEach(() => {
    cleanup();
  });

  it("shows extracting spinner when documentStatus is 'extracting'", () => {
    render(ExtractionPreview, {
      props: {
        pageId: "page-1",
        autoExtractedData: null,
        documentStatus: "extracting",
        onAccepted: vi.fn(),
      },
    });

    expect(screen.getByText("OCR 추출 진행 중...")).toBeTruthy();
  });

  it("shows auto-extracted data summary when data is available", () => {
    const autoData = makeAutoData(4);
    render(ExtractionPreview, {
      props: {
        pageId: "page-1",
        autoExtractedData: autoData,
        documentStatus: "ready",
        onAccepted: vi.fn(),
      },
    });

    expect(screen.getByText("자동 추출 결과가 있습니다")).toBeTruthy();
    // 4 total elements: 2 text, 2 figure
    expect(screen.getByText(/총 4개 요소/)).toBeTruthy();
  });

  it("shows accept and dismiss buttons when data is available", () => {
    const autoData = makeAutoData(2);
    render(ExtractionPreview, {
      props: {
        pageId: "page-1",
        autoExtractedData: autoData,
        documentStatus: "ready",
        onAccepted: vi.fn(),
      },
    });

    expect(screen.getByText("수락")).toBeTruthy();
    expect(screen.getByText("무시")).toBeTruthy();
  });

  it("hides after dismiss is clicked", async () => {
    const autoData = makeAutoData(2);
    render(ExtractionPreview, {
      props: {
        pageId: "page-1",
        autoExtractedData: autoData,
        documentStatus: "ready",
        onAccepted: vi.fn(),
      },
    });

    expect(screen.getByText("수락")).toBeTruthy();

    const dismissBtn = screen.getByText("무시");
    await fireEvent.click(dismissBtn);

    expect(screen.queryByText("수락")).toBeNull();
  });

  it("shows no-data hint when auto_extracted_data is null and documentStatus is ready", () => {
    render(ExtractionPreview, {
      props: {
        pageId: "page-1",
        autoExtractedData: null,
        documentStatus: "ready",
        onAccepted: vi.fn(),
      },
    });

    expect(screen.getByText("자동 추출 결과가 없습니다.")).toBeTruthy();
    expect(screen.getByText(/OCR 설정/)).toBeTruthy();
  });

  it("does not show no-data hint when documentStatus is undefined (still loading)", () => {
    render(ExtractionPreview, {
      props: {
        pageId: "page-1",
        autoExtractedData: null,
        onAccepted: vi.fn(),
      },
    });

    expect(screen.queryByText("자동 추출 결과가 없습니다.")).toBeNull();
  });

  it("does not show data summary when annotations already exist", () => {
    annotationStore.load("page-1", makeAutoData(3));
    const autoData = makeAutoData(2);

    render(ExtractionPreview, {
      props: {
        pageId: "page-1",
        autoExtractedData: autoData,
        documentStatus: "ready",
        onAccepted: vi.fn(),
      },
    });

    // Since annotationStore has elements, ExtractionPreview should not show
    expect(screen.queryByText("자동 추출 결과가 있습니다")).toBeNull();
  });

  it("does not show no-data hint when annotations already exist", () => {
    annotationStore.load("page-1", makeAutoData(3));

    render(ExtractionPreview, {
      props: {
        pageId: "page-1",
        autoExtractedData: null,
        documentStatus: "ready",
        onAccepted: vi.fn(),
      },
    });

    expect(screen.queryByText("자동 추출 결과가 없습니다.")).toBeNull();
  });
});
