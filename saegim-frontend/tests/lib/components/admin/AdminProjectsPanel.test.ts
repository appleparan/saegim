import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/svelte'
import AdminProjectsPanel from '$lib/components/admin/AdminProjectsPanel.svelte'
import type { AdminProjectResponse } from '$lib/api/types'

describe('AdminProjectsPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const sampleProjects: AdminProjectResponse[] = [
    {
      id: 'p1',
      name: 'Test Project',
      description: 'A test project',
      member_count: 3,
      total_pages: 100,
      completed_pages: 50,
      submitted_pages: 10,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'p2',
      name: 'Empty Project',
      description: '',
      member_count: 0,
      total_pages: 0,
      completed_pages: 0,
      submitted_pages: 0,
      created_at: '2026-02-01T00:00:00Z',
    },
  ]

  it('renders empty state when no projects', () => {
    render(AdminProjectsPanel, {
      props: { projects: [] },
    })

    expect(screen.getByText('등록된 프로젝트가 없습니다.')).toBeTruthy()
  })

  it('renders project list with names', () => {
    render(AdminProjectsPanel, {
      props: { projects: sampleProjects },
    })

    expect(screen.getByText('Test Project')).toBeTruthy()
    expect(screen.getByText('Empty Project')).toBeTruthy()
  })

  it('shows progress percentage', () => {
    render(AdminProjectsPanel, {
      props: { projects: sampleProjects },
    })

    expect(screen.getByText('50%')).toBeTruthy()
    expect(screen.getByText('0%')).toBeTruthy()
  })

  it('renders section heading', () => {
    render(AdminProjectsPanel, {
      props: { projects: sampleProjects },
    })

    expect(screen.getByText('프로젝트 관리')).toBeTruthy()
  })
})
