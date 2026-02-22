import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/svelte";
import { canvasStore } from "$lib/stores/canvas.svelte";
import { annotationStore } from "$lib/stores/annotation.svelte";

// Mock ResizeObserver (not available in jsdom)
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
vi.stubGlobal("ResizeObserver", MockResizeObserver);

// Mock HTMLCanvasElement.getContext (not available in jsdom without canvas package)
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  clearRect: vi.fn(),
  drawImage: vi.fn(),
  fillRect: vi.fn(),
  scale: vi.fn(),
  translate: vi.fn(),
  transform: vi.fn(),
  setTransform: vi.fn(),
  save: vi.fn(),
  restore: vi.fn(),
})) as unknown as typeof HTMLCanvasElement.prototype.getContext;

// Mock Konva — HybridViewer creates a Konva.Stage on mount
vi.mock("konva", () => {
  class MockStage {
    add = vi.fn();
    width = vi.fn();
    height = vi.fn();
    destroy = vi.fn();
    getLayers = vi.fn(() => []);
    on = vi.fn();
    getPointerPosition = vi.fn();
  }

  class MockLayer {
    add = vi.fn();
    batchDraw = vi.fn();
    position = vi.fn();
    scale = vi.fn();
    destroy = vi.fn();
  }

  class MockTransformer {
    nodes = vi.fn();
    moveToTop = vi.fn();
  }

  class MockRect {
    on = vi.fn();
    setAttrs = vi.fn();
    setAttr = vi.fn();
    getAttr = vi.fn();
    x = vi.fn(() => 0);
    y = vi.fn(() => 0);
    width = vi.fn(() => 100);
    height = vi.fn(() => 100);
    scaleX = vi.fn(() => 1);
    scaleY = vi.fn(() => 1);
    position = vi.fn();
    destroy = vi.fn();
  }

  return {
    default: {
      Stage: MockStage,
      Layer: MockLayer,
      Transformer: MockTransformer,
      Rect: MockRect,
    },
  };
});

// Mock pdfjs-dist for PdfRenderer child component
vi.mock("pdfjs-dist", () => ({
  getDocument: vi.fn(),
  GlobalWorkerOptions: { workerSrc: "" },
  TextLayer: class {
    render() {
      return Promise.resolve();
    }
    cancel() {}
    get textDivs() {
      return [];
    }
    get textContentItemsStr() {
      return [];
    }
  },
}));

const HybridViewer = (
  await import("$lib/components/canvas/HybridViewer.svelte")
).default;

function makeMockPageProxy() {
  return {
    pageNumber: 1,
    getViewport: vi.fn(() => ({ width: 1190, height: 1684 })),
    render: vi.fn(() => ({
      promise: Promise.resolve(),
      cancel: vi.fn(),
    })),
    getTextContent: vi.fn(() =>
      Promise.resolve({ items: [], styles: {} }),
    ),
  } as unknown as import("pdfjs-dist").PDFPageProxy;
}

describe("HybridViewer", () => {
  beforeEach(() => {
    canvasStore.setImageDimensions(1190, 1684);
    canvasStore.setScale(1);
    canvasStore.setOffset(0, 0);
    annotationStore.clear();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders fallback <img> when only imageUrl is provided", () => {
    const { container } = render(HybridViewer, {
      props: {
        imageUrl: "/test-image.png",
        width: 1190,
        height: 1684,
      },
    });

    const img = container.querySelector("img");
    expect(img).toBeTruthy();
    expect(img?.getAttribute("src")).toBe("/test-image.png");

    // No PdfRenderer canvas should be present
    const canvas = container.querySelector("canvas");
    expect(canvas).toBeNull();
  });

  it("renders PdfRenderer <canvas> when pageProxy is provided", () => {
    const pageProxy = makeMockPageProxy();
    const { container } = render(HybridViewer, {
      props: {
        pageProxy,
        imageUrl: "/test-image.png",
        width: 1190,
        height: 1684,
      },
    });

    // PdfRenderer renders a <canvas>
    const canvas = container.querySelector("canvas");
    expect(canvas).toBeTruthy();

    // Fallback <img> should NOT be present when pageProxy is given
    const img = container.querySelector("img");
    expect(img).toBeNull();
  });

  it("renders nothing for background when neither prop is provided", () => {
    const { container } = render(HybridViewer, {
      props: {
        width: 1190,
        height: 1684,
      },
    });

    const img = container.querySelector("img");
    const canvas = container.querySelector("canvas");
    expect(img).toBeNull();
    expect(canvas).toBeNull();
  });

  it("prefers pageProxy over imageUrl when both are provided", () => {
    const pageProxy = makeMockPageProxy();
    const { container } = render(HybridViewer, {
      props: {
        pageProxy,
        imageUrl: "/fallback.png",
        width: 1190,
        height: 1684,
      },
    });

    // Canvas (from PdfRenderer) should be present
    expect(container.querySelector("canvas")).toBeTruthy();
    // Img should NOT be present
    expect(container.querySelector("img")).toBeNull();
  });

  it("applies correct CSS transform to fallback image", async () => {
    const { container } = render(HybridViewer, {
      props: {
        imageUrl: "/test-image.png",
        width: 800,
        height: 1100,
      },
    });

    // Set viewport after render (initStage calls fitToContainer which resets)
    canvasStore.setViewport(1.5, 100, 200);

    // Wait for Svelte reactivity to propagate
    await new Promise((r) => setTimeout(r, 0));

    const img = container.querySelector("img");
    expect(img).toBeTruthy();
    const style = img!.style;
    expect(style.transform).toContain("translate(100px, 200px)");
    expect(style.transform).toContain("scale(1.5)");
    expect(style.width).toBe("800px");
    expect(style.height).toBe("1100px");
  });

  it("creates Konva container div with z-index 10", () => {
    const { container } = render(HybridViewer, {
      props: {
        imageUrl: "/test.png",
        width: 800,
        height: 1100,
      },
    });

    const konvaDiv = container.querySelector('[style*="z-index: 10"]');
    expect(konvaDiv).toBeTruthy();
  });

  it("hides OCR TextOverlay when pageProxy is provided (PDF.js TextLayer handles text)", () => {
    const pageProxy = makeMockPageProxy();
    const { container } = render(HybridViewer, {
      props: {
        pageProxy,
        imageUrl: "/fallback.png",
        width: 1190,
        height: 1684,
      },
    });

    // TextOverlay uses z-index: 20 — should NOT be present when PDF.js is active
    const textOverlay = container.querySelector('[style*="z-index: 20"]');
    expect(textOverlay).toBeNull();
  });

  it("shows OCR TextOverlay when only imageUrl is provided (no PDF.js)", () => {
    const { container } = render(HybridViewer, {
      props: {
        imageUrl: "/test.png",
        width: 1190,
        height: 1684,
      },
    });

    // TextOverlay uses z-index: 20 — should be present for image fallback
    const textOverlay = container.querySelector('[style*="z-index: 20"]');
    expect(textOverlay).toBeTruthy();
  });

  it("renders PDF.js TextLayer div when pageProxy is provided", () => {
    const pageProxy = makeMockPageProxy();
    const { container } = render(HybridViewer, {
      props: {
        pageProxy,
        width: 1190,
        height: 1684,
      },
    });

    const textLayerDiv = container.querySelector("[data-text-layer]");
    expect(textLayerDiv).toBeTruthy();
  });
});
