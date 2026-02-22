import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

async function loadUrlUtils(apiBase: string) {
  vi.doMock('$lib/api/client', () => ({ API_BASE: apiBase }))
  return import('$lib/utils/url')
}

describe('url utils', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('resolves backend asset URL using API origin (ignoring /api/v1 path)', async () => {
    const { resolveBackendAssetUrl } = await loadUrlUtils('http://localhost:5000/api/v1')

    expect(resolveBackendAssetUrl('/storage/pdfs/sample.pdf')).toBe(
      'http://localhost:5000/storage/pdfs/sample.pdf',
    )
  })

  it('keeps absolute asset URLs unchanged', async () => {
    const { resolveBackendAssetUrl } = await loadUrlUtils('http://localhost:5000')

    expect(resolveBackendAssetUrl('https://cdn.example.com/file.pdf')).toBe(
      'https://cdn.example.com/file.pdf',
    )
  })

  it('uses pdf_url when provided', async () => {
    const { resolvePdfUrl } = await loadUrlUtils('http://localhost:5000/api/v1')

    expect(resolvePdfUrl('/storage/pdfs/from-url.pdf', '/tmp/other.pdf')).toBe(
      'http://localhost:5000/storage/pdfs/from-url.pdf',
    )
  })

  it('falls back to pdf_path basename when pdf_url is empty', async () => {
    const { resolvePdfUrl } = await loadUrlUtils('http://localhost:5000/api/v1')

    expect(resolvePdfUrl('', '/var/data/storage/pdfs/from-path.pdf')).toBe(
      'http://localhost:5000/storage/pdfs/from-path.pdf',
    )
  })

  it('returns null when both pdf_url and pdf_path are missing', async () => {
    const { resolvePdfUrl } = await loadUrlUtils('http://localhost:5000')

    expect(resolvePdfUrl('', null)).toBeNull()
  })
})
