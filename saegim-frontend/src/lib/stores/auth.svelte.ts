/**
 * Authentication state management using Svelte 5 runes.
 * Follows the class-based singleton pattern from other stores.
 */

import { decodeJwtPayload, isTokenExpired, type JwtPayload } from '$lib/utils/jwt'

const TOKEN_KEY = 'saegim_auth_token'

export type UserRole = 'admin' | 'annotator' | 'reviewer'

export interface AuthUser {
  readonly id: string
  readonly role: UserRole
}

class AuthStore {
  token = $state<string | null>(null)

  payload = $derived<JwtPayload | null>(this.token ? decodeJwtPayload(this.token) : null)

  user = $derived<AuthUser | null>(
    this.payload && !isTokenExpired(this.payload)
      ? { id: this.payload.sub, role: this.payload.role }
      : null,
  )

  isAuthenticated = $derived(this.user !== null)

  isAdmin = $derived(this.user?.role === 'admin')

  constructor() {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(TOKEN_KEY)
      if (stored) {
        const decoded = decodeJwtPayload(stored)
        if (decoded && !isTokenExpired(decoded)) {
          this.token = stored
        } else {
          localStorage.removeItem(TOKEN_KEY)
        }
      }
    }
  }

  setToken(token: string): void {
    this.token = token
    localStorage.setItem(TOKEN_KEY, token)
  }

  logout(): void {
    this.token = null
    localStorage.removeItem(TOKEN_KEY)
  }

  /**
   * Check token expiration and auto-logout if expired.
   * Returns true if the token was expired and removed.
   */
  checkExpiration(): boolean {
    if (this.payload && isTokenExpired(this.payload)) {
      this.logout()
      return true
    }
    return false
  }
}

export const authStore = new AuthStore()
