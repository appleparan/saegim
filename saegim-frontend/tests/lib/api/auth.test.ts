import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { login, register } from '$lib/api/auth'
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
    const tokenData = { access_token: 'jwt-token-123', token_type: 'bearer' }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, tokenData))

    const result = await login({ email: 'user@example.com', password: 'password123' })

    expect(result).toEqual(tokenData)
    expect(mockFetch).toHaveBeenCalledOnce()
  })

  it('throws ApiError on 401', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid email or password' }))

    await expect(login({ email: 'user@example.com', password: 'wrong' })).rejects.toThrow(ApiError)
  })
})

describe('register', () => {
  it('returns TokenResponse on success', async () => {
    const tokenData = { access_token: 'jwt-token-456', token_type: 'bearer' }
    mockFetch.mockResolvedValueOnce(jsonResponse(201, tokenData))

    const result = await register({
      name: 'Test User',
      email: 'new@example.com',
      password: 'password123',
    })

    expect(result).toEqual(tokenData)
  })

  it('throws ApiError on 409 (duplicate email)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(409, { detail: 'Email already registered' }))

    await expect(
      register({ name: 'User', email: 'exists@example.com', password: 'password123' }),
    ).rejects.toThrow(ApiError)
  })
})
