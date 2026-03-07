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
  vi.stubGlobal('fetch', mockFetch)
  // Reset token directly to avoid triggering logoutFromServer fetch
  authStore.token = null
  mockFetch.mockReset()
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

describe('credentials include', () => {
  it('sends credentials: include on all requests', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(200, { data: 'ok' }))

    await api.get('/api/v1/test')

    const [, init] = mockFetch.mock.calls[0]
    expect(init.credentials).toBe('include')
  })

  it('sends credentials: include on upload requests', async () => {
    mockFetch.mockResolvedValueOnce(new Response('ok', { status: 200 }))

    await api.upload('/api/v1/upload', new FormData())

    const [, init] = mockFetch.mock.calls[0]
    expect(init.credentials).toBe('include')
  })
})

describe('401 refresh and retry', () => {
  it('attempts refresh and retries on 401', async () => {
    authStore.setToken(validToken())
    const newToken = validToken()

    // 1st call: original request → 401
    mockFetch.mockResolvedValueOnce(jsonResponse(401, { detail: 'Unauthorized' }))
    // 2nd call: refresh → success
    mockFetch.mockResolvedValueOnce(
      jsonResponse(200, {
        access_token: newToken,
        token_type: 'bearer',
        must_change_password: false,
      }),
    )
    // 3rd call: retry original request → success
    mockFetch.mockResolvedValueOnce(jsonResponse(200, { data: 'ok' }))

    const result = await api.get<{ data: string }>('/api/v1/protected')

    expect(result).toEqual({ data: 'ok' })
    expect(mockFetch).toHaveBeenCalledTimes(3)
  })

  it('logs out when refresh fails on 401', async () => {
    authStore.setToken(validToken())
    expect(authStore.isAuthenticated).toBe(true)

    // 1st call: original request → 401
    mockFetch.mockResolvedValueOnce(jsonResponse(401, { detail: 'Unauthorized' }))
    // 2nd call: refresh → failure
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }))
    // 3rd call: logoutFromServer (fire-and-forget)
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 204 }))

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
