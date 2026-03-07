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
  deleteProject,
  login,
  getDocument,
} from '../../helpers/api'
import { getTestPdfPath } from '../../helpers/pdf'

const ts = Date.now().toString().slice(-6)
const WORKER = {
  loginId: `task-worker-${ts}`,
  password: 'TestPassword123!',
  name: `Task Worker ${ts}`,
}
const IDLE_USER = {
  loginId: `task-idle-${ts}`,
  password: 'TestPassword123!',
  name: `Task Idle ${ts}`,
}

let projectId: string
let workerToken: string

describe('Browser Task Workflow', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Register worker and idle user
    const { data: workerAuth } = await register(WORKER.name, WORKER.loginId, WORKER.password)
    workerToken = workerAuth.access_token
    setAuthToken(workerToken)

    // Create project and upload PDF
    const { data: project } = await createProject(`Task Flow ${ts}`, 'E2E task test')
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

    // Get pages and assign first page to worker
    const { data: docs } = await listDocuments(projectId)
    const { data: pages } = await listPages(docs[0].id)

    // Need to decode JWT to get user_id
    const payload = JSON.parse(atob(workerToken.split('.')[1]))
    await assignPage(pages[0].id, payload.sub)

    // Register idle user
    await register(IDLE_USER.name, IDLE_USER.loginId, IDLE_USER.password)

    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
    try {
      setAuthToken(workerToken)
      await deleteProject(projectId)
    } catch {
      // cleanup best-effort
    }
  })

  test('tasks page shows assigned task for worker', async () => {
    await loginAsUser(WORKER.loginId, WORKER.password)
    await navigateTo('/tasks')
    await waitForText('내 작업', 20000)
    await waitForText('1706.03762v7_4p.pdf', 20000)
  }, 60000)

  test('filter buttons are present', async () => {
    await loginAsUser(WORKER.loginId, WORKER.password)
    await navigateTo('/tasks')
    await waitForText('내 작업', 20000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('전체')
    expect(snapshot).toContain('진행중')
    expect(snapshot).toContain('제출됨')
  }, 60000)

  test('idle user sees empty task list', async () => {
    await loginAsUser(IDLE_USER.loginId, IDLE_USER.password)
    await navigateTo('/tasks')
    await waitForText('할당된 작업이 없습니다', 20000)
  }, 60000)

  test('task card shows page number', async () => {
    await loginAsUser(WORKER.loginId, WORKER.password)
    await navigateTo('/tasks')
    await waitForText('내 작업', 20000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toMatch(/페이지/)
  }, 60000)
})
