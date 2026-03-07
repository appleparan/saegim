import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  clickByPattern,
  takeSnapshot,
  getCurrentPath,
  navigateTo,
} from '../../helpers/mcp'
import {
  waitForBackendReady,
  register,
  setAuthToken,
  createProject,
  deleteProject,
} from '../../helpers/api'

const ts = Date.now().toString().slice(-6)
const TEST_USER = {
  loginId: `settings-user-${ts}`,
  password: 'TestPassword123!',
  name: `Settings User ${ts}`,
}
let projectId: string

describe('Browser Project Settings', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    const { data: authData } = await register(
      TEST_USER.name,
      TEST_USER.loginId,
      TEST_USER.password,
    )
    setAuthToken(authData.access_token)
    const { data: project } = await createProject(
      `Settings Flow ${ts}`,
      'E2E settings test',
    )
    projectId = project.id
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

  test('settings page shows OCR tab by default', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await navigateTo(`/projects/${projectId}/settings`)
    await waitForText('프로젝트 설정', 20000)
    await waitForText('OCR 설정', 10000)
  }, 60000)

  test('switch to member management tab', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await navigateTo(`/projects/${projectId}/settings`)
    await waitForText('프로젝트 설정', 20000)
    await clickByPattern(/멤버 관리/)
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain(TEST_USER.name)
  }, 60000)

  test('project name shown in header', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await navigateTo(`/projects/${projectId}/settings`)
    await waitForText(`Settings Flow ${ts}`, 20000)
  }, 60000)

  test('back link navigates to project detail', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await navigateTo(`/projects/${projectId}/settings`)
    await waitForText('프로젝트 설정', 20000)
    await clickByPattern(/문서 목록/)
    const path = await getCurrentPath()
    expect(path).toBe(`/projects/${projectId}`)
  }, 60000)
})
