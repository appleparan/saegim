/**
 * Base HTTP client for communicating with the FastAPI backend.
 * Automatically injects Bearer token when authenticated.
 * On 401, attempts silent refresh before failing.
 * All requests include credentials for HttpOnly cookie support.
 */

import { authStore } from '$lib/stores/auth.svelte'

export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly body?: unknown,
  ) {
    super(`API Error ${status}: ${statusText}`)
    this.name = 'ApiError'
  }
}

export class NetworkError extends Error {
  constructor(
    message: string,
    public readonly cause?: Error,
  ) {
    super(message)
    this.name = 'NetworkError'
  }
}

function authHeaders(): Record<string, string> {
  if (authStore.token) {
    return { Authorization: `Bearer ${authStore.token}` }
  }
  return {}
}

async function doFetch(path: string, options?: RequestInit): Promise<Response> {
  // Proactive refresh: if token expires within 2 min, refresh first
  if (authStore.shouldRefresh()) {
    await authStore.refreshToken()
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options?.headers,
    },
  })
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    let res = await doFetch(path, options)

    // On 401, try silent refresh and retry once
    if (res.status === 401) {
      const refreshed = await authStore.refreshToken()
      if (refreshed) {
        res = await doFetch(path, options)
      }
      if (res.status === 401) {
        authStore.logout()
        const body = await res.json().catch(() => undefined)
        throw new ApiError(res.status, res.statusText, body)
      }
    }

    if (!res.ok) {
      const body = await res.json().catch(() => undefined)
      throw new ApiError(res.status, res.statusText, body)
    }

    if (res.status === 204) {
      return undefined as T
    }

    return (await res.json()) as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new NetworkError(
      'Failed to connect to backend. Is the server running?',
      error instanceof Error ? error : undefined,
    )
  }
}

async function requestRaw(path: string, options?: RequestInit): Promise<Response> {
  try {
    let res = await fetch(`${API_BASE}${path}`, {
      ...options,
      credentials: 'include',
      headers: {
        ...authHeaders(),
        ...options?.headers,
      },
    })

    // On 401, try silent refresh and retry once
    if (res.status === 401) {
      const refreshed = await authStore.refreshToken()
      if (refreshed) {
        res = await fetch(`${API_BASE}${path}`, {
          ...options,
          credentials: 'include',
          headers: {
            ...authHeaders(),
            ...options?.headers,
          },
        })
      }
      if (res.status === 401) {
        authStore.logout()
        const body = await res.json().catch(() => undefined)
        throw new ApiError(res.status, res.statusText, body)
      }
    }

    if (!res.ok) {
      const body = await res.json().catch(() => undefined)
      throw new ApiError(res.status, res.statusText, body)
    }

    return res
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new NetworkError(
      'Failed to connect to backend. Is the server running?',
      error instanceof Error ? error : undefined,
    )
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'DELETE',
      body: body ? JSON.stringify(body) : undefined,
    }),

  /** For multipart uploads (e.g., PDF files). Does NOT set Content-Type. */
  upload: (path: string, formData: FormData) =>
    requestRaw(path, {
      method: 'POST',
      body: formData,
    }),
}
