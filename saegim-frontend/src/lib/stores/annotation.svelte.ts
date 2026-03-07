/**
 * Core annotation state management using Svelte 5 runes.
 * All mutations produce new objects (immutability).
 */

import type { AnnotationData, LayoutElement, PageAttribute } from '$lib/types/omnidocbench'
import type { BlockCategoryType } from '$lib/types/categories'
import { historyStore } from './history.svelte'

class AnnotationStore {
  pageId = $state<string | null>(null)
  annotationData = $state<AnnotationData | null>(null)
  selectedElementId = $state<number | null>(null)
  selectedElementIds = $state.raw<number[]>([])
  isDirty = $state(false)
  isLoading = $state(false)
  error = $state<string | null>(null)
  private selectionAnchorId = $state<number | null>(null)
  private lastSavedAnnotationData = $state.raw<AnnotationData | null>(null)

  elements = $derived(this.annotationData?.layout_dets ?? [])

  selectedElement = $derived(
    this.elements.find((el) => el.anno_id === this.selectedElementId) ?? null,
  )

  pageAttribute = $derived(this.annotationData?.page_attribute ?? null)

  relations = $derived(this.annotationData?.extra?.relation ?? [])

  canUndo = $derived(historyStore.canUndo)
  canRedo = $derived(historyStore.canRedo)
  selectedCount = $derived(this.selectedElementIds.length)

  /** Record current annotationData snapshot for undo before a mutation. */
  private recordHistory(): void {
    if (this.annotationData) {
      // $state.snapshot strips the Svelte 5 deep proxy so structuredClone works
      historyStore.push($state.snapshot(this.annotationData) as AnnotationData)
    }
  }

  private hasElement(annoId: number): boolean {
    return this.elements.some((el) => el.anno_id === annoId)
  }

  private getSortedElementsByOrder(): LayoutElement[] {
    return [...this.elements].sort((a, b) => a.order - b.order)
  }

  private getCurrentSelectionIds(): number[] {
    if (this.selectedElementIds.length > 0) {
      return [...this.selectedElementIds]
    }
    if (this.selectedElementId !== null) {
      return [this.selectedElementId]
    }
    return []
  }

  private syncSelectionWithCurrentElements(): void {
    const existingIds = new Set(this.elements.map((el) => el.anno_id))
    this.selectedElementIds = this.selectedElementIds.filter((id) => existingIds.has(id))

    if (this.selectedElementIds.length === 0) {
      this.selectedElementId = null
      this.selectionAnchorId = null
      return
    }

    if (
      this.selectedElementId === null ||
      !existingIds.has(this.selectedElementId) ||
      !this.selectedElementIds.includes(this.selectedElementId)
    ) {
      this.selectedElementId = this.selectedElementIds[this.selectedElementIds.length - 1] ?? null
    }

    if (this.selectionAnchorId !== null && !existingIds.has(this.selectionAnchorId)) {
      this.selectionAnchorId = this.selectedElementId
    }
  }

  load(pageId: string, data: AnnotationData): void {
    this.pageId = pageId
    this.annotationData = data
    this.lastSavedAnnotationData = structuredClone(data)
    this.selectedElementId = null
    this.selectedElementIds = []
    this.selectionAnchorId = null
    this.isDirty = false
    this.error = null
    historyStore.clear()
  }

  clear(): void {
    this.pageId = null
    this.annotationData = null
    this.lastSavedAnnotationData = null
    this.selectedElementId = null
    this.selectedElementIds = []
    this.selectionAnchorId = null
    this.isDirty = false
    this.error = null
    historyStore.clear()
  }

  clearSelection(): void {
    this.selectedElementId = null
    this.selectedElementIds = []
    this.selectionAnchorId = null
  }

  selectElement(annoId: number | null): void {
    if (annoId === null) {
      this.clearSelection()
      return
    }
    if (!this.hasElement(annoId)) {
      this.clearSelection()
      return
    }
    this.selectedElementId = annoId
    this.selectedElementIds = [annoId]
    this.selectionAnchorId = annoId
  }

  toggleElementSelection(annoId: number): void {
    if (!this.hasElement(annoId)) return

    if (this.selectedElementIds.includes(annoId)) {
      this.selectedElementIds = this.selectedElementIds.filter((id) => id !== annoId)
      if (this.selectedElementIds.length === 0) {
        this.selectedElementId = null
        this.selectionAnchorId = null
      } else if (this.selectedElementId === annoId) {
        this.selectedElementId = this.selectedElementIds[this.selectedElementIds.length - 1] ?? null
      }
      return
    }

    this.selectedElementIds = [...this.selectedElementIds, annoId]
    this.selectedElementId = annoId
    this.selectionAnchorId = annoId
  }

