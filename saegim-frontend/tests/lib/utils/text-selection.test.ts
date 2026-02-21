import { describe, it, expect } from "vitest";
import {
  rectsOverlap,
  findOverlappingBbox,
  selectionToImageRect,
} from "$lib/utils/text-selection";
import type { LayoutElement } from "$lib/types/omnidocbench";

function makeElement(
  annoId: number,
  x: number,
  y: number,
  w: number,
  h: number,
  category: string = "text_block",
): LayoutElement {
  return {
    anno_id: annoId,
    category_type: category,
    poly: [x, y, x + w, y, x + w, y + h, x, y + h],
    ignore: false,
    order: annoId,
  } as LayoutElement;
}

describe("rectsOverlap", () => {
  it("returns true for overlapping rectangles", () => {
    const a = { x: 0, y: 0, width: 100, height: 100 };
    const b = { x: 50, y: 50, width: 100, height: 100 };
    expect(rectsOverlap(a, b)).toBe(true);
  });

  it("returns true for contained rectangle", () => {
    const a = { x: 0, y: 0, width: 200, height: 200 };
    const b = { x: 50, y: 50, width: 50, height: 50 };
    expect(rectsOverlap(a, b)).toBe(true);
  });

  it("returns false for non-overlapping rectangles", () => {
    const a = { x: 0, y: 0, width: 100, height: 100 };
    const b = { x: 200, y: 200, width: 100, height: 100 };
    expect(rectsOverlap(a, b)).toBe(false);
  });

  it("returns false for touching but not overlapping rectangles", () => {
    const a = { x: 0, y: 0, width: 100, height: 100 };
    const b = { x: 100, y: 0, width: 100, height: 100 };
    expect(rectsOverlap(a, b)).toBe(false);
  });

  it("returns false for horizontally separated", () => {
    const a = { x: 0, y: 0, width: 50, height: 50 };
    const b = { x: 60, y: 0, width: 50, height: 50 };
    expect(rectsOverlap(a, b)).toBe(false);
  });

  it("returns false for vertically separated", () => {
    const a = { x: 0, y: 0, width: 50, height: 50 };
    const b = { x: 0, y: 60, width: 50, height: 50 };
    expect(rectsOverlap(a, b)).toBe(false);
  });
});

describe("findOverlappingBbox", () => {
  it("returns null for empty elements list", () => {
    const selection = { x: 10, y: 10, width: 50, height: 20 };
    expect(findOverlappingBbox(selection, [])).toBeNull();
  });

  it("returns null when no elements overlap", () => {
    const selection = { x: 500, y: 500, width: 50, height: 20 };
    const elements = [
      makeElement(0, 10, 10, 100, 30),
      makeElement(1, 10, 50, 100, 30),
    ];
    expect(findOverlappingBbox(selection, elements)).toBeNull();
  });

  it("returns the anno_id of the overlapping element", () => {
    const selection = { x: 30, y: 15, width: 50, height: 10 };
    const elements = [
      makeElement(0, 10, 10, 100, 30),
      makeElement(1, 10, 200, 100, 30),
    ];
    expect(findOverlappingBbox(selection, elements)).toBe(0);
  });

  it("returns the element with largest overlap area", () => {
    const selection = { x: 80, y: 10, width: 100, height: 30 };
    const elements = [
      makeElement(0, 10, 10, 100, 30), // overlap: (100-80)*30 = 600
      makeElement(1, 90, 10, 200, 30), // overlap: (180-90)*30 = 2700 (larger)
    ];
    expect(findOverlappingBbox(selection, elements)).toBe(1);
  });

  it("handles single pixel overlap", () => {
    const selection = { x: 99, y: 0, width: 10, height: 10 };
    const elements = [makeElement(0, 0, 0, 100, 100)];
    expect(findOverlappingBbox(selection, elements)).toBe(0);
  });
});

describe("selectionToImageRect", () => {
  it("returns null for collapsed selection", () => {
    const mockSelection = {
      rangeCount: 1,
      isCollapsed: true,
      getRangeAt: () => ({ commonAncestorContainer: document.body }),
    } as unknown as Selection;

    const container = document.createElement("div");
    expect(selectionToImageRect(mockSelection, container, 0, 0, 1)).toBeNull();
  });

  it("returns null for empty selection (no ranges)", () => {
    const mockSelection = {
      rangeCount: 0,
      isCollapsed: false,
    } as unknown as Selection;

    const container = document.createElement("div");
    expect(selectionToImageRect(mockSelection, container, 0, 0, 1)).toBeNull();
  });

  it("returns null when selection is outside container", () => {
    const container = document.createElement("div");
    const outsideNode = document.createElement("div");

    const mockRange = {
      commonAncestorContainer: outsideNode,
      getClientRects: () => [],
    };

    const mockSelection = {
      rangeCount: 1,
      isCollapsed: false,
      getRangeAt: () => mockRange,
    } as unknown as Selection;

    expect(selectionToImageRect(mockSelection, container, 0, 0, 1)).toBeNull();
  });

  it("returns image-space rect when selection is valid", () => {
    const container = document.createElement("div");
    document.body.appendChild(container);
    const textNode = document.createTextNode("hello");
    container.appendChild(textNode);

    // Mock getBoundingClientRect for the container
    container.getBoundingClientRect = () =>
      ({ left: 100, top: 50, right: 300, bottom: 250 }) as DOMRect;

    const mockRange = {
      commonAncestorContainer: textNode,
      getClientRects: () => [
        { left: 120, top: 60, right: 200, bottom: 80 } as DOMRect,
      ],
    };

    const mockSelection = {
      rangeCount: 1,
      isCollapsed: false,
      getRangeAt: () => mockRange,
    } as unknown as Selection;

    // Scale = 1, offset = 0
    const result = selectionToImageRect(mockSelection, container, 0, 0, 1);
    expect(result).not.toBeNull();
    // Selection at (120, 60) relative to container at (100, 50) = image (20, 10)
    expect(result!.x).toBe(20);
    expect(result!.y).toBe(10);
    expect(result!.width).toBe(80); // 200 - 120
    expect(result!.height).toBe(20); // 80 - 60

    document.body.removeChild(container);
  });

  it("accounts for scale when converting to image coordinates", () => {
    const container = document.createElement("div");
    document.body.appendChild(container);
    const textNode = document.createTextNode("hello");
    container.appendChild(textNode);

    container.getBoundingClientRect = () =>
      ({ left: 0, top: 0, right: 400, bottom: 400 }) as DOMRect;

    const mockRange = {
      commonAncestorContainer: textNode,
      getClientRects: () => [
        { left: 40, top: 20, right: 140, bottom: 60 } as DOMRect,
      ],
    };

    const mockSelection = {
      rangeCount: 1,
      isCollapsed: false,
      getRangeAt: () => mockRange,
    } as unknown as Selection;

    // Scale = 2 (zoomed in 2x)
    const result = selectionToImageRect(mockSelection, container, 0, 0, 2);
    expect(result).not.toBeNull();
    expect(result!.x).toBe(20); // 40 / 2
    expect(result!.y).toBe(10); // 20 / 2
    expect(result!.width).toBe(50); // 100 / 2
    expect(result!.height).toBe(20); // 40 / 2

    document.body.removeChild(container);
  });
});
