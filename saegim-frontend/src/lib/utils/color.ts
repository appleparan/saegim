/**
 * Category-to-color mapping for bbox rendering.
 */

import type { BlockCategoryType } from '$lib/types/categories'

const CATEGORY_COLORS: Record<BlockCategoryType, string> = {
  title: '#e74c3c',
  text_block: '#3498db',
  figure: '#2ecc71',
  figure_caption: '#27ae60',
  figure_footnote: '#1abc9c',
  table: '#f39c12',
  table_caption: '#e67e22',
  table_footnote: '#d35400',
  equation_isolated: '#9b59b6',
  equation_caption: '#8e44ad',
  header: '#95a5a6',
  footer: '#7f8c8d',
  page_number: '#bdc3c7',
  page_footnote: '#34495e',
  abandon: '#c0392b',
  code_txt: '#2c3e50',
  code_txt_caption: '#1a252f',
  reference: '#16a085',
}

/** Get the display color for a block category type. */
export function getCategoryColor(category: BlockCategoryType): string {
  return CATEGORY_COLORS[category] ?? '#95a5a6'
}
