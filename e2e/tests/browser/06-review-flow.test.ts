import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  clickByPattern,
  takeSnapshot,
  navigateTo,
} from '../../helpers/mcp'
import {
  waitForBackendReady,
  register,
  setAuthToken,
  createProject,
  uploadPdf,
  listDocuments,
  listPages,
  assignPage,
  submitPage,
  deleteProject,
  getDocument,
  getUserIdFromToken,
} from '../../helpers/api'
import { getTestPdfPath } from '../../helpers/pdf'

const ts = Date.now().toString().slice(-6)
const REVIEWER = {
  loginId: `reviewer-${ts}`,
  password: 'TestPassword123!',
  name: `Reviewer ${ts}`,
}

let projectId: string
let reviewerToken: string

describe('Browser Review Flow', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Register reviewer
    const { data: reviewerAuth } = await register(
      REVIEWER.name,
      REVIEWER.loginId,
      REVIEWER.password,
    )
    reviewerToken = reviewerAuth.access_token
    setAuthToken(reviewerToken)

    // Create project and upload multipage PDF
    const { data: project } = await createProject(`Review Flow ${ts}`, 'E2E review test')
    projectId = project.id
    const { data: docData } = await uploadPdf(projectId, getTestPdfPath())

    // Wait for document processing
    let docReady = false
    for (let i = 0; i < 30; i++) {
      const { data: doc } = await getDocument(docData.id)
      if (doc.status === 'ready') {
        docReady = true
        break
      }
      await new Promise((r) => setTimeout(r, 3000))
    }
    if (!docReady) throw new Error('Document processing timed out')

    // Get pages, assign and submit them
    const { data: docs } = await listDocuments(projectId)
    const { data: pages } = await listPages(docs[0].id)
    const userId = getUserIdFromToken(reviewerToken)

    // Submit first 2 pages
    for (const p of pages.slice(0, 2)) {
      await assignPage(p.id, userId)
      await submitPage(p.id)
    }

    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
    try {
      setAuthToken(reviewerToken)
      await deleteProject(projectId)
    } catch {
      // cleanup best-effort
    }
  })

  test('review queue shows submitted items', async () => {
    await loginAsUser(REVIEWER.loginId, REVIEWER.password)
    await navigateTo(`/projects/${projectId}/review`)
    await waitForText('검수 큐', 20000)
    await waitForText('검수 대기 항목', 20000)
  }, 60000)

  test('approve button is visible', async () => {
    await loginAsUser(REVIEWER.loginId, REVIEWER.password)
    await navigateTo(`/projects/${projectId}/review`)
    await waitForText('검수 큐', 20000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('승인')
    expect(snapshot).toContain('반려')
  }, 60000)

  test('approve page shows success message', async () => {
    await loginAsUser(REVIEWER.loginId, REVIEWER.password)
    await navigateTo(`/projects/${projectId}/review`)
    await waitForText('검수 큐', 20000)
    await clickByPattern(/button "승인"/)
    await waitForText('승인 완료', 20000)
  }, 60000)

  test('empty queue shows empty state message', async () => {
    // After approving all items in previous tests, approve remaining
    await loginAsUser(REVIEWER.loginId, REVIEWER.password)
    await navigateTo(`/projects/${projectId}/review`)
    await waitForText('검수 큐', 20000)

    // Approve any remaining items
    const snapshot = await takeSnapshot()
    if (snapshot.includes('승인')) {
      await clickByPattern(/button "승인"/)
      await waitForText('승인 완료', 20000)
    }

    // Reload to see empty state
    await navigateTo(`/projects/${projectId}/review`)
    await waitForText('검수 대기 항목이 없습니다', 20000)
  }, 60000)
})
