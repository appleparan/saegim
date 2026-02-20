import { describe, it, expect } from "vitest";
import {
  computeKonvaPointerEvents,
  computeTextPointerEvents,
  findHoveredImageBlock,
  resolveInteractionMode,
} from "$lib/utils/interaction";
import type { LayoutElement } from "$lib/types/omnidocbench";

function makeElement(
  annoId: number,
  category: LayoutElement["category_type"],
  x: number,
  y: number,
  w: number,
  h: number,
): LayoutElement {
  return {
    category_type: category,
    poly: [x, y, x + w, y, x + w, y + h, x, y + h],
    ignore: false,
    order: 0,
    anno_id: annoId,
  };
}

describe("computeKonvaPointerEvents", () => {
  it("returns auto in draw mode", () => {
    expect(computeKonvaPointerEvents("draw", "browse", null)).toBe("auto");
  });

  it("returns auto in edit mode", () => {
    expect(computeKonvaPointerEvents("select", "edit", null)).toBe("auto");
  });

  it("returns auto when hovering over image block", () => {
    expect(computeKonvaPointerEvents("select", "browse", 42)).toBe("auto");
  });

  it("returns none in default browse mode", () => {
    expect(computeKonvaPointerEvents("select", "browse", null)).toBe("none");
  });

  it("returns none in pan mode without hover", () => {
    expect(computeKonvaPointerEvents("pan", "browse", null)).toBe("none");
  });
});

describe("computeTextPointerEvents", () => {
  it("returns auto in default browse mode", () => {
    expect(computeTextPointerEvents("select", "browse", null)).toBe("auto");
  });

  it("returns none in draw mode", () => {
    expect(computeTextPointerEvents("draw", "browse", null)).toBe("none");
  });

  it("returns none in edit mode", () => {
    expect(computeTextPointerEvents("select", "edit", null)).toBe("none");
  });

  it("returns none when hovering over image block", () => {
    expect(computeTextPointerEvents("select", "browse", 42)).toBe("none");
  });

  it("returns auto in pan mode without hover", () => {
    expect(computeTextPointerEvents("pan", "browse", null)).toBe("auto");
  });
});

describe("computeKonva/Text pointer-events are mutually exclusive", () => {
  const scenarios = [
    { tool: "select", mode: "browse" as const, hover: null },
    { tool: "select", mode: "browse" as const, hover: 1 },
    { tool: "select", mode: "edit" as const, hover: null },
    { tool: "draw", mode: "browse" as const, hover: null },
    { tool: "pan", mode: "browse" as const, hover: null },
  ];

  for (const s of scenarios) {
    it(`tool=${s.tool} mode=${s.mode} hover=${s.hover}`, () => {
      const konva = computeKonvaPointerEvents(s.tool, s.mode, s.hover);
      const text = computeTextPointerEvents(s.tool, s.mode, s.hover);
      // At least one must be 'none' to prevent event conflicts
      expect(konva === "none" || text === "none").toBe(true);
    });
  }
});

describe("findHoveredImageBlock", () => {
  const containerRect = { x: 100, y: 50, width: 800, height: 600 };
  const elements: readonly LayoutElement[] = [
    makeElement(0, "text_block", 10, 10, 200, 30),
    makeElement(1, "figure", 50, 300, 400, 300),
    makeElement(2, "table", 500, 100, 200, 150),
  ];

  it("returns anno_id when cursor is over a figure", () => {
    // Screen point that maps to image point inside the figure (50,300)-(450,600)
    // With scale=1, offset=0: imagePoint = screenPoint - containerRect
    // We need imagePoint ~= (250, 450) → screenPoint = (350, 500)
    const result = findHoveredImageBlock(
      { x: 350, y: 500 },
      containerRect,
      0,
      0,
      1,
      elements,
    );
    expect(result).toBe(1);
  });

  it("returns anno_id when cursor is over a table", () => {
    // imagePoint ~= (550, 175) → screenPoint = (650, 225)
    const result = findHoveredImageBlock(
      { x: 650, y: 225 },
      containerRect,
      0,
      0,
      1,
      elements,
    );
    expect(result).toBe(2);
  });

  it("returns null when cursor is over a text block", () => {
    // imagePoint ~= (100, 20) → screenPoint = (200, 70)
    const result = findHoveredImageBlock(
      { x: 200, y: 70 },
      containerRect,
      0,
      0,
      1,
      elements,
    );
    expect(result).toBeNull();
  });

  it("returns null when cursor is over empty space", () => {
    const result = findHoveredImageBlock(
      { x: 150, y: 200 },
      containerRect,
      0,
      0,
      1,
      elements,
    );
    expect(result).toBeNull();
  });

  it("accounts for zoom and pan offset", () => {
    // scale=2, offset=(20, 30)
    // imagePoint = ((screenX - containerX) - offsetX) / scale
    // Need imagePoint inside figure (50,300)-(450,600)
    // Let target imagePoint = (250, 450)
    // screenX - containerX = 250 * 2 + 20 = 520 → screenX = 620
    // screenY - containerY = 450 * 2 + 30 = 930 → screenY = 980
    const result = findHoveredImageBlock(
      { x: 620, y: 980 },
      containerRect,
      20,
      30,
      2,
      elements,
    );
    expect(result).toBe(1);
  });

  it("returns null when elements list is empty", () => {
    const result = findHoveredImageBlock(
      { x: 200, y: 200 },
      containerRect,
      0,
      0,
      1,
      [],
    );
    expect(result).toBeNull();
  });
});

describe("resolveInteractionMode", () => {
  it("enters edit mode when selecting an image block", () => {
    const el = makeElement(1, "figure", 50, 300, 400, 300);
    expect(resolveInteractionMode("browse", el, 1)).toBe("edit");
  });

  it("stays in browse when selecting a text block", () => {
    const el = makeElement(0, "text_block", 10, 10, 200, 30);
    expect(resolveInteractionMode("browse", el, 0)).toBe("browse");
  });

  it("exits edit mode when selection is cleared", () => {
    expect(resolveInteractionMode("edit", null, null)).toBe("browse");
  });

  it("stays in browse when selection is cleared from browse", () => {
    expect(resolveInteractionMode("browse", null, null)).toBe("browse");
  });

  it("stays in edit when a different image block is selected", () => {
    const el = makeElement(2, "table", 500, 100, 200, 150);
    expect(resolveInteractionMode("edit", el, 2)).toBe("edit");
  });

  it("enters edit from browse when table is selected", () => {
    const el = makeElement(2, "table", 500, 100, 200, 150);
    expect(resolveInteractionMode("browse", el, 2)).toBe("edit");
  });

  it("enters edit when equation_isolated is selected", () => {
    const el = makeElement(3, "equation_isolated", 100, 100, 300, 50);
    expect(resolveInteractionMode("browse", el, 3)).toBe("edit");
  });
});
