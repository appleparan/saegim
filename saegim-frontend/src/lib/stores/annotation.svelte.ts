/**
 * Core annotation state management using Svelte 5 runes.
 * All mutations produce new objects (immutability).
 */

import type { AnnotationData, LayoutElement, PageAttribute } from '$lib/types/omnidocbench'
import type { BlockCategoryType } from '$lib/types/categories'

class AnnotationStore {
  pageId = $state<string | null>(null)
  annotationData = $state<AnnotationData | null>(null)
  selectedElementId = $state<number | null>(null)
  isDirty = $state(false)
  isLoading = $state(false)
  error = $state<string | null>(null)

  elements = $derived(this.annotationData?.layout_dets ?? [])

  selectedElement = $derived(
    this.elements.find((el) => el.anno_id === this.selectedElementId) ?? null,
  )

  pageAttribute = $derived(this.annotationData?.page_attribute ?? null)

  relations = $derived(this.annotationData?.extra?.relation ?? [])

  load(pageId: string, data: AnnotationData): void {
    this.pageId = pageId
    this.annotationData = data
    this.selectedElementId = null
    this.isDirty = false
    this.error = null
  }

  clear(): void {
    this.pageId = null
    this.annotationData = null
    this.selectedElementId = null
    this.isDirty = false
    this.error = null
  }

  selectElement(annoId: number | null): void {
    this.selectedElementId = annoId
  }

  updateElement(annoId: number, updates: Partial<LayoutElement>): void {
    if (!this.annotationData) return
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

    const annoId = this.getNextAnnoId()
    const newElement: LayoutElement = {
      category_type: categoryType,
      poly: poly as LayoutElement['poly'],
      ignore: false,
      order: this.annotationData.layout_dets.length,
      anno_id: annoId,
    }

    this.annotationData = {
      ...this.annotationData,
      layout_dets: [...this.annotationData.layout_dets, newElement],
    }
    this.isDirty = true
    return annoId
  }

  removeElement(annoId: number): void {
    if (!this.annotationData) return

    this.annotationData = {
      ...this.annotationData,
      layout_dets: this.annotationData.layout_dets.filter((el) => el.anno_id !== annoId),
      extra: {
        ...this.annotationData.extra,
        relation: this.annotationData.extra.relation.filter(
          (r) => r.source_anno_id !== annoId && r.target_anno_id !== annoId,
        ),
      },
    }

    if (this.selectedElementId === annoId) {
      this.selectedElementId = null
    }
    this.isDirty = true
  }

  updatePageAttribute(updates: Partial<PageAttribute>): void {
    if (!this.annotationData) return
    this.annotationData = {
      ...this.annotationData,
      page_attribute: { ...this.annotationData.page_attribute, ...updates },
    }
    this.isDirty = true
  }

  getNextAnnoId(): number {
    if (!this.annotationData || this.annotationData.layout_dets.length === 0) {
      return 0
    }
    return Math.max(...this.annotationData.layout_dets.map((el) => el.anno_id)) + 1
  }

  markSaved(): void {
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
