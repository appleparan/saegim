import { describe, it, expect } from "vitest";
import {
  polyToRect,
  rectToPoly,
  screenToImage,
  imageToScreen,
  pointInRect,
  clampRect,
  normalizeRect,
} from "$lib/utils/bbox";
import type { Poly } from "$lib/types/omnidocbench";

describe("polyToRect", () => {
  it("converts axis-aligned poly to rect", () => {
    const poly: Poly = [100, 200, 300, 200, 300, 400, 100, 400];
    const rect = polyToRect(poly);
    expect(rect).toEqual({ x: 100, y: 200, width: 200, height: 200 });
  });

  it("handles non-axis-aligned poly by using bounding box", () => {
    const poly: Poly = [150, 100, 300, 150, 250, 300, 100, 250];
    const rect = polyToRect(poly);
    expect(rect.x).toBe(100);
    expect(rect.y).toBe(100);
    expect(rect.width).toBe(200);
    expect(rect.height).toBe(200);
  });

  it("handles zero-size poly", () => {
    const poly: Poly = [50, 50, 50, 50, 50, 50, 50, 50];
    const rect = polyToRect(poly);
    expect(rect).toEqual({ x: 50, y: 50, width: 0, height: 0 });
  });
});

describe("rectToPoly", () => {
  it("converts rect to clockwise poly", () => {
    const rect = { x: 100, y: 200, width: 200, height: 150 };
    const poly = rectToPoly(rect);
    expect(poly).toEqual([100, 200, 300, 200, 300, 350, 100, 350]);
  });

  it("is inverse of polyToRect for axis-aligned polys", () => {
    const original: Poly = [10, 20, 110, 20, 110, 120, 10, 120];
    const rect = polyToRect(original);
    const roundTrip = rectToPoly(rect);
    expect(roundTrip).toEqual(original);
  });
});

describe("screenToImage / imageToScreen", () => {
  it("converts screen coords to image coords at 2x zoom", () => {
    const result = screenToImage({ x: 200, y: 300 }, 50, 50, 2);
    expect(result).toEqual({ x: 75, y: 125 });
  });

  it("converts image coords to screen coords at 2x zoom", () => {
    const result = imageToScreen({ x: 75, y: 125 }, 50, 50, 2);
    expect(result).toEqual({ x: 200, y: 300 });
  });

  it("round-trips correctly", () => {
    const original = { x: 150, y: 250 };
    const stageX = 30;
    const stageY = 40;
    const scale = 1.5;
    const image = screenToImage(original, stageX, stageY, scale);
    const screen = imageToScreen(image, stageX, stageY, scale);
    expect(screen.x).toBeCloseTo(original.x);
    expect(screen.y).toBeCloseTo(original.y);
  });
});

describe("pointInRect", () => {
  const rect = { x: 10, y: 20, width: 100, height: 50 };

  it("returns true for point inside", () => {
    expect(pointInRect({ x: 50, y: 40 }, rect)).toBe(true);
  });

  it("returns true for point on edge", () => {
    expect(pointInRect({ x: 10, y: 20 }, rect)).toBe(true);
    expect(pointInRect({ x: 110, y: 70 }, rect)).toBe(true);
  });

  it("returns false for point outside", () => {
    expect(pointInRect({ x: 5, y: 40 }, rect)).toBe(false);
    expect(pointInRect({ x: 50, y: 80 }, rect)).toBe(false);
  });
});

describe("clampRect", () => {
  it("clamps rect within bounds", () => {
    const rect = { x: -10, y: -20, width: 100, height: 50 };
    const clamped = clampRect(rect, 200, 200);
    expect(clamped.x).toBeGreaterThanOrEqual(0);
    expect(clamped.y).toBeGreaterThanOrEqual(0);
  });

  it("does not modify rect already within bounds", () => {
    const rect = { x: 10, y: 20, width: 50, height: 30 };
    const clamped = clampRect(rect, 200, 200);
    expect(clamped).toEqual(rect);
  });
});

describe("normalizeRect", () => {
  it("flips negative width/height", () => {
    const rect = { x: 100, y: 200, width: -50, height: -30 };
    const normalized = normalizeRect(rect);
    expect(normalized).toEqual({ x: 50, y: 170, width: 50, height: 30 });
  });

  it("keeps positive width/height unchanged", () => {
    const rect = { x: 10, y: 20, width: 100, height: 50 };
    expect(normalizeRect(rect)).toEqual(rect);
  });
});
