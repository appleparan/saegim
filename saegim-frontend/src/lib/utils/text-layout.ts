/**
 * Utilities for estimating text layout properties from bbox geometry.
 *
 * Used by the DOM text overlay to approximate font size from the
 * OmniDocBench poly coordinates.
 */

import type { Poly } from '$lib/types/omnidocbench'
import { polyToRect } from './bbox'

/** Minimum font size to prevent unreadable text. */
const MIN_FONT_SIZE = 8

/** Ratio of font size to line height (heuristic). */
const FONT_HEIGHT_RATIO = 0.7

/**
 * Estimate font size from a poly bounding box.
 *
 * The heuristic divides the bbox height by the number of lines,
 * then applies FONT_HEIGHT_RATIO to approximate the CSS font-size.
 */
export function estimateFontSize(poly: Poly, lineCount: number = 1): number {
  const rect = polyToRect(poly)
  const safeLineCount = Math.max(lineCount, 1)
  const lineHeight = rect.height / safeLineCount
  return Math.max(MIN_FONT_SIZE, Math.round(lineHeight * FONT_HEIGHT_RATIO))
}
