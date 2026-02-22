/**
 * Base HTTP client for communicating with the FastAPI backend.
 */

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

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

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
    const res = await fetch(`${API_BASE}${path}`, options)

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

  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

  /** For multipart uploads (e.g., PDF files). Does NOT set Content-Type. */
  upload: (path: string, formData: FormData) =>
    requestRaw(path, {
      method: 'POST',
      body: formData,
    }),
}
