/**
 * Utilities for mapping text selections to bbox coordinates.
 */

import type { Rect } from "$lib/types/canvas";
import type { LayoutElement } from "$lib/types/omnidocbench";
import { polyToRect } from "./bbox";

/** Check if two rectangles overlap. */
export function rectsOverlap(a: Rect, b: Rect): boolean {
  return (
    a.x < b.x + b.width &&
    a.x + a.width > b.x &&
    a.y < b.y + b.height &&
    a.y + a.height > b.y
  );
}

/**
 * Find the first element whose bbox overlaps with the given rectangle.
 * Returns the anno_id of the best matching element, or null if none found.
 */
export function findOverlappingBbox(
  selectionRect: Rect,
  elements: readonly LayoutElement[],
): number | null {
  let bestId: number | null = null;
  let bestOverlap = 0;

  for (const el of elements) {
    const elRect = polyToRect(el.poly);
    if (!rectsOverlap(selectionRect, elRect)) continue;

    // Calculate intersection area
    const overlapX = Math.max(
      0,
      Math.min(selectionRect.x + selectionRect.width, elRect.x + elRect.width) -
        Math.max(selectionRect.x, elRect.x),
    );
    const overlapY = Math.max(
      0,
      Math.min(
        selectionRect.y + selectionRect.height,
        elRect.y + elRect.height,
      ) - Math.max(selectionRect.y, elRect.y),
    );
    const overlapArea = overlapX * overlapY;

    if (overlapArea > bestOverlap) {
      bestOverlap = overlapArea;
      bestId = el.anno_id;
    }
  }

  return bestId;
}

/**
 * Convert a browser Selection range to image-space coordinates.
 * The container must be the transform-origin element that holds the text divs.
 * offsetX/offsetY/scale are the viewport transform values.
 *
 * Returns null if the selection is empty or outside the container.
 */
export function selectionToImageRect(
  selection: Selection,
  container: HTMLElement,
  offsetX: number,
  offsetY: number,
  scale: number,
): Rect | null {
  if (!selection.rangeCount || selection.isCollapsed) return null;

  const range = selection.getRangeAt(0);

  // Check that the selection is within our container
  if (!container.contains(range.commonAncestorContainer)) return null;

  const rects = range.getClientRects();
  if (rects.length === 0) return null;

  // Compute bounding box of all client rects
  const containerRect = container.getBoundingClientRect();
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  for (const r of rects) {
    minX = Math.min(minX, r.left);
    minY = Math.min(minY, r.top);
    maxX = Math.max(maxX, r.right);
    maxY = Math.max(maxY, r.bottom);
  }

  // Convert from screen coordinates to image coordinates.
  // containerRect already accounts for the CSS transform (translate + scale),
  // so we need to convert screen-relative positions back to image space.
  const imageX = (minX - containerRect.left) / scale;
  const imageY = (minY - containerRect.top) / scale;
  const imageWidth = (maxX - minX) / scale;
  const imageHeight = (maxY - minY) / scale;

  if (imageWidth < 1 || imageHeight < 1) return null;

  return { x: imageX, y: imageY, width: imageWidth, height: imageHeight };
}
