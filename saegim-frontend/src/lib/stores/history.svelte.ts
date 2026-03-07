/**
 * Undo/redo history management using snapshot-based approach.
 * Stores deep clones of AnnotationData before each mutation.
 */

import type { AnnotationData } from '$lib/types/omnidocbench'

const MAX_HISTORY = 50

class HistoryStore {
  // Use $state.raw to avoid deep Svelte 5 proxying on stack contents.
  // structuredClone cannot clone Svelte proxies, and we always replace
  // the entire array reference so shallow reactivity is sufficient.
  private undoStack = $state.raw<AnnotationData[]>([])
  private redoStack = $state.raw<AnnotationData[]>([])

  canUndo = $derived(this.undoStack.length > 0)
  canRedo = $derived(this.redoStack.length > 0)

  undoCount = $derived(this.undoStack.length)
  redoCount = $derived(this.redoStack.length)

  /**
   * Record current state before a mutation.
   * Clears redo stack (new user action invalidates redo history).
   */
  push(snapshot: AnnotationData): void {
    const clone = structuredClone(snapshot)
    this.undoStack = [...this.undoStack.slice(-(MAX_HISTORY - 1)), clone]
    this.redoStack = []
  }

  /**
   * Undo: restore previous state.
   *
   * @param currentState - the current annotationData before undo
   * @returns the restored state, or null if nothing to undo
   */
  undo(currentState: AnnotationData): AnnotationData | null {
    if (this.undoStack.length === 0) return null
    const newUndo = [...this.undoStack]
    const previous = newUndo.pop()!
    this.undoStack = newUndo
    this.redoStack = [...this.redoStack, structuredClone(currentState)]
    return previous
  }

  /**
   * Redo: restore next state.
   *
   * @param currentState - the current annotationData before redo
   * @returns the restored state, or null if nothing to redo
   */
  redo(currentState: AnnotationData): AnnotationData | null {
    if (this.redoStack.length === 0) return null
    const newRedo = [...this.redoStack]
    const next = newRedo.pop()!
    this.redoStack = newRedo
    this.undoStack = [...this.undoStack, structuredClone(currentState)]
    return next
  }

  /** Clear all history (e.g., when loading a new page). */
  clear(): void {
    this.undoStack = []
    this.redoStack = []
  }
}

export const historyStore = new HistoryStore()
