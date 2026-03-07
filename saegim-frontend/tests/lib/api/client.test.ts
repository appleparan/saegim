import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { authStore } from '$lib/stores/auth.svelte'
import { api, ApiError } from '$lib/api/client'

/** Build a fake JWT with the given payload. */
function fakeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = btoa(JSON.stringify(payload))
  return `${header}.${body}.fake-signature`
}

function validToken(): string {
  return fakeJwt({
    sub: 'user-1',
    role: 'annotator',
    exp: Math.floor(Date.now() / 1000) + 3600,
  })
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: { 'Content-Type': 'application/json' },
  })
}

const mockFetch = vi.fn()

beforeEach(() => {
  mockFetch.mockReset()
  vi.stubGlobal('fetch', mockFetch)
  authStore.logout()
  localStorage.clear()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('auth header injection', () => {
  it('does not include Authorization header when no token', async () => {
    expect(authStore.token).toBeNull()
    mockFetch.mockResolvedValueOnce(jsonResponse(200, { data: 'ok' }))

    await api.get('/api/v1/test')

    const [, init] = mockFetch.mock.calls[0]
    expect(init.headers).not.toHaveProperty('Authorization')
  })

  it('includes Authorization header when token is set', async () => {
    authStore.setToken(validToken())
    mockFetch.mockResolvedValueOnce(jsonResponse(200, { data: 'ok' }))

    await api.get('/api/v1/test')

    const [, init] = mockFetch.mock.calls[0]
    expect(init.headers).toHaveProperty('Authorization')
    expect(init.headers.Authorization).toMatch(/^Bearer /)
  })

  it('includes Authorization header for upload (requestRaw)', async () => {
    authStore.setToken(validToken())
    mockFetch.mockResolvedValueOnce(new Response('ok', { status: 200 }))

    const formData = new FormData()
    await api.upload('/api/v1/upload', formData)

    const [, init] = mockFetch.mock.calls[0]
    expect(init.headers).toHaveProperty('Authorization')
  })
})

describe('401 auto-logout', () => {
  it('calls authStore.logout on 401 response', async () => {
    authStore.setToken(validToken())
    expect(authStore.isAuthenticated).toBe(true)

    mockFetch.mockResolvedValueOnce(jsonResponse(401, { detail: 'Unauthorized' }))

    await expect(api.get('/api/v1/protected')).rejects.toThrow(ApiError)
    expect(authStore.isAuthenticated).toBe(false)
  })

  it('does not logout on non-401 errors', async () => {
    authStore.setToken(validToken())
    mockFetch.mockResolvedValueOnce(jsonResponse(500, { detail: 'Server error' }))

    await expect(api.get('/api/v1/test')).rejects.toThrow(ApiError)
    expect(authStore.isAuthenticated).toBe(true)
  })
})
