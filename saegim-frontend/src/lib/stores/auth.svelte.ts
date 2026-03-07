/**
 * Authentication state management using Svelte 5 runes.
 * Access token stored in memory only (not localStorage).
 * Refresh token managed via HttpOnly cookie by the server.
 */

import { refreshAccessToken, logoutFromServer } from '$lib/api/auth'
import { decodeJwtPayload, isTokenExpired, type JwtPayload } from '$lib/utils/jwt'

export type UserRole = 'admin' | 'annotator' | 'reviewer'

export interface AuthUser {
  readonly id: string
  readonly role: UserRole
  readonly mustChangePassword: boolean
}

class AuthStore {
  token = $state<string | null>(null)

  isInitialized = $state(false)

  payload = $derived<JwtPayload | null>(this.token ? decodeJwtPayload(this.token) : null)

  user = $derived<AuthUser | null>(
    this.payload && !isTokenExpired(this.payload)
      ? {
          id: this.payload.sub,
          role: this.payload.role,
          mustChangePassword: this.payload.must_change_password === true,
        }
      : null,
  )

  isAuthenticated = $derived(this.user !== null)

  isAdmin = $derived(this.user?.role === 'admin')

  mustChangePassword = $derived(this.user?.mustChangePassword === true)

  private _refreshPromise: Promise<boolean> | null = null

  setToken(token: string): void {
    this.token = token
  }

  logout(): void {
    this.token = null
    logoutFromServer()
  }

  /**
   * Initialize auth state on app load.
   * Tries to refresh access token using the HttpOnly refresh cookie.
   */
  async initialize(): Promise<void> {
    if (typeof window === 'undefined') return

    // Migrate: remove any legacy localStorage token
    localStorage.removeItem('saegim_auth_token')

    const success = await this.refreshToken()
    if (!success) {
      this.token = null
    }
    this.isInitialized = true
  }

  /**
   * Refresh the access token using the HttpOnly refresh cookie.
   * Deduplicates concurrent refresh calls.
   * Returns true if refresh succeeded.
   */
  async refreshToken(): Promise<boolean> {
    if (this._refreshPromise) return this._refreshPromise
    this._refreshPromise = this._doRefresh()
    try {
      return await this._refreshPromise
    } finally {
      this._refreshPromise = null
    }
  }

  /**
   * Check if token should be proactively refreshed (< 2 min remaining).
   */
  shouldRefresh(): boolean {
    if (!this.payload) return false
    const nowSeconds = Math.floor(Date.now() / 1000)
    return this.payload.exp <= nowSeconds + 120
  }

  /**
   * Check token expiration and clear if expired.
   * Returns true if the token was expired and removed.
   */
  checkExpiration(): boolean {
    if (this.payload && isTokenExpired(this.payload)) {
      this.token = null
      return true
    }
    return false
  }

  private async _doRefresh(): Promise<boolean> {
    try {
      const data = await refreshAccessToken()
      if (!data) return false
      this.token = data.access_token
      return true
    } catch {
      return false
    }
  }
}

export const authStore = new AuthStore()