  selectRangeToElement(annoId: number, additive = false): void {
    if (!this.hasElement(annoId)) return

    const anchorId = this.selectionAnchorId ?? this.selectedElementId ?? annoId
    const sorted = this.getSortedElementsByOrder()
    const anchorIdx = sorted.findIndex((el) => el.anno_id === anchorId)
    const targetIdx = sorted.findIndex((el) => el.anno_id === annoId)

    if (anchorIdx < 0 || targetIdx < 0) {
      this.selectElement(annoId)
      return
    }

    const start = Math.min(anchorIdx, targetIdx)
    const end = Math.max(anchorIdx, targetIdx)
    const rangeIds = sorted.slice(start, end + 1).map((el) => el.anno_id)

    if (additive) {
      const merged = new Set([...this.selectedElementIds, ...rangeIds])
      this.selectedElementIds = [...merged]
    } else {
      this.selectedElementIds = rangeIds
    }

    this.selectedElementId = annoId
    this.selectionAnchorId = anchorId
  }

  isElementSelected(annoId: number): boolean {
    return this.selectedElementIds.includes(annoId)
  }

  updateElement(annoId: number, updates: Partial<LayoutElement>): void {
    if (!this.annotationData) return
    this.recordHistory()
    this.annotationData = {
      ...this.annotationData,
      layout_dets: this.annotationData.layout_dets.map((el) =>
        el.anno_id === annoId ? { ...el, ...updates } : el,
      ),
    }
    this.isDirty = true
  }

  updateElementAttribute(annoId: number, key: string, value: string | boolean): void {
    if (!this.annotationData) return
    this.recordHistory()
    this.annotationData = {
      ...this.annotationData,
      layout_dets: this.annotationData.layout_dets.map((el) =>
        el.anno_id === annoId ? { ...el, attribute: { ...el.attribute, [key]: value } } : el,
      ),
    }
    this.isDirty = true
  }

  addElement(categoryType: BlockCategoryType, poly: readonly number[]): number {
    if (!this.annotationData) return -1
    this.recordHistory()

    const layoutDets = this.annotationData.layout_dets ?? []
    const annoId = this.getNextAnnoId()
    const newElement: LayoutElement = {
      category_type: categoryType,
      poly: poly as LayoutElement['poly'],
      ignore: false,
      order: layoutDets.length,
      anno_id: annoId,
    }

    this.annotationData = {
      ...this.annotationData,
      layout_dets: [...layoutDets, newElement],
      extra: this.annotationData.extra ?? { relation: [] },
    }
    this.isDirty = true
    return annoId
  }

  removeElement(annoId: number): void {
    this.removeElements([annoId])
  }

  removeElements(annoIds: readonly number[]): void {
    if (!this.annotationData) return
    const targetIds = new Set(annoIds.filter((id) => this.hasElement(id)))
    if (targetIds.size === 0) return

    this.recordHistory()

    const layoutDets = this.annotationData.layout_dets ?? []
    const relations = this.annotationData.extra?.relation ?? []

    this.annotationData = {
      ...this.annotationData,
      layout_dets: layoutDets.filter((el) => !targetIds.has(el.anno_id)),
      extra: {
        ...this.annotationData.extra,
        relation: relations.filter(
          (r) => !targetIds.has(r.source_anno_id) && !targetIds.has(r.target_anno_id),
        ),
      },
    }

    this.syncSelectionWithCurrentElements()
    this.isDirty = true
  }

  removeSelectedElements(): void {
    this.removeElements(this.getCurrentSelectionIds())
  }

  addRelation(sourceAnnoId: number, targetAnnoId: number, relationType: string): void {
    if (!this.annotationData) return
    this.recordHistory()
    this.annotationData = {
      ...this.annotationData,
      extra: {
        ...this.annotationData.extra,
        relation: [
          ...(this.annotationData.extra?.relation ?? []),
          {
            source_anno_id: sourceAnnoId,
            target_anno_id: targetAnnoId,
            relation_type: relationType,
          },
        ],
      },
    }
    this.isDirty = true
  }

  removeRelation(sourceAnnoId: number, targetAnnoId: number): void {
    if (!this.annotationData) return
    this.recordHistory()
    this.annotationData = {
      ...this.annotationData,
      extra: {
        ...this.annotationData.extra,
        relation: (this.annotationData.extra?.relation ?? []).filter(
          (r) => !(r.source_anno_id === sourceAnnoId && r.target_anno_id === targetAnnoId),
        ),
      },
    }
    this.isDirty = true
  }

