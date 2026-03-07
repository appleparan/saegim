/**
 * JWT payload parsing utilities.
 * No verification — that's the server's job.
 */

export interface JwtPayload {
  readonly sub: string
  readonly role: 'admin' | 'annotator' | 'reviewer'
  readonly exp: number
}

/**
 * Decode a JWT token's payload without verification.
 * Returns null if the token is malformed.
 */
export function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(atob(parts[1])) as Record<string, unknown>
    if (
      typeof payload.sub !== 'string' ||
      typeof payload.role !== 'string' ||
      typeof payload.exp !== 'number'
    ) {
      return null
    }
    return payload as unknown as JwtPayload
  } catch {
    return null
  }
}

/**
 * Check if a JWT token has expired.
 * Includes a 30-second buffer to prevent edge-case failures.
 */
export function isTokenExpired(payload: JwtPayload): boolean {
  const nowSeconds = Math.floor(Date.now() / 1000)
  return payload.exp <= nowSeconds + 30
}
