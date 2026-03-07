import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/svelte'
import ProjectMembersPanel from '$lib/components/settings/ProjectMembersPanel.svelte'
import type { ProjectMemberResponse } from '$lib/api/types'

describe('ProjectMembersPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const sampleMembers: ProjectMemberResponse[] = [
    {
      user_id: 'user-1',
      user_name: 'Alice',
      user_email: 'alice@example.com',
      role: 'owner',
      joined_at: '2024-01-01T00:00:00Z',
    },
    {
      user_id: 'user-2',
      user_name: 'Bob',
      user_email: 'bob@example.com',
      role: 'annotator',
      joined_at: '2024-01-02T00:00:00Z',
    },
    {
      user_id: 'user-3',
      user_name: 'Charlie',
      user_email: 'charlie@example.com',
      role: 'reviewer',
      joined_at: '2024-01-03T00:00:00Z',
    },
  ]

  it('renders empty state when no members', () => {
    render(ProjectMembersPanel, {
      props: { members: [], currentUserId: 'user-1' },
    })

    expect(screen.getByText('멤버가 없습니다.')).toBeTruthy()
  })

  it('renders member list with names and emails', () => {
    render(ProjectMembersPanel, {
      props: { members: sampleMembers, currentUserId: 'user-1' },
    })

    expect(screen.getByText('Alice')).toBeTruthy()
    expect(screen.getByText('alice@example.com')).toBeTruthy()
    expect(screen.getByText('Bob')).toBeTruthy()
    expect(screen.getByText('bob@example.com')).toBeTruthy()
    expect(screen.getByText('Charlie')).toBeTruthy()
    expect(screen.getByText('charlie@example.com')).toBeTruthy()
  })

  it('shows role badges for non-editable view', () => {
    render(ProjectMembersPanel, {
      props: { members: sampleMembers, currentUserId: 'user-4', isOwnerOrAdmin: false },
    })

    expect(screen.getByText('Owner')).toBeTruthy()
    expect(screen.getByText('Annotator')).toBeTruthy()
    expect(screen.getByText('Reviewer')).toBeTruthy()
  })

  it('shows "(나)" label for current user', () => {
    render(ProjectMembersPanel, {
      props: { members: sampleMembers, currentUserId: 'user-1' },
    })

    expect(screen.getByText('(나)')).toBeTruthy()
  })

  it('shows header with title', () => {
    render(ProjectMembersPanel, {
      props: { members: [], currentUserId: 'user-1' },
    })

    expect(screen.getByText('멤버 관리')).toBeTruthy()
  })

  it('shows add member button when owner or admin', () => {
    render(ProjectMembersPanel, {
      props: { members: sampleMembers, currentUserId: 'user-1', isOwnerOrAdmin: true },
    })

    expect(screen.getByText('멤버 추가')).toBeTruthy()
  })

  it('hides add member button when not owner or admin', () => {
    render(ProjectMembersPanel, {
      props: { members: sampleMembers, currentUserId: 'user-2', isOwnerOrAdmin: false },
    })

    expect(screen.queryByText('멤버 추가')).toBeNull()
  })

  it('shows remove button for non-owner members when owner', () => {
    render(ProjectMembersPanel, {
      props: { members: sampleMembers, currentUserId: 'user-1', isOwnerOrAdmin: true },
    })

    // Should show remove buttons for non-owner, non-self members
    const removeButtons = screen.getAllByText('제거')
    expect(removeButtons.length).toBe(2) // Bob and Charlie
  })

  it('does not show remove button for owner member', () => {
    render(ProjectMembersPanel, {
      props: { members: sampleMembers, currentUserId: 'user-4', isOwnerOrAdmin: true },
    })

    // Owner (Alice) should not have a remove button
    // Bob, Charlie should have remove buttons
    const removeButtons = screen.getAllByText('제거')
    expect(removeButtons.length).toBe(2)
  })
})
