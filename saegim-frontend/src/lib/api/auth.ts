/**
 * Authentication API calls.
 */

import { api } from './client'

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
