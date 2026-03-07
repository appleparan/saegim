import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { listAdminUsers, updateAdminUser, listAdminProjects, getAdminStats } from '$lib/api/admin'
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

describe('listAdminUsers', () => {
  it('returns user list on success', async () => {
    const users = [
      {
        id: 'u1',
        name: 'Admin',
        login_id: 'admin',
        email: 'admin@example.com',
        role: 'admin',
        must_change_password: false,
        is_active: true,
        created_at: '2026-03-07T10:00:00Z',
      },
    ]
    mockFetch.mockResolvedValueOnce(jsonResponse(200, users))

    const result = await listAdminUsers()

    expect(result).toEqual(users)
    expect(result[0].is_active).toBe(true)
  })

  it('throws ApiError on 403', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(403, { detail: 'Forbidden' }))

    await expect(listAdminUsers()).rejects.toThrow(ApiError)
  })
})

describe('updateAdminUser', () => {
  it('returns updated user with role change', async () => {
    const updated = {
      id: 'u1',
      name: 'User',
      login_id: 'user1',
      email: 'user@example.com',
      role: 'reviewer',
      must_change_password: false,
      is_active: true,
      created_at: '2026-03-07T10:00:00Z',
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, updated))

    const result = await updateAdminUser('u1', { role: 'reviewer' })

    expect(result.role).toBe('reviewer')
  })

  it('returns updated user with is_active toggle', async () => {
    const updated = {
      id: 'u1',
      name: 'User',
      login_id: 'user1',
      email: 'user@example.com',
      role: 'annotator',
      must_change_password: false,
      is_active: false,
      created_at: '2026-03-07T10:00:00Z',
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, updated))

    const result = await updateAdminUser('u1', { is_active: false })

    expect(result.is_active).toBe(false)
  })

  it('throws ApiError on 404', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse(404, { detail: 'User not found' }))

    await expect(updateAdminUser('unknown', { role: 'admin' })).rejects.toThrow(ApiError)
  })
})

describe('listAdminProjects', () => {
  it('returns enriched project list', async () => {
    const projects = [
      {
        id: 'p1',
        name: 'Project 1',
        description: 'Test',
        member_count: 3,
        total_pages: 10,
        completed_pages: 5,
        submitted_pages: 2,
        created_at: '2026-03-07T10:00:00Z',
      },
    ]
    mockFetch.mockResolvedValueOnce(jsonResponse(200, projects))

    const result = await listAdminProjects()

    expect(result).toEqual(projects)
    expect(result[0].member_count).toBe(3)
    expect(result[0].total_pages).toBe(10)
  })
})

describe('getAdminStats', () => {
  it('returns stats on success', async () => {
    const stats = {
      total_users: 10,
      active_users: 8,
      total_projects: 5,
      total_pages: 100,
      completed_pages: 40,
      submitted_pages: 15,
      completion_rate: 40.0,
    }
    mockFetch.mockResolvedValueOnce(jsonResponse(200, stats))

    const result = await getAdminStats()

    expect(result.total_users).toBe(10)
    expect(result.completion_rate).toBe(40.0)
  })
})
