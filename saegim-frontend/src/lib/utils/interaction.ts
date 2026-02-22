/**
 * Pure utility functions for the hybrid viewer interaction logic.
 *
 * Extracted from HybridViewer.svelte for testability.
 */

import type { LayoutElement } from '$lib/types/omnidocbench'
import type { Point, Rect } from '$lib/types/canvas'
import { isImageBlock } from '$lib/types/element-groups'
import { polyToRect, pointInRect, screenToImage } from './bbox'

export type InteractionMode = 'browse' | 'edit'

/**
 * Determine pointer-events for the Konva container.
 *
 * Returns 'auto' when the canvas should receive clicks:
 * - draw mode, edit mode, or cursor hovering over an image block.
 */
export function computeKonvaPointerEvents(
  toolMode: string,
  interactionMode: InteractionMode,
  hoveredImageBlockId: number | null,
): 'auto' | 'none' {
  if (toolMode === 'draw' || interactionMode === 'edit' || hoveredImageBlockId !== null) {
    return 'auto'
  }
  return 'none'
}

/**
 * Determine pointer-events for the text overlay.
 *
 * Returns 'auto' only when the user should be able to select text:
 * browse mode with cursor NOT over an image block.
 */
export function computeTextPointerEvents(
  toolMode: string,
  interactionMode: InteractionMode,
  hoveredImageBlockId: number | null,
): 'auto' | 'none' {
  if (toolMode === 'draw' || interactionMode === 'edit' || hoveredImageBlockId !== null) {
    return 'none'
  }
  return 'auto'
}

/**
 * Find the anno_id of the image block under the given screen coordinates.
 *
 * Returns the anno_id if found, null otherwise.
 */
export function findHoveredImageBlock(
  screenPoint: Point,
  containerRect: Rect,
  offsetX: number,
  offsetY: number,
  scale: number,
  elements: readonly LayoutElement[],
): number | null {
  const imagePoint = screenToImage(
    {
      x: screenPoint.x - containerRect.x,
      y: screenPoint.y - containerRect.y,
    },
    offsetX,
    offsetY,
    scale,
  )

  for (const el of elements) {
    if (!isImageBlock(el)) continue
    if (pointInRect(imagePoint, polyToRect(el.poly))) {
      return el.anno_id
    }
  }
  return null
}

/**
 * Compute the next interaction mode based on selection state.
 */
export function resolveInteractionMode(
  currentMode: InteractionMode,
  selectedElement: LayoutElement | null,
  selectedElementId: number | null,
): InteractionMode {
  // Enter edit mode when an image block is selected
  if (selectedElement && isImageBlock(selectedElement)) {
    return 'edit'
  }
  // Exit edit mode when selection is cleared
  if (selectedElementId === null && currentMode === 'edit') {
    return 'browse'
  }
  return currentMode
}
