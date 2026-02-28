/**
 * Device pixel ratio utilities for HiDPI-aware canvas rendering.
 */

/** Return the current device pixel ratio, defaulting to 1 in SSR. */
export function getDevicePixelRatio(): number {
  return typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1
}
