import { API_BASE } from '$lib/api/client'

function getApiOrigin(): string {
  try {
    const locationOrigin = globalThis.location?.origin ?? 'http://localhost'
    return new URL(API_BASE, locationOrigin).origin
  } catch {
    return globalThis.location?.origin ?? ''
  }
}

/** Resolve backend-served asset URLs (e.g. /storage/images, /storage/pdfs) to absolute URLs. */
export function resolveBackendAssetUrl(path: string | null | undefined): string {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path

  const origin = getApiOrigin()
  if (!origin) return path

  try {
    return new URL(path, `${origin}/`).toString()
  } catch {
    return path
  }
}

/** Resolve the PDF document URL from API fields, falling back to pdf_path when needed. */
export function resolvePdfUrl(
  pdfUrl: string | null | undefined,
  pdfPath: string | null | undefined,
): string | null {
  if (pdfUrl && pdfUrl.trim().length > 0) {
    return resolveBackendAssetUrl(pdfUrl.trim())
  }

  if (!pdfPath || pdfPath.trim().length === 0) {
    return null
  }

  const normalized = pdfPath.replaceAll('\\', '/')
  const fileName = normalized.split('/').filter(Boolean).at(-1)
  if (!fileName) return null

  return resolveBackendAssetUrl(`/storage/pdfs/${fileName}`)
}
