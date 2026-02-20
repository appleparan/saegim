/**
 * Category grouping for the hybrid labeling UI.
 *
 * Splits the 18 block categories into two groups:
 * - IMAGE_BLOCK_CATEGORIES: rendered as interactive Konva bboxes (canvas)
 * - TEXT_BLOCK_CATEGORIES: rendered as DOM text overlays (selectable text)
 */

import type { BlockCategoryType } from "./categories";
import type { LayoutElement } from "./omnidocbench";

/** Categories rendered as interactive Konva bboxes (image/table content). */
export const IMAGE_BLOCK_CATEGORIES: ReadonlySet<BlockCategoryType> = new Set([
  "figure",
  "table",
  "equation_isolated",
]);

/** Categories rendered as DOM text overlays (selectable text). */
export const TEXT_BLOCK_CATEGORIES: ReadonlySet<BlockCategoryType> = new Set([
  "title",
  "text_block",
  "header",
  "footer",
  "page_number",
  "page_footnote",
  "figure_caption",
  "figure_footnote",
  "table_caption",
  "table_footnote",
  "equation_caption",
  "code_txt",
  "code_txt_caption",
  "reference",
  "abandon",
]);

/** Check if an element belongs to the image block group (canvas bbox). */
export function isImageBlock(el: LayoutElement): boolean {
  return IMAGE_BLOCK_CATEGORIES.has(el.category_type);
}

/** Check if an element belongs to the text block group (DOM overlay). */
export function isTextBlock(el: LayoutElement): boolean {
  return TEXT_BLOCK_CATEGORIES.has(el.category_type);
}
