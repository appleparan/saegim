/**
 * Authentication API calls.
 */

import { api, API_BASE } from './client'

export interface LoginRequest {
  readonly login_id: string
  readonly password: string
}

export interface RegisterRequest {
  readonly name: string
  readonly login_id: string
  readonly password: string
}

export interface TokenResponse {
  readonly access_token: string
  readonly token_type: string
  readonly must_change_password: boolean
}

export interface LoginIdCheckResponse {
  readonly login_id: string
  readonly available: boolean
}

export interface CredentialUpdateRequest {
  readonly current_password: string
  readonly login_id?: string
  readonly email?: string
  readonly new_password?: string
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  return api.post<TokenResponse>('/api/v1/auth/login', data)
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  return api.post<TokenResponse>('/api/v1/auth/register', data)
}

export async function checkLoginId(loginId: string): Promise<LoginIdCheckResponse> {
  const query = encodeURIComponent(loginId)
  return api.get<LoginIdCheckResponse>(`/api/v1/auth/check-login-id?login_id=${query}`)
}

export async function updateMyCredentials(data: CredentialUpdateRequest): Promise<TokenResponse> {
  return api.patch<TokenResponse>('/api/v1/auth/me/credentials', data)
}

/**
 * Refresh the access token using the HttpOnly refresh cookie.
 * Uses raw fetch to bypass the api client's auto-refresh logic.
 */
export async function refreshAccessToken(): Promise<TokenResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
    if (!res.ok) return null
    return (await res.json()) as TokenResponse
  } catch {
    return null
  }
}

/**
 * Logout by revoking the refresh token on the server.
 * Uses raw fetch to bypass the api client.
 */
export async function logoutFromServer(): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
  } catch {
    // Ignore errors — we're logging out anyway
  }
}
