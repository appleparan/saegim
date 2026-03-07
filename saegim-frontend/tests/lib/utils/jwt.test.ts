import { describe, it, expect, vi, afterEach } from 'vitest'
import { decodeJwtPayload, isTokenExpired, type JwtPayload } from '$lib/utils/jwt'

/** Build a fake JWT with the given payload (no signature verification needed). */
function fakeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = btoa(JSON.stringify(payload))
  return `${header}.${body}.fake-signature`
}

describe('decodeJwtPayload', () => {
  it('decodes a valid JWT payload', () => {
    const token = fakeJwt({
      sub: 'user-123',
      role: 'admin',
      exp: 9999999999,
      must_change_password: true,
    })
    const result = decodeJwtPayload(token)
    expect(result).toEqual({
      sub: 'user-123',
      role: 'admin',
      exp: 9999999999,
      must_change_password: true,
    })
  })

  it('returns null for a token with wrong number of parts', () => {
    expect(decodeJwtPayload('only.two')).toBeNull()
    expect(decodeJwtPayload('single')).toBeNull()
    expect(decodeJwtPayload('')).toBeNull()
  })

  it('returns null for invalid base64', () => {
    expect(decodeJwtPayload('a.!!!invalid!!!.c')).toBeNull()
  })

  it('returns null when required fields are missing', () => {
    expect(decodeJwtPayload(fakeJwt({ sub: 'u1', role: 'admin' }))).toBeNull() // no exp
    expect(decodeJwtPayload(fakeJwt({ sub: 'u1', exp: 123 }))).toBeNull() // no role
    expect(decodeJwtPayload(fakeJwt({ role: 'admin', exp: 123 }))).toBeNull() // no sub
  })

  it('returns null when field types are wrong', () => {
    expect(decodeJwtPayload(fakeJwt({ sub: 123, role: 'admin', exp: 999 }))).toBeNull()
    expect(decodeJwtPayload(fakeJwt({ sub: 'u', role: 'admin', exp: '999' }))).toBeNull()
    expect(
      decodeJwtPayload(
        fakeJwt({ sub: 'u', role: 'admin', exp: 999, must_change_password: 'true' }),
      ),
    ).toBeNull()
  })
})

describe('isTokenExpired', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns false when token expires in the future', () => {
    const futureExp = Math.floor(Date.now() / 1000) + 3600
    const payload: JwtPayload = { sub: 'u', role: 'annotator', exp: futureExp }
    expect(isTokenExpired(payload)).toBe(false)
  })

  it('returns true when token has already expired', () => {
    const pastExp = Math.floor(Date.now() / 1000) - 60
    const payload: JwtPayload = { sub: 'u', role: 'annotator', exp: pastExp }
    expect(isTokenExpired(payload)).toBe(true)
  })

  it('returns true within the 30-second buffer', () => {
    const almostExpired = Math.floor(Date.now() / 1000) + 15 // 15 seconds from now
    const payload: JwtPayload = { sub: 'u', role: 'annotator', exp: almostExpired }
    expect(isTokenExpired(payload)).toBe(true)
  })

  it('returns false just outside the 30-second buffer', () => {
    const justOutside = Math.floor(Date.now() / 1000) + 60 // 60 seconds from now
    const payload: JwtPayload = { sub: 'u', role: 'annotator', exp: justOutside }
    expect(isTokenExpired(payload)).toBe(false)
  })
})
