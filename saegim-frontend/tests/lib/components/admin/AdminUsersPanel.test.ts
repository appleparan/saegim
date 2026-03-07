import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/svelte'
import AdminUsersPanel from '$lib/components/admin/AdminUsersPanel.svelte'
import type { AdminUserResponse } from '$lib/api/types'

describe('AdminUsersPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const sampleUsers: AdminUserResponse[] = [
    {
      id: 'u1',
      name: 'Admin',
      login_id: 'admin',
      email: 'admin@example.com',
      role: 'admin',
      must_change_password: false,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'u2',
      name: 'User',
      login_id: 'user1',
      email: 'user@example.com',
      role: 'annotator',
      must_change_password: false,
      is_active: false,
      created_at: '2026-02-01T00:00:00Z',
    },
  ]

  it('renders empty state when no users', () => {
    render(AdminUsersPanel, {
      props: { users: [] },
    })

    expect(screen.getByText('등록된 사용자가 없습니다.')).toBeTruthy()
  })

  it('renders user list with names and emails', () => {
    render(AdminUsersPanel, {
      props: { users: sampleUsers },
    })

    expect(screen.getByText('Admin')).toBeTruthy()
    expect(screen.getByText('admin@example.com')).toBeTruthy()
    expect(screen.getByText('User')).toBeTruthy()
    expect(screen.getByText('user@example.com')).toBeTruthy()
  })

  it('renders login IDs', () => {
    render(AdminUsersPanel, {
      props: { users: sampleUsers },
    })

    expect(screen.getByText('admin')).toBeTruthy()
    expect(screen.getByText('user1')).toBeTruthy()
  })

  it('renders section heading', () => {
    render(AdminUsersPanel, {
      props: { users: sampleUsers },
    })

    expect(screen.getByText('사용자 관리')).toBeTruthy()
  })
})
