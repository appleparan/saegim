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

function expiringToken(): string {
  return fakeJwt({
    sub: 'user-abc',
    role: 'annotator',
    exp: Math.floor(Date.now() / 1000) + 60, // expires in 60s (< 120s threshold)
  })
}

function expiredToken(): string {
  return fakeJwt({
    sub: 'user-abc',
    role: 'annotator',
    exp: Math.floor(Date.now() / 1000) - 60,
  })
}

const mockFetch = vi.fn()

describe('AuthStore', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    // Reset token directly to avoid triggering logoutFromServer fetch
    authStore.token = null
    authStore.isInitialized = false
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

    it('stores token in memory only (not localStorage)', () => {
      const token = validToken()
      authStore.setToken(token)

      expect(authStore.token).toBe(token)
      expect(localStorage.getItem('saegim_auth_token')).toBeNull()
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

    it('calls logoutFromServer to revoke refresh token', () => {
      authStore.setToken(validToken())
      authStore.logout()

      // logoutFromServer fires a POST to /auth/logout
      expect(mockFetch).toHaveBeenCalledOnce()
      const [url, init] = mockFetch.mock.calls[0]
      expect(url).toContain('/api/v1/auth/logout')
      expect(init.method).toBe('POST')
      expect(init.credentials).toBe('include')
    })
  })

  describe('checkExpiration', () => {
    it('returns false for a valid token', () => {
      authStore.setToken(validToken())
      expect(authStore.checkExpiration()).toBe(false)
      expect(authStore.isAuthenticated).toBe(true)
    })

    it('returns true and clears token for an expired token', () => {
      authStore.token = expiredToken()
      expect(authStore.checkExpiration()).toBe(true)
      expect(authStore.isAuthenticated).toBe(false)
    })
  })

  describe('shouldRefresh', () => {
    it('returns false when no token', () => {
      expect(authStore.shouldRefresh()).toBe(false)
    })

    it('returns false for a token expiring far in the future', () => {
      authStore.setToken(validToken()) // expires in 3600s
      expect(authStore.shouldRefresh()).toBe(false)
    })

    it('returns true for a token expiring within 2 minutes', () => {
      authStore.token = expiringToken() // expires in 60s < 120s
      expect(authStore.shouldRefresh()).toBe(true)
    })
  })

  describe('refreshToken', () => {
    it('sets new token on successful refresh', async () => {
      const newToken = validToken('admin')
      mockFetch.mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            access_token: newToken,
            token_type: 'bearer',
            must_change_password: false,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )

      const result = await authStore.refreshToken()

      expect(result).toBe(true)
      expect(authStore.token).toBe(newToken)
    })

    it('returns false on refresh failure', async () => {
      mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }))

      const result = await authStore.refreshToken()

      expect(result).toBe(false)
    })

    it('deduplicates concurrent refresh calls', async () => {
      const newToken = validToken()
      mockFetch.mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            access_token: newToken,
            token_type: 'bearer',
            must_change_password: false,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )

      // Fire two refreshes concurrently
      const [r1, r2] = await Promise.all([authStore.refreshToken(), authStore.refreshToken()])

      expect(r1).toBe(true)
      expect(r2).toBe(true)
      // Only one fetch call should have been made
      expect(mockFetch).toHaveBeenCalledOnce()
    })
  })

  describe('initialize', () => {
    it('calls refresh and sets isInitialized on success', async () => {
      const newToken = validToken()
      mockFetch.mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            access_token: newToken,
            token_type: 'bearer',
            must_change_password: false,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )

      await authStore.initialize()

      expect(authStore.isInitialized).toBe(true)
      expect(authStore.token).toBe(newToken)
    })

    it('sets isInitialized even on refresh failure', async () => {
      mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }))

      await authStore.initialize()

      expect(authStore.isInitialized).toBe(true)
      expect(authStore.token).toBeNull()
    })

    it('removes legacy localStorage token', async () => {
      localStorage.setItem('saegim_auth_token', 'legacy-token')
      mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }))

      await authStore.initialize()

      expect(localStorage.getItem('saegim_auth_token')).toBeNull()
    })

    it('does not clear token set while initialize is awaiting refresh', async () => {
      let resolveFetch: ((value: Response) => void) | null = null
      mockFetch.mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            resolveFetch = resolve
          }),
      )

      const initPromise = authStore.initialize()
      const tokenFromLogin = validToken('admin')
      authStore.setToken(tokenFromLogin)

      resolveFetch?.(new Response(null, { status: 401 }))
      await initPromise

      expect(authStore.token).toBe(tokenFromLogin)
      expect(authStore.isInitialized).toBe(true)
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
