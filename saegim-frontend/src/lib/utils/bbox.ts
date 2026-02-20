/**
 * Bbox geometry helpers for converting between OmniDocBench poly coordinates and Rect.
 */

import type { Poly } from "$lib/types/omnidocbench";
import type { Point, Rect } from "$lib/types/canvas";

/** Convert OmniDocBench poly [x1,y1,x2,y2,x3,y3,x4,y4] to axis-aligned Rect. */
export function polyToRect(poly: Poly): Rect {
  const xs = [poly[0], poly[2], poly[4], poly[6]];
  const ys = [poly[1], poly[3], poly[5], poly[7]];
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  return {
    x: minX,
    y: minY,
    width: Math.max(...xs) - minX,
    height: Math.max(...ys) - minY,
  };
}

/** Convert axis-aligned Rect back to poly (clockwise from top-left). */
export function rectToPoly(rect: Rect): Poly {
  return [
    rect.x,
    rect.y,
    rect.x + rect.width,
    rect.y,
    rect.x + rect.width,
    rect.y + rect.height,
    rect.x,
    rect.y + rect.height,
  ];
}

/** Convert screen coordinates to image coordinates accounting for zoom/pan. */
export function screenToImage(
  point: Point,
  stageX: number,
  stageY: number,
  scale: number,
): Point {
  return {
    x: (point.x - stageX) / scale,
    y: (point.y - stageY) / scale,
  };
}

/** Convert image coordinates to screen coordinates accounting for zoom/pan. */
export function imageToScreen(
  point: Point,
  stageX: number,
  stageY: number,
  scale: number,
): Point {
  return {
    x: point.x * scale + stageX,
    y: point.y * scale + stageY,
  };
}

/** Check if a point is inside a rect. */
export function pointInRect(point: Point, rect: Rect): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  );
}

/** Clamp a rect to stay within image bounds. */
export function clampRect(
  rect: Rect,
  imageWidth: number,
  imageHeight: number,
): Rect {
  const x = Math.max(0, Math.min(rect.x, imageWidth - rect.width));
  const y = Math.max(0, Math.min(rect.y, imageHeight - rect.height));
  const width = Math.min(rect.width, imageWidth - x);
  const height = Math.min(rect.height, imageHeight - y);
  return { x, y, width, height };
}

/** Normalize a rect so width/height are always positive. */
export function normalizeRect(rect: Rect): Rect {
  return {
    x: rect.width < 0 ? rect.x + rect.width : rect.x,
    y: rect.height < 0 ? rect.y + rect.height : rect.y,
    width: Math.abs(rect.width),
    height: Math.abs(rect.height),
  };
}
