import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  takeSnapshot,
  navigateTo,
  clickByPattern,
} from '../../helpers/mcp'
import {
  waitForBackendReady,
  register,
  setAuthToken,
  createProject,
  uploadPdf,
  getDocument,
  getUserIdFromToken,
} from '../../helpers/api'
import { getTestPdfPath } from '../../helpers/pdf'

const ts = Date.now().toString().slice(-6)
const OWNER = {
  loginId: `prog-owner-${ts}`,
  password: 'TestPassword123!',
  name: `Prog Owner ${ts}`,
}

let projectId: string
let ownerToken: string

describe('Browser Project Progress', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Register owner and create project with a document
    const { data: ownerAuth } = await register(OWNER.name, OWNER.loginId, OWNER.password)
    ownerToken = ownerAuth.access_token
    setAuthToken(ownerToken)

    const { data: project } = await createProject(`Progress ${ts}`, 'E2E progress test')
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

    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
  })

  test('progress page shows header and summary cards', async () => {
    await loginAsUser(OWNER.loginId, OWNER.password)
    await navigateTo(`/projects/${projectId}/progress`)
    await waitForText('작업 현황', 20000)
    await waitForText('총 페이지', 20000)
    await waitForText('완료율', 20000)
    await waitForText('검수 대기', 20000)
  }, 60000)

  test('progress page shows status breakdown cards', async () => {
    await loginAsUser(OWNER.loginId, OWNER.password)
    await navigateTo(`/projects/${projectId}/progress`)
    await waitForText('작업 현황', 20000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('대기')
    expect(snapshot).toContain('진행 중')
    expect(snapshot).toContain('제출됨')
    expect(snapshot).toContain('검토 완료')
  }, 60000)

  test('progress page shows documents table', async () => {
    await loginAsUser(OWNER.loginId, OWNER.password)
    await navigateTo(`/projects/${projectId}/progress`)
    await waitForText('문서별 진행 현황', 20000)
    await waitForText('1706.03762v7_4p.pdf', 20000)
  }, 60000)

  test('progress page shows members table', async () => {
    await loginAsUser(OWNER.loginId, OWNER.password)
    await navigateTo(`/projects/${projectId}/progress`)
    await waitForText('멤버별 활동', 20000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain(OWNER.name)
    expect(snapshot).toContain('소유자')
  }, 60000)

  test('project detail page has progress link', async () => {
    await loginAsUser(OWNER.loginId, OWNER.password)
    await navigateTo(`/projects/${projectId}`)
    await waitForText('작업 현황', 20000)
    await clickByPattern(/작업 현황/)
    await waitForText('프로젝트 전체 진행률을 확인합니다', 20000)
  }, 60000)
})
