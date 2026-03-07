import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { checkLoginId, login, register } from '$lib/api/auth'
import { ApiError } from '$lib/api/client'

const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch)
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
    mockFetch.mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid ID or password' }))

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
