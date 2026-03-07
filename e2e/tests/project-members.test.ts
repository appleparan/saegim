import { describe, test, expect, beforeAll } from 'vitest'
import {
  waitForBackendReady,
  register,
  setAuthToken,
  createProject,
  listProjectMembers,
  addProjectMember,
  updateProjectMemberRole,
  removeProjectMember,
} from '../helpers/api'

describe('Project Members', () => {
  let ownerToken: string
  let memberToken: string
  let ownerUserId: string
  let memberUserId: string
  let projectId: string

  const ts = Date.now()
  const ownerEmail = `e2e-owner-${ts}@test.com`
  const memberEmail = `e2e-member-${ts}@test.com`
  const password = 'TestPassword123!'

  beforeAll(async () => {
    await waitForBackendReady()

    // Register owner (first user = admin)
    const ownerRes = await register('E2E Owner', ownerEmail, password)
    expect(ownerRes.status).toBe(201)
    ownerToken = ownerRes.data.access_token

    // Register member (second user = annotator)
    const memberRes = await register('E2E Member', memberEmail, password)
    expect(memberRes.status).toBe(201)
    memberToken = memberRes.data.access_token

    // Decode user IDs from JWT payload
    ownerUserId = decodeJwtSub(ownerToken)
    memberUserId = decodeJwtSub(memberToken)

    // Create project as owner (auto-registers as owner member)
    setAuthToken(ownerToken)
    const projRes = await createProject('E2E Member Test Project', 'Testing project members')
    projectId = projRes.data.id
  })

  test('project creator is auto-registered as owner', async () => {
    setAuthToken(ownerToken)
    const { data, status } = await listProjectMembers(projectId)
    expect(status).toBe(200)
    expect(data).toHaveLength(1)
    expect(data[0].user_id).toBe(ownerUserId)
    expect(data[0].role).toBe('owner')
    expect(data[0].user_name).toBe('E2E Owner')
  })

  test('owner can add a member', async () => {
    setAuthToken(ownerToken)
    const { data, status } = await addProjectMember(projectId, memberUserId, 'annotator')
    expect(status).toBe(201)
    expect(data.user_id).toBe(memberUserId)
    expect(data.role).toBe('annotator')
    expect(data.user_name).toBe('E2E Member')
    expect(data.user_email).toBe(memberEmail)
  })

  test('member list now includes both users', async () => {
    setAuthToken(ownerToken)
    const { data, status } = await listProjectMembers(projectId)
    expect(status).toBe(200)
    expect(data).toHaveLength(2)
    const roles = data.map((m) => m.role).sort()
    expect(roles).toEqual(['annotator', 'owner'])
  })

  test('member can view member list', async () => {
    setAuthToken(memberToken)
    const { data, status } = await listProjectMembers(projectId)
    expect(status).toBe(200)
    expect(data).toHaveLength(2)
  })

  test('non-owner cannot add member (403)', async () => {
    setAuthToken(memberToken)
    const thirdEmail = `e2e-third-${ts}@test.com`
    const thirdRes = await register('E2E Third', thirdEmail, password)
    const thirdId = decodeJwtSub(thirdRes.data.access_token)

    const { status } = await addProjectMember(projectId, thirdId, 'annotator')
    expect(status).toBe(403)
  })

  test('owner can update member role', async () => {
    setAuthToken(ownerToken)
    const { data, status } = await updateProjectMemberRole(projectId, memberUserId, 'reviewer')
    expect(status).toBe(200)
    expect(data.role).toBe('reviewer')
  })

  test('non-owner cannot update role (403)', async () => {
    setAuthToken(memberToken)
    const { status } = await updateProjectMemberRole(projectId, memberUserId, 'annotator')
    expect(status).toBe(403)
  })

  test('duplicate add returns 409', async () => {
    setAuthToken(ownerToken)
    const { status } = await addProjectMember(projectId, memberUserId, 'annotator')
    expect(status).toBe(409)
  })

  test('owner can remove member', async () => {
    setAuthToken(ownerToken)
    const { status } = await removeProjectMember(projectId, memberUserId)
    expect(status).toBe(204)

    // Verify removed
    const { data } = await listProjectMembers(projectId)
    expect(data).toHaveLength(1)
    expect(data[0].user_id).toBe(ownerUserId)
  })

  test('removed member cannot access project (403)', async () => {
    setAuthToken(memberToken)
    const { status } = await listProjectMembers(projectId)
    expect(status).toBe(403)
  })
})

function decodeJwtSub(token: string): string {
  const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString())
  return payload.sub
}
