import { describe, it, expect, beforeEach } from 'vitest'
import { historyStore } from '$lib/stores/history.svelte'
import type { AnnotationData } from '$lib/types/omnidocbench'

function makeAnnotation(elementCount: number): AnnotationData {
  return {
    layout_dets: Array.from({ length: elementCount }, (_, i) => ({
      category_type: 'text_block' as const,
      poly: [0, 0, 100, 0, 100, 100, 0, 100] as const,
      ignore: false,
      order: i,
      anno_id: i,
    })),
    page_attribute: {},
    extra: { relation: [] },
  }
}

describe('HistoryStore', () => {
  beforeEach(() => {
    historyStore.clear()
  })

  describe('initial state', () => {
    it('starts with empty stacks', () => {
      expect(historyStore.canUndo).toBe(false)
      expect(historyStore.canRedo).toBe(false)
      expect(historyStore.undoCount).toBe(0)
      expect(historyStore.redoCount).toBe(0)
    })
  })

  describe('push', () => {
    it('adds snapshot to undo stack', () => {
      historyStore.push(makeAnnotation(1))
      expect(historyStore.canUndo).toBe(true)
      expect(historyStore.undoCount).toBe(1)
    })

    it('clears redo stack on push', () => {
      const s0 = makeAnnotation(0)
      const s1 = makeAnnotation(1)
      const s2 = makeAnnotation(2)
      historyStore.push(s0)
      historyStore.push(s1)
      historyStore.undo(s2)
      expect(historyStore.canRedo).toBe(true)

      historyStore.push(makeAnnotation(3))
      expect(historyStore.canRedo).toBe(false)
    })

    it('limits undo stack to MAX_HISTORY (50)', () => {
      for (let i = 0; i < 60; i++) {
        historyStore.push(makeAnnotation(i))
      }
      expect(historyStore.undoCount).toBe(50)
    })

    it('deep clones snapshot to prevent mutation', () => {
      const data = makeAnnotation(1)
      historyStore.push(data)
      // Mutate original after push
      ;(data as unknown as { layout_dets: unknown[] }).layout_dets = []
      const restored = historyStore.undo(makeAnnotation(0))
      expect(restored!.layout_dets).toHaveLength(1)
    })
  })

  describe('undo', () => {
    it('returns null when nothing to undo', () => {
      expect(historyStore.undo(makeAnnotation(0))).toBeNull()
    })

    it('restores previous state and pushes current to redo', () => {
      const s0 = makeAnnotation(0)
      const s1 = makeAnnotation(1)
      historyStore.push(s0)
      const restored = historyStore.undo(s1)
      expect(restored!.layout_dets).toHaveLength(0)
      expect(historyStore.canRedo).toBe(true)
      expect(historyStore.canUndo).toBe(false)
    })

    it('supports multiple consecutive undos', () => {
      const s0 = makeAnnotation(0)
      const s1 = makeAnnotation(1)
      const s2 = makeAnnotation(2)
      historyStore.push(s0)
      historyStore.push(s1)
      const first = historyStore.undo(s2)
      expect(first!.layout_dets).toHaveLength(1)
      const second = historyStore.undo(first!)
      expect(second!.layout_dets).toHaveLength(0)
    })
  })

  describe('redo', () => {
    it('returns null when nothing to redo', () => {
      expect(historyStore.redo(makeAnnotation(0))).toBeNull()
    })

    it('restores next state and pushes current to undo', () => {
      const s0 = makeAnnotation(0)
      const s1 = makeAnnotation(1)
      historyStore.push(s0)
      historyStore.undo(s1)
      const restored = historyStore.redo(s0)
      expect(restored!.layout_dets).toHaveLength(1)
      expect(historyStore.canUndo).toBe(true)
      expect(historyStore.canRedo).toBe(false)
    })
  })

  describe('undo-redo round trip', () => {
    it('preserves data through undo then redo', () => {
      const s0 = makeAnnotation(1)
      const s1 = makeAnnotation(2)
      historyStore.push(s0)
      const undone = historyStore.undo(s1)
      const redone = historyStore.redo(undone!)
      expect(redone!.layout_dets).toHaveLength(2)
    })

    it('supports multiple undo-redo cycles', () => {
      const s0 = makeAnnotation(0)
      const s1 = makeAnnotation(1)
      const s2 = makeAnnotation(2)
      historyStore.push(s0)
      historyStore.push(s1)

      // undo twice
      const u1 = historyStore.undo(s2)
      const u2 = historyStore.undo(u1!)

      // redo twice
      const r1 = historyStore.redo(u2!)
      const r2 = historyStore.redo(r1!)
      expect(r2!.layout_dets).toHaveLength(2)
    })
  })

  describe('clear', () => {
    it('empties both stacks', () => {
      historyStore.push(makeAnnotation(0))
      historyStore.push(makeAnnotation(1))
      historyStore.clear()
      expect(historyStore.canUndo).toBe(false)
      expect(historyStore.canRedo).toBe(false)
      expect(historyStore.undoCount).toBe(0)
      expect(historyStore.redoCount).toBe(0)
    })
  })
})
