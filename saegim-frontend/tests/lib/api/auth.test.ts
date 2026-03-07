import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  checkLoginId,
  login,
  register,
  updateMyCredentials,
  refreshAccessToken,
  logoutFromServer,
} from '$lib/api/auth'
import { ApiError } from '$lib/api/client'
import { authStore } from '$lib/stores/auth.svelte'

const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch)
  // Reset token directly to avoid triggering logoutFromServer fetch
  authStore.token = null
  mockFetch.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('login', () => {
  it('returns TokenResponse on success', async () => {
    const tokenData = {
      access_token: 'jwt-token-123',
      token_type: 'bearer',
      must_change_password: false,
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, tokenData))

    const result = await login({ login_id: 'user01', password: 'password123' })

    expect(result).toEqual(tokenData)
    expect(mockFetch).toHaveBeenCalledOnce()
  })

  it('throws ApiError on 401', async () => {
    // 1st call: login → 401
    mockFetch.mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid ID or password' }))
    // 2nd call: refresh attempt (triggered by 401 handler) → fails
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }))

    await expect(login({ login_id: 'user01', password: 'wrong' })).rejects.toThrow(ApiError)
  })
})

describe('register', () => {
  it('returns TokenResponse on success', async () => {
    const tokenData = {
      access_token: 'jwt-token-456',
      token_type: 'bearer',
      must_change_password: false,
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(201, tokenData))

    const result = await register({
      name: 'Test User',
      login_id: 'newuser',
      password: 'password123',
    })

    expect(result).toEqual(tokenData)
  })

  it('throws ApiError on 409 (duplicate login ID)', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse(409, { detail: 'User with this login ID already exists' }),
    )

    await expect(
      register({ name: 'User', login_id: 'exists', password: 'password123' }),
    ).rejects.toThrow(ApiError)
  })
})

describe('checkLoginId', () => {
  it('returns availability response', async () => {
    const payload = { login_id: 'newuser', available: true }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, payload))

    const result = await checkLoginId('newuser')
    expect(result).toEqual(payload)
  })
})

describe('updateMyCredentials', () => {
  it('returns TokenResponse on success', async () => {
    const tokenData = {
      access_token: 'jwt-token-updated',
      token_type: 'bearer',
      must_change_password: false,
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, tokenData))

    const result = await updateMyCredentials({
      current_password: 'oldpass123',
      login_id: 'newid',
      email: 'new@example.com',
      new_password: 'newpass123',
    })

    expect(result).toEqual(tokenData)
  })

  it('throws ApiError on 401', async () => {
    // 1st call: credentials update → 401
    mockFetch.mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid current password' }))
    // 2nd call: refresh attempt → fails
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }))

    await expect(
      updateMyCredentials({ current_password: 'wrongpass', login_id: 'newid' }),
    ).rejects.toThrow(ApiError)
  })
})

describe('refreshAccessToken', () => {
  it('returns TokenResponse on success', async () => {
    const tokenData = {
      access_token: 'new-jwt-token',
      token_type: 'bearer',
      must_change_password: false,
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, tokenData))

    const result = await refreshAccessToken()

    expect(result).toEqual(tokenData)
    const [url, init] = mockFetch.mock.calls[0]
    expect(url).toContain('/api/v1/auth/refresh')
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('include')
  })

  it('returns null on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }))

    const result = await refreshAccessToken()

    expect(result).toBeNull()
  })

  it('returns null on network error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    const result = await refreshAccessToken()

    expect(result).toBeNull()
  })
})

describe('logoutFromServer', () => {
  it('sends POST to /auth/logout with credentials', async () => {
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 204 }))

    await logoutFromServer()

    expect(mockFetch).toHaveBeenCalledOnce()
    const [url, init] = mockFetch.mock.calls[0]
    expect(url).toContain('/api/v1/auth/logout')
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('include')
  })

  it('does not throw on network error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    await expect(logoutFromServer()).resolves.toBeUndefined()
  })
})
