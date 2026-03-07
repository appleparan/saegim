/**
 * Auto-save state management using Svelte 5 runes.
 * Settings persist to localStorage per browser.
 */

const STORAGE_KEY = 'saegim:autosave:enabled'

class AutosaveStore {
  enabled = $state(false)
  lastSavedAt = $state<Date | null>(null)
  isSaving = $state(false)

  private initialized = false

  /** Load enabled state from localStorage. Call once on mount. */
  init(): void {
    if (this.initialized) return
    this.initialized = true
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored === 'true') {
        this.enabled = true
      }
    } catch {
      // localStorage unavailable (SSR or private browsing)
    }
  }

  setEnabled(value: boolean): void {
    this.enabled = value
    try {
      localStorage.setItem(STORAGE_KEY, String(value))
    } catch {
      // localStorage unavailable
    }
  }

  markSaving(): void {
    this.isSaving = true
  }

  markSaved(): void {
    this.isSaving = false
    this.lastSavedAt = new Date()
  }

  markSaveFailed(): void {
    this.isSaving = false
  }

  /** Reset store state (for testing or cleanup). */
  reset(): void {
    this.enabled = false
    this.lastSavedAt = null
    this.isSaving = false
    this.initialized = false
  }
}

export const autosaveStore = new AutosaveStore()
