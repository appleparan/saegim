import { describe, it, expect, afterEach, vi } from 'vitest'
import { getDevicePixelRatio } from '$lib/utils/dpr'

describe('getDevicePixelRatio', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns window.devicePixelRatio when available', () => {
    vi.stubGlobal('window', { devicePixelRatio: 2 })
    expect(getDevicePixelRatio()).toBe(2)
  })

  it('returns 1 when devicePixelRatio is 0', () => {
    vi.stubGlobal('window', { devicePixelRatio: 0 })
    expect(getDevicePixelRatio()).toBe(1)
  })

  it('returns 1 when devicePixelRatio is undefined', () => {
    vi.stubGlobal('window', { devicePixelRatio: undefined })
    expect(getDevicePixelRatio()).toBe(1)
  })

  it('returns fractional DPR values', () => {
    vi.stubGlobal('window', { devicePixelRatio: 1.5 })
    expect(getDevicePixelRatio()).toBe(1.5)
  })

  it('returns high DPR values (3x displays)', () => {
    vi.stubGlobal('window', { devicePixelRatio: 3 })
    expect(getDevicePixelRatio()).toBe(3)
  })
})