  getRelationsForElement(annoId: number): readonly import('$lib/types/omnidocbench').Relation[] {
    return this.relations.filter((r) => r.source_anno_id === annoId || r.target_anno_id === annoId)
  }

  reorderElements(orderMap: Record<number, number>): void {
    if (!this.annotationData) return
    this.recordHistory()
    this.annotationData = {
      ...this.annotationData,
      layout_dets: this.annotationData.layout_dets.map((el) =>
        el.anno_id in orderMap ? { ...el, order: orderMap[el.anno_id] } : el,
      ),
    }
    this.isDirty = true
  }

  swapElementOrder(annoId1: number, annoId2: number): void {
    if (!this.annotationData) return
    const el1 = this.annotationData.layout_dets.find((el) => el.anno_id === annoId1)
    const el2 = this.annotationData.layout_dets.find((el) => el.anno_id === annoId2)
    if (!el1 || !el2) return
    this.reorderElements({
      [annoId1]: el2.order,
      [annoId2]: el1.order,
    })
  }

  updatePageAttribute(updates: Partial<PageAttribute>): void {
    if (!this.annotationData) return
    this.recordHistory()
    this.annotationData = {
      ...this.annotationData,
      page_attribute: { ...this.annotationData.page_attribute, ...updates },
    }
    this.isDirty = true
  }

  getNextAnnoId(): number {
    const layoutDets = this.annotationData?.layout_dets ?? []
    if (layoutDets.length === 0) {
      return 0
    }
    return Math.max(...layoutDets.map((el) => el.anno_id)) + 1
  }

  moveSelectedElements(delta: -1 | 1): void {
    if (!this.annotationData) return

    const selectedIds = this.getCurrentSelectionIds()
    if (selectedIds.length === 0) return

    const selectedSet = new Set(selectedIds)
    const reordered = this.getSortedElementsByOrder()
    let moved = false

    if (delta < 0) {
      for (let i = 1; i < reordered.length; i++) {
        const current = reordered[i]
        const previous = reordered[i - 1]
        if (selectedSet.has(current.anno_id) && !selectedSet.has(previous.anno_id)) {
          ;[reordered[i - 1], reordered[i]] = [reordered[i], reordered[i - 1]]
          moved = true
        }
      }
    } else {
      for (let i = reordered.length - 2; i >= 0; i--) {
        const current = reordered[i]
        const next = reordered[i + 1]
        if (selectedSet.has(current.anno_id) && !selectedSet.has(next.anno_id)) {
          ;[reordered[i], reordered[i + 1]] = [reordered[i + 1], reordered[i]]
          moved = true
        }
      }
    }

    if (!moved) return

    this.recordHistory()
    const orderMap: Record<number, number> = {}
    for (let i = 0; i < reordered.length; i++) {
      orderMap[reordered[i].anno_id] = i
    }

    this.annotationData = {
      ...this.annotationData,
      layout_dets: this.annotationData.layout_dets.map((el) =>
        el.anno_id in orderMap ? { ...el, order: orderMap[el.anno_id] } : el,
      ),
    }
    this.isDirty = true
  }

  /** Undo the last mutation, restoring previous annotationData. */
  undo(): void {
    if (!this.annotationData) return
    const current = $state.snapshot(this.annotationData) as AnnotationData
    const restored = historyStore.undo(current)
    if (!restored) return
    this.annotationData = restored
    this.syncSelectionWithCurrentElements()
    this.isDirty = true
  }

  /** Redo the last undone mutation. */
  redo(): void {
    if (!this.annotationData) return
    const current = $state.snapshot(this.annotationData) as AnnotationData
    const restored = historyStore.redo(current)
    if (!restored) return
    this.annotationData = restored
    this.syncSelectionWithCurrentElements()
    this.isDirty = true
  }

  markSaved(): void {
    if (this.annotationData) {
      this.lastSavedAnnotationData = structuredClone(
        $state.snapshot(this.annotationData) as AnnotationData,
      )
    }
    this.isDirty = false
  }

  revertToLastSaved(): void {
    if (!this.annotationData || !this.lastSavedAnnotationData) return
    this.recordHistory()
    this.annotationData = structuredClone(this.lastSavedAnnotationData)
    this.syncSelectionWithCurrentElements()
    this.isDirty = false
  }

  setLoading(loading: boolean): void {
    this.isLoading = loading
  }

  setError(error: string | null): void {
    this.error = error
  }
}

export const annotationStore = new AnnotationStore()
