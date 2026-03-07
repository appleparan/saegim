import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  clickByPattern,
  takeSnapshot,
  waitForAnyText,
} from '../../helpers/mcp'
import {
  waitForBackendReady,
  register,
  setAuthToken,
  createProject,
  uploadPdf,
  deleteProject,
} from '../../helpers/api'
import { getTestPdfPath } from '../../helpers/pdf'

const ts = Date.now().toString().slice(-6)
const TEST_USER = {
  loginId: `doc-user-${ts}`,
  password: 'TestPassword123!',
  name: `Doc User ${ts}`,
}
let projectId: string

describe('Browser Document Flow', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    const { data: authData } = await register(
      TEST_USER.name,
      TEST_USER.loginId,
      TEST_USER.password,
    )
    setAuthToken(authData.access_token)
    const { data: project } = await createProject(`Doc Flow ${ts}`, 'E2E document flow test')
    projectId = project.id
    await uploadPdf(projectId, getTestPdfPath())
    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
    try {
      await deleteProject(projectId)
    } catch {
      // cleanup best-effort
    }
  })

  test('project detail page shows uploaded document', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await clickByPattern(new RegExp(`Doc Flow ${ts}`))
    await waitForText('1706.03762v7_4p.pdf', 20000)
  }, 60000)

  test('document status badge is visible', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await clickByPattern(new RegExp(`Doc Flow ${ts}`))
    await waitForAnyText(['처리 중', '준비됨'], 30000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toMatch(/처리 중|준비됨/)
  }, 60000)

  test('project detail shows navigation links', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await clickByPattern(new RegExp(`Doc Flow ${ts}`))
    await waitForText('1706.03762v7_4p.pdf', 20000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('검수 큐')
    expect(snapshot).toContain('프로젝트 목록')
  }, 60000)

  test('expand document shows page list after processing', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await clickByPattern(new RegExp(`Doc Flow ${ts}`))

    // Wait for document processing to complete
    let attempts = 0
    while (attempts < 30) {
      const snap = await takeSnapshot()
      if (snap.includes('준비됨')) break
      await new Promise((r) => setTimeout(r, 3000))
      attempts++
    }

    // Click document row to expand page list
    await clickByPattern(/1706\.03762v7_4p\.pdf/)
    await waitForAnyText(['대기', '진행 중', '완료'], 20000)
  }, 120000)
})
