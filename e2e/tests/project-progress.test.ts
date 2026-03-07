import { describe, test, expect, beforeAll } from 'vitest'
import {
  waitForBackendReady,
  register,
  setAuthToken,
  createProject,
  uploadPdf,
  listPages,
  addProjectMember,
  assignPage,
  submitPage,
  getProjectProgress,
} from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'

describe('Project Progress', () => {
  let ownerToken: string
  let memberToken: string
  let memberUserId: string
  let projectId: string

  const ts = Date.now()
  const ownerLogin = `e2e-prog-owner-${ts}`
  const memberLogin = `e2e-prog-member-${ts}`
  const password = 'TestPassword123!'

  beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()

    // Register owner
    const ownerRes = await register('Progress Owner', ownerLogin, password)
    expect(ownerRes.status).toBe(201)
    ownerToken = ownerRes.data.access_token

    // Register member
    const memberRes = await register('Progress Member', memberLogin, password)
    expect(memberRes.status).toBe(201)
    memberToken = memberRes.data.access_token
    memberUserId = decodeJwtSub(memberToken)

    // Create project
    setAuthToken(ownerToken)
    const projRes = await createProject('E2E Progress Test', 'Testing progress board')
    projectId = projRes.data.id

    // Add member as annotator
    await addProjectMember(projectId, memberUserId, 'annotator')

    // Upload a test PDF to create pages
    await uploadPdf(projectId, getTestPdfPath())
  })

  test('returns progress for empty project (no workflow actions)', async () => {
    setAuthToken(ownerToken)
    const { data, status } = await getProjectProgress(projectId)

    expect(status).toBe(200)
    expect(data.total_pages).toBeGreaterThan(0)
    expect(data.completion_rate).toBe(0.0)
    expect(data.status_breakdown).toBeDefined()
    expect(data.status_breakdown.pending).toBe(data.total_pages)
    expect(data.status_breakdown.in_progress).toBe(0)
    expect(data.status_breakdown.submitted).toBe(0)
    expect(data.status_breakdown.reviewed).toBe(0)
    expect(data.documents).toHaveLength(1)
    expect(data.members).toHaveLength(2)
  })

  test('documents array contains correct structure', async () => {
    setAuthToken(ownerToken)
    const { data } = await getProjectProgress(projectId)

    const doc = data.documents[0]
    expect(doc.document_id).toBeDefined()
    expect(doc.filename).toMatch(/\.pdf$/)
    expect(doc.total_pages).toBeGreaterThan(0)
    expect(doc.status_counts).toBeDefined()
    expect(doc.completion_rate).toBe(0.0)
  })

  test('members array contains owner and member', async () => {
    setAuthToken(ownerToken)
    const { data } = await getProjectProgress(projectId)

    const roles = data.members.map((m) => m.role).sort()
    expect(roles).toContain('annotator')
    expect(roles).toContain('owner')
  })

  test('progress updates after assign and submit', async () => {
    // Assign a page to the member
    setAuthToken(ownerToken)
    const { data: pages } = await listPages(
      (await getProjectProgress(projectId)).data.documents[0].document_id,
    )
    const pageId = pages[0].id

    await assignPage(pageId, memberUserId)

    // Submit the page as the member
    setAuthToken(memberToken)
    await submitPage(pageId)

    // Check progress reflects the change
    setAuthToken(ownerToken)
    const { data: progress } = await getProjectProgress(projectId)
    expect(progress.status_breakdown.submitted).toBeGreaterThanOrEqual(1)
    expect(progress.status_breakdown.pending).toBeLessThan(progress.total_pages)
  })

  test('member can view progress', async () => {
    setAuthToken(memberToken)
    const { data, status } = await getProjectProgress(projectId)

    expect(status).toBe(200)
    expect(data.total_pages).toBeGreaterThan(0)
  })

  test('unauthenticated request returns 401', async () => {
    setAuthToken(null)
    const { status } = await getProjectProgress(projectId)
    expect(status).toBe(401)
  })

  test('non-member returns 403', async () => {
    const outsiderRes = await register(`e2e-prog-outsider-${ts}`, `e2e-prog-outsider-${ts}`, password)
    setAuthToken(outsiderRes.data.access_token)

    const { status } = await getProjectProgress(projectId)
    expect(status).toBe(403)
  })
})

function decodeJwtSub(token: string): string {
  const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString())
  return payload.sub
}
