import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getProjectProgress } from '$lib/api/projects'
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

const sampleProgress = {
  total_pages: 10,
  completion_rate: 40.0,
  status_breakdown: {
    pending: 3,
    in_progress: 2,
    submitted: 1,
    reviewed: 4,
  },
  documents: [
    {
      document_id: 'doc-1',
      filename: 'report.pdf',
      total_pages: 6,
      status_counts: { pending: 2, in_progress: 1, submitted: 1, reviewed: 2 },
      completion_rate: 33.33,
    },
    {
      document_id: 'doc-2',
      filename: 'invoice.pdf',
      total_pages: 4,
      status_counts: { pending: 1, in_progress: 1, submitted: 0, reviewed: 2 },
      completion_rate: 50.0,
    },
  ],
  members: [
    {
      user_id: 'user-1',
      user_name: 'Alice',
      role: 'annotator',
      assigned_pages: 5,
      in_progress_pages: 2,
      submitted_pages: 1,
      reviewed_pages: 2,
    },
    {
      user_id: 'user-2',
      user_name: 'Bob',
      role: 'reviewer',
      assigned_pages: 0,
      in_progress_pages: 0,
      submitted_pages: 0,
      reviewed_pages: 2,
    },
  ],
}

describe('getProjectProgress', () => {
  it('returns full progress data on success', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(200, sampleProgress))

    const result = await getProjectProgress('project-1')

    expect(result.total_pages).toBe(10)
    expect(result.completion_rate).toBe(40.0)
    expect(result.status_breakdown.reviewed).toBe(4)
    expect(result.documents).toHaveLength(2)
    expect(result.documents[0].filename).toBe('report.pdf')
    expect(result.members).toHaveLength(2)
    expect(result.members[0].user_name).toBe('Alice')
    expect(mockFetch).toHaveBeenCalledOnce()
  })

  it('returns empty progress for project with no data', async () => {
    const emptyProgress = {
      total_pages: 0,
      completion_rate: 0.0,
      status_breakdown: { pending: 0, in_progress: 0, submitted: 0, reviewed: 0 },
      documents: [],
      members: [],
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, emptyProgress))

    const result = await getProjectProgress('project-1')

    expect(result.total_pages).toBe(0)
    expect(result.completion_rate).toBe(0.0)
    expect(result.documents).toEqual([])
    expect(result.members).toEqual([])
  })

  it('throws ApiError on 403 (not a member)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(403, { detail: 'Not a project member' }))

    await expect(getProjectProgress('project-1')).rejects.toThrow(ApiError)
  })

  it('throws ApiError on 401 (unauthenticated)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(401, { detail: 'Not authenticated' }))

    await expect(getProjectProgress('project-1')).rejects.toThrow(ApiError)
  })
})
