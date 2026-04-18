import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/svelte'
import AdminStatsPanel from '$lib/components/admin/AdminStatsPanel.svelte'
import type { AdminStatsResponse } from '$lib/api/types'

describe('AdminStatsPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const sampleStats: AdminStatsResponse = {
    total_users: 10,
    active_users: 8,
    total_projects: 5,
    total_pages: 100,
    completed_pages: 40,
    submitted_pages: 15,
    completion_rate: 40.0,
  }

  it('renders all three stat cards', () => {
    render(AdminStatsPanel, {
      props: { stats: sampleStats },
    })

    expect(screen.getByText('Total Users')).toBeTruthy()
    expect(screen.getByText('Total Projects')).toBeTruthy()
    expect(screen.getByText('Overall Completion')).toBeTruthy()
  })

  it('shows correct values', () => {
    render(AdminStatsPanel, {
      props: { stats: sampleStats },
    })

    expect(screen.getByText('10')).toBeTruthy()
    expect(screen.getByText('5')).toBeTruthy()
    expect(screen.getByText('40%')).toBeTruthy()
  })

  it('shows active users count', () => {
    render(AdminStatsPanel, {
      props: { stats: sampleStats },
    })

    expect(screen.getByText('Active users: 8')).toBeTruthy()
  })

  it('shows zero values gracefully', () => {
    const zeroStats: AdminStatsResponse = {
      total_users: 0,
      active_users: 0,
      total_projects: 0,
      total_pages: 0,
      completed_pages: 0,
      submitted_pages: 0,
      completion_rate: 0,
    }
    render(AdminStatsPanel, {
      props: { stats: zeroStats },
    })

    expect(screen.getByText('0%')).toBeTruthy()
    expect(screen.getByText('Active users: 0')).toBeTruthy()
  })
})
