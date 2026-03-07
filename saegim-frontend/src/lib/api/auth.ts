/**
 * Authentication API calls.
 */

import { api } from './client'

export interface LoginRequest {
  readonly email: string
  readonly password: string
}

export interface RegisterRequest {
  readonly name: string
  readonly email: string
  readonly password: string
}

export interface TokenResponse {
  readonly access_token: string
  readonly token_type: string
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  return api.post<TokenResponse>('/api/v1/auth/login', data)
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  return api.post<TokenResponse>('/api/v1/auth/register', data)
}
