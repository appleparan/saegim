import { describe, it, expect } from 'vitest'
import { BLOCK_CATEGORIES } from '$lib/types/categories'
import {
  IMAGE_BLOCK_CATEGORIES,
  TEXT_BLOCK_CATEGORIES,
  isImageBlock,
  isTextBlock,
} from '$lib/types/element-groups'
import type { LayoutElement } from '$lib/types/omnidocbench'
import type { BlockCategoryType } from '$lib/types/categories'

function makeElement(category: BlockCategoryType): LayoutElement {
  return {
    category_type: category,
    poly: [0, 0, 100, 0, 100, 50, 0, 50],
    ignore: false,
    order: 0,
    anno_id: 0,
  }
}

describe('element-groups', () => {
  it('covers all 18 block categories with no overlap', () => {
    const allGrouped = new Set([
      ...IMAGE_BLOCK_CATEGORIES,
      ...TEXT_BLOCK_CATEGORIES,
    ])

    expect(allGrouped.size).toBe(BLOCK_CATEGORIES.length)

    for (const cat of BLOCK_CATEGORIES) {
      expect(allGrouped.has(cat)).toBe(true)
    }
  })

  it('has no overlap between image and text groups', () => {
    for (const cat of IMAGE_BLOCK_CATEGORIES) {
      expect(TEXT_BLOCK_CATEGORIES.has(cat)).toBe(false)
    }
  })

  it('isImageBlock returns true for image categories', () => {
    expect(isImageBlock(makeElement('figure'))).toBe(true)
    expect(isImageBlock(makeElement('table'))).toBe(true)
    expect(isImageBlock(makeElement('equation_isolated'))).toBe(true)
  })

  it('isImageBlock returns false for text categories', () => {
    expect(isImageBlock(makeElement('title'))).toBe(false)
    expect(isImageBlock(makeElement('text_block'))).toBe(false)
    expect(isImageBlock(makeElement('header'))).toBe(false)
  })

  it('isTextBlock returns true for text categories', () => {
    expect(isTextBlock(makeElement('title'))).toBe(true)
    expect(isTextBlock(makeElement('text_block'))).toBe(true)
    expect(isTextBlock(makeElement('header'))).toBe(true)
    expect(isTextBlock(makeElement('footer'))).toBe(true)
    expect(isTextBlock(makeElement('reference'))).toBe(true)
  })

  it('isTextBlock returns false for image categories', () => {
    expect(isTextBlock(makeElement('figure'))).toBe(false)
    expect(isTextBlock(makeElement('table'))).toBe(false)
    expect(isTextBlock(makeElement('equation_isolated'))).toBe(false)
  })
})
