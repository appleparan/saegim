import { describe, it, expect, beforeEach } from 'vitest'
import { autosaveStore } from '$lib/stores/autosave.svelte'

describe('AutosaveStore', () => {
  beforeEach(() => {
    autosaveStore.reset()
    localStorage.clear()
  })

  describe('initial state', () => {
    it('defaults to disabled', () => {
      expect(autosaveStore.enabled).toBe(false)
      expect(autosaveStore.lastSavedAt).toBeNull()
      expect(autosaveStore.isSaving).toBe(false)
    })
  })

  describe('setEnabled', () => {
    it('updates enabled state', () => {
      autosaveStore.setEnabled(true)
      expect(autosaveStore.enabled).toBe(true)
    })

    it('persists to localStorage', () => {
      autosaveStore.setEnabled(true)
      expect(localStorage.getItem('saegim:autosave:enabled')).toBe('true')

      autosaveStore.setEnabled(false)
      expect(localStorage.getItem('saegim:autosave:enabled')).toBe('false')
    })
  })

  describe('init', () => {
    it('restores enabled=true from localStorage', () => {
      localStorage.setItem('saegim:autosave:enabled', 'true')
      autosaveStore.init()
      expect(autosaveStore.enabled).toBe(true)
    })

    it('keeps enabled=false when localStorage has false', () => {
      localStorage.setItem('saegim:autosave:enabled', 'false')
      autosaveStore.init()
      expect(autosaveStore.enabled).toBe(false)
    })

    it('keeps enabled=false when localStorage is empty', () => {
      autosaveStore.init()
      expect(autosaveStore.enabled).toBe(false)
    })

    it('only initializes once', () => {
      localStorage.setItem('saegim:autosave:enabled', 'true')
      autosaveStore.init()
      expect(autosaveStore.enabled).toBe(true)

      // Change localStorage and re-init — should not change
      localStorage.setItem('saegim:autosave:enabled', 'false')
      autosaveStore.init()
      expect(autosaveStore.enabled).toBe(true)
    })
  })

  describe('markSaving', () => {
    it('sets isSaving to true', () => {
      autosaveStore.markSaving()
      expect(autosaveStore.isSaving).toBe(true)
    })
  })

  describe('markSaved', () => {
    it('sets isSaving to false and updates lastSavedAt', () => {
      autosaveStore.markSaving()
      expect(autosaveStore.isSaving).toBe(true)

      const before = new Date()
      autosaveStore.markSaved()
      const after = new Date()

      expect(autosaveStore.isSaving).toBe(false)
      expect(autosaveStore.lastSavedAt).not.toBeNull()
      expect(autosaveStore.lastSavedAt!.getTime()).toBeGreaterThanOrEqual(before.getTime())
      expect(autosaveStore.lastSavedAt!.getTime()).toBeLessThanOrEqual(after.getTime())
    })
  })

  describe('markSaveFailed', () => {
    it('sets isSaving to false without updating lastSavedAt', () => {
      autosaveStore.markSaving()
      autosaveStore.markSaveFailed()

      expect(autosaveStore.isSaving).toBe(false)
      expect(autosaveStore.lastSavedAt).toBeNull()
    })
  })

  describe('reset', () => {
    it('resets all state', () => {
      autosaveStore.setEnabled(true)
      autosaveStore.markSaving()
      autosaveStore.markSaved()

      autosaveStore.reset()

      expect(autosaveStore.enabled).toBe(false)
      expect(autosaveStore.lastSavedAt).toBeNull()
      expect(autosaveStore.isSaving).toBe(false)
    })

    it('allows re-initialization after reset', () => {
      localStorage.setItem('saegim:autosave:enabled', 'true')
      autosaveStore.init()
      expect(autosaveStore.enabled).toBe(true)

      autosaveStore.reset()
      expect(autosaveStore.enabled).toBe(false)

      // Should be able to init again
      localStorage.setItem('saegim:autosave:enabled', 'true')
      autosaveStore.init()
      expect(autosaveStore.enabled).toBe(true)
    })
  })
})
