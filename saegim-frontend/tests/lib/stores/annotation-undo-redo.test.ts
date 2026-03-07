import { describe, it, expect, beforeEach } from 'vitest'
import { annotationStore } from '$lib/stores/annotation.svelte'
import type { AnnotationData } from '$lib/types/omnidocbench'

function baseAnnotation(): AnnotationData {
  return {
    layout_dets: [
      {
        category_type: 'text_block' as const,
        poly: [0, 0, 100, 0, 100, 100, 0, 100] as const,
        ignore: false,
        order: 0,
        anno_id: 0,
        text: 'hello',
      },
    ],
    page_attribute: { language: 'ko' },
    extra: { relation: [] },
  }
}

describe('AnnotationStore Undo/Redo', () => {
  beforeEach(() => {
    annotationStore.load('page-1', baseAnnotation())
  })

  describe('undo updateElement', () => {
    it('reverts element text change', () => {
      annotationStore.updateElement(0, { text: 'changed' })
      expect(annotationStore.elements[0].text).toBe('changed')

      annotationStore.undo()
      expect(annotationStore.elements[0].text).toBe('hello')
    })

    it('redo restores element text change', () => {
      annotationStore.updateElement(0, { text: 'changed' })
      annotationStore.undo()
      annotationStore.redo()
      expect(annotationStore.elements[0].text).toBe('changed')
    })
  })

  describe('undo updateElementAttribute', () => {
    it('reverts attribute change', () => {
      annotationStore.updateElementAttribute(0, 'bold', true)
      expect(annotationStore.elements[0].attribute?.bold).toBe(true)

      annotationStore.undo()
      expect(annotationStore.elements[0].attribute?.bold).toBeUndefined()
    })
  })

  describe('undo addElement', () => {
    it('removes the added element', () => {
      annotationStore.addElement('title', [10, 10, 50, 10, 50, 50, 10, 50])
      expect(annotationStore.elements).toHaveLength(2)

      annotationStore.undo()
      expect(annotationStore.elements).toHaveLength(1)
    })

    it('redo restores the added element', () => {
      annotationStore.addElement('title', [10, 10, 50, 10, 50, 50, 10, 50])
      annotationStore.undo()
      annotationStore.redo()
      expect(annotationStore.elements).toHaveLength(2)
    })
  })

  describe('undo removeElement', () => {
    it('restores the removed element', () => {
      annotationStore.removeElement(0)
      expect(annotationStore.elements).toHaveLength(0)

      annotationStore.undo()
      expect(annotationStore.elements).toHaveLength(1)
      expect(annotationStore.elements[0].text).toBe('hello')
    })
  })

  describe('undo addRelation', () => {
    it('removes the added relation', () => {
      annotationStore.addElement('figure', [10, 10, 50, 10, 50, 50, 10, 50])
      annotationStore.addRelation(0, 1, 'figure_caption')
      expect(annotationStore.relations).toHaveLength(1)

      annotationStore.undo()
      expect(annotationStore.relations).toHaveLength(0)
    })
  })

  describe('undo removeRelation', () => {
    it('restores the removed relation', () => {
      annotationStore.addElement('figure', [10, 10, 50, 10, 50, 50, 10, 50])
      annotationStore.addRelation(0, 1, 'figure_caption')
      annotationStore.removeRelation(0, 1)
      expect(annotationStore.relations).toHaveLength(0)

      annotationStore.undo()
      expect(annotationStore.relations).toHaveLength(1)
    })
  })

  describe('undo reorderElements', () => {
    it('reverts order changes', () => {
      annotationStore.addElement('title', [10, 10, 50, 10, 50, 50, 10, 50])
      annotationStore.reorderElements({ 0: 1, 1: 0 })

      const el0Before = annotationStore.elements.find((e) => e.anno_id === 0)
      expect(el0Before!.order).toBe(1)

      annotationStore.undo()
      const el0After = annotationStore.elements.find((e) => e.anno_id === 0)
      expect(el0After!.order).toBe(0)
    })
  })

  describe('undo updatePageAttribute', () => {
    it('reverts page attribute change', () => {
      annotationStore.updatePageAttribute({ language: 'en' })
      expect(annotationStore.pageAttribute?.language).toBe('en')

      annotationStore.undo()
      expect(annotationStore.pageAttribute?.language).toBe('ko')
    })
  })

  describe('selectedElementId preservation', () => {
    it('keeps selection if element still exists after undo', () => {
      annotationStore.selectElement(0)
      annotationStore.updateElement(0, { text: 'changed' })
      annotationStore.undo()
      expect(annotationStore.selectedElementId).toBe(0)
    })

    it('clears selection if element no longer exists after undo', () => {
      const newId = annotationStore.addElement('title', [10, 10, 50, 10, 50, 50, 10, 50])
      annotationStore.selectElement(newId)
      annotationStore.undo()
      expect(annotationStore.selectedElementId).toBeNull()
    })
  })

  describe('isDirty after undo/redo', () => {
    it('remains dirty after undo', () => {
      annotationStore.updateElement(0, { text: 'changed' })
      annotationStore.undo()
      expect(annotationStore.isDirty).toBe(true)
    })

    it('remains dirty after redo', () => {
      annotationStore.updateElement(0, { text: 'changed' })
      annotationStore.undo()
      annotationStore.redo()
      expect(annotationStore.isDirty).toBe(true)
    })
  })

  describe('load clears history', () => {
    it('clears undo and redo stacks on load', () => {
      annotationStore.updateElement(0, { text: 'changed' })
      expect(annotationStore.canUndo).toBe(true)

      annotationStore.load('page-2', baseAnnotation())
      expect(annotationStore.canUndo).toBe(false)
      expect(annotationStore.canRedo).toBe(false)
    })
  })

  describe('clear clears history', () => {
    it('clears undo and redo stacks on clear', () => {
      annotationStore.updateElement(0, { text: 'changed' })
      expect(annotationStore.canUndo).toBe(true)

      annotationStore.clear()
      expect(annotationStore.canUndo).toBe(false)
      expect(annotationStore.canRedo).toBe(false)
    })
  })

  describe('new action clears redo', () => {
    it('clears redo stack when new mutation occurs after undo', () => {
      annotationStore.updateElement(0, { text: 'v1' })
      annotationStore.updateElement(0, { text: 'v2' })
      annotationStore.undo()
      expect(annotationStore.canRedo).toBe(true)

      annotationStore.updateElement(0, { text: 'v3' })
      expect(annotationStore.canRedo).toBe(false)
    })
  })

  describe('undo with no data', () => {
    it('does nothing when annotationData is null', () => {
      annotationStore.clear()
      annotationStore.undo()
      expect(annotationStore.annotationData).toBeNull()
    })

    it('redo does nothing when annotationData is null', () => {
      annotationStore.clear()
      annotationStore.redo()
      expect(annotationStore.annotationData).toBeNull()
    })
  })

  describe('multiple sequential undos', () => {
    it('reverts through multiple changes', () => {
      annotationStore.updateElement(0, { text: 'v1' })
      annotationStore.updateElement(0, { text: 'v2' })
      annotationStore.updateElement(0, { text: 'v3' })

      annotationStore.undo()
      expect(annotationStore.elements[0].text).toBe('v2')

      annotationStore.undo()
      expect(annotationStore.elements[0].text).toBe('v1')

      annotationStore.undo()
      expect(annotationStore.elements[0].text).toBe('hello')
    })
  })

  describe('canUndo and canRedo derived state', () => {
    it('reflects history availability', () => {
      expect(annotationStore.canUndo).toBe(false)
      expect(annotationStore.canRedo).toBe(false)

      annotationStore.updateElement(0, { text: 'changed' })
      expect(annotationStore.canUndo).toBe(true)
      expect(annotationStore.canRedo).toBe(false)

      annotationStore.undo()
      expect(annotationStore.canUndo).toBe(false)
      expect(annotationStore.canRedo).toBe(true)

      annotationStore.redo()
      expect(annotationStore.canUndo).toBe(true)
      expect(annotationStore.canRedo).toBe(false)
    })
  })
})
