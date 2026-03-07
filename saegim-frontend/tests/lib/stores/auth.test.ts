import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { authStore } from '$lib/stores/auth.svelte'

/** Build a fake JWT with the given payload. */
function fakeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = btoa(JSON.stringify(payload))
  return `${header}.${body}.fake-signature`
}

function validToken(role: string = 'annotator', mustChangePassword: boolean = false): string {
  return fakeJwt({
    sub: 'user-abc',
    role,
    must_change_password: mustChangePassword,
    exp: Math.floor(Date.now() / 1000) + 3600,
  })
}

function expiredToken(): string {
  return fakeJwt({
    sub: 'user-abc',
    role: 'annotator',
    exp: Math.floor(Date.now() / 1000) - 60,
  })
}

describe('AuthStore', () => {
  beforeEach(() => {
    authStore.logout()
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('setToken', () => {
    it('sets token and updates derived state', () => {
      const token = validToken()
      authStore.setToken(token)

      expect(authStore.token).toBe(token)
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.user).toEqual({
        id: 'user-abc',
        role: 'annotator',
        mustChangePassword: false,
      })
    })

    it('persists token to localStorage', () => {
      const token = validToken()
      authStore.setToken(token)

      expect(localStorage.getItem('saegim_auth_token')).toBe(token)
    })
  })

  describe('logout', () => {
    it('clears all auth state', () => {
      authStore.setToken(validToken())
      authStore.logout()

      expect(authStore.token).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.user).toBeNull()
    })

    it('removes token from localStorage', () => {
      authStore.setToken(validToken())
      authStore.logout()

      expect(localStorage.getItem('saegim_auth_token')).toBeNull()
    })
  })

  describe('checkExpiration', () => {
    it('returns false for a valid token', () => {
      authStore.setToken(validToken())
      expect(authStore.checkExpiration()).toBe(false)
      expect(authStore.isAuthenticated).toBe(true)
    })

    it('returns true and logs out for an expired token', () => {
      // Directly set an expired token (bypassing setToken validation)
      authStore.token = expiredToken()
      expect(authStore.checkExpiration()).toBe(true)
      expect(authStore.isAuthenticated).toBe(false)
      expect(localStorage.getItem('saegim_auth_token')).toBeNull()
    })
  })

  describe('isAdmin', () => {
    it('returns true for admin role', () => {
      authStore.setToken(validToken('admin'))
      expect(authStore.isAdmin).toBe(true)
    })

    it('returns false for annotator role', () => {
      authStore.setToken(validToken('annotator'))
      expect(authStore.isAdmin).toBe(false)
    })

    it('returns false for reviewer role', () => {
      authStore.setToken(validToken('reviewer'))
      expect(authStore.isAdmin).toBe(false)
    })

    it('returns false when not authenticated', () => {
      expect(authStore.isAdmin).toBe(false)
    })
  })

  describe('mustChangePassword', () => {
    it('returns true when payload requires password change', () => {
      authStore.setToken(validToken('admin', true))
      expect(authStore.mustChangePassword).toBe(true)
    })

    it('returns false when payload does not require password change', () => {
      authStore.setToken(validToken('annotator', false))
      expect(authStore.mustChangePassword).toBe(false)
    })
  })
})
