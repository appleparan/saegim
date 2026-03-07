import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getMyTasks, getReviewQueue } from '$lib/api/tasks'
import { submitPage, reviewPage } from '$lib/api/pages'
import { ApiError } from '$lib/api/client'

const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch)
})

afterEach(() => {
  vi.restoreAllMocks()
})

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('getMyTasks', () => {
  it('returns task list on success', async () => {
    const tasks = [
      {
        page_id: 'p1',
        page_no: 1,
        document_id: 'd1',
        document_filename: 'report.pdf',
        project_id: 'proj1',
        project_name: 'Test Project',
        status: 'in_progress',
        assigned_at: '2026-03-07T10:00:00Z',
      },
    ]
    mockFetch.mockResolvedValueOnce(jsonResponse(200, tasks))

    const result = await getMyTasks()

    expect(result).toEqual(tasks)
    expect(mockFetch).toHaveBeenCalledOnce()
  })

  it('returns empty array when no tasks', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(200, []))

    const result = await getMyTasks()

    expect(result).toEqual([])
  })
})

describe('getReviewQueue', () => {
  it('returns review queue items on success', async () => {
    const items = [
      {
        page_id: 'p1',
        page_no: 2,
        document_id: 'd1',
        document_filename: 'doc.pdf',
        assigned_to: 'user1',
        assigned_to_name: 'Alice',
        submitted_at: '2026-03-07T11:00:00Z',
      },
    ]
    mockFetch.mockResolvedValueOnce(jsonResponse(200, items))

    const result = await getReviewQueue('project-1')

    expect(result).toEqual(items)
  })

  it('returns empty array when queue is empty', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(200, []))

    const result = await getReviewQueue('project-1')

    expect(result).toEqual([])
  })
})

describe('submitPage', () => {
  it('returns updated page on success', async () => {
    const pageResponse = {
      id: 'p1',
      document_id: 'd1',
      page_no: 1,
      status: 'submitted',
      width: 100,
      height: 200,
      image_url: '/img.png',
      pdf_url: '/doc.pdf',
      annotation_data: {},
      auto_extracted_data: null,
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, pageResponse))

    const result = await submitPage('p1')

    expect(result.status).toBe('submitted')
  })

  it('throws ApiError on 409 (invalid state)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(409, { detail: 'Invalid state' }))

    await expect(submitPage('p1')).rejects.toThrow(ApiError)
  })
})

describe('reviewPage', () => {
  it('returns updated page on approve', async () => {
    const pageResponse = {
      id: 'p1',
      document_id: 'd1',
      page_no: 1,
      status: 'reviewed',
      width: 100,
      height: 200,
      image_url: '/img.png',
      pdf_url: '/doc.pdf',
      annotation_data: {},
      auto_extracted_data: null,
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, pageResponse))

    const result = await reviewPage('p1', { action: 'approved' })

    expect(result.status).toBe('reviewed')
  })

  it('returns updated page on reject with comment', async () => {
    const pageResponse = {
      id: 'p1',
      document_id: 'd1',
      page_no: 1,
      status: 'in_progress',
      width: 100,
      height: 200,
      image_url: '/img.png',
      pdf_url: '/doc.pdf',
      annotation_data: {},
      auto_extracted_data: null,
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, pageResponse))

    const result = await reviewPage('p1', { action: 'rejected', comment: '수정 필요' })

    expect(result.status).toBe('in_progress')
  })

  it('throws ApiError on 409 (not submitted)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(409, { detail: 'Page not submitted' }))

    await expect(reviewPage('p1', { action: 'approved' })).rejects.toThrow(ApiError)
  })

  it('throws ApiError on 403 (not authorized)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(403, { detail: 'Forbidden' }))

    await expect(reviewPage('p1', { action: 'approved' })).rejects.toThrow(ApiError)
  })
})
