import { describe, it, expect } from 'vitest'
import { estimateFontSize } from '$lib/utils/text-layout'
import type { Poly } from '$lib/types/omnidocbench'

describe('estimateFontSize', () => {
  it('returns ~70% of bbox height for a single line', () => {
    const poly: Poly = [0, 0, 200, 0, 200, 20, 0, 20]
    const fontSize = estimateFontSize(poly)
    expect(fontSize).toBe(14) // 20 * 0.7 = 14
  })

  it('divides height by line count before applying ratio', () => {
    const poly: Poly = [0, 0, 200, 0, 200, 40, 0, 40]
    const fontSize = estimateFontSize(poly, 2)
    expect(fontSize).toBe(14) // (40 / 2) * 0.7 = 14
  })

  it('enforces minimum font size of 8', () => {
    const poly: Poly = [0, 0, 100, 0, 100, 5, 0, 5]
    const fontSize = estimateFontSize(poly)
    expect(fontSize).toBe(8) // 5 * 0.7 = 3.5, clamped to 8
  })

  it('treats lineCount <= 0 as 1', () => {
    const poly: Poly = [0, 0, 100, 0, 100, 20, 0, 20]
    expect(estimateFontSize(poly, 0)).toBe(14)
    expect(estimateFontSize(poly, -1)).toBe(14)
  })

  it('handles large bboxes', () => {
    const poly: Poly = [0, 0, 800, 0, 800, 100, 0, 100]
    const fontSize = estimateFontSize(poly)
    expect(fontSize).toBe(70) // 100 * 0.7 = 70
  })
})
