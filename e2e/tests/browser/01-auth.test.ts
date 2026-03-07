import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  openPage,
  fillByPattern,
  clickByPattern,
  waitForText,
  getCurrentPath,
  loginAsAdmin,
  registerUser,
  callTool,
  snapshotText,
  parseJsonCodeFence,
  evaluateScript,
} from '../../helpers/mcp'
import { waitForBackendReady } from '../../helpers/api'

describe('Browser Auth Flow', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
  })

  test('default admin login redirects to /account/security', async () => {
    await loginAsAdmin()
    await expect(getCurrentPath()).resolves.toBe('/account/security')
  }, 60000)

  test('register page performs realtime login ID duplicate checks', async () => {
    await openPage('/register')
    await fillByPattern(/textbox "ID"/, 'admin')
    await waitForText('이미 사용 중인 ID입니다.', 20000)

    const uniqueLoginId = `mcp-user-${Date.now().toString().slice(-6)}`
    await fillByPattern(/textbox "ID"/, uniqueLoginId)
    await waitForText('사용 가능한 ID입니다.', 20000)
  }, 60000)

  test('security page performs realtime login ID duplicate checks', async () => {
    await loginAsAdmin()

    await fillByPattern(/textbox "새 ID \(선택\)"/, 'admin')
    await waitForText('이미 사용 중인 ID입니다.', 20000)

    const uniqueLoginId = `admin-${Date.now().toString().slice(-6)}`
    await fillByPattern(/textbox "새 ID \(선택\)"/, uniqueLoginId)
    await waitForText('사용 가능한 ID입니다.', 20000)
  }, 60000)

  test('access token is stored in memory, not localStorage', async () => {
    await loginAsAdmin()

    const value = await evaluateScript<null>(
      '() => localStorage.getItem("saegim_auth_token")',
    )
    expect(value).toBeNull()
  }, 60000)

  test('page reload restores auth via silent refresh', async () => {
    await loginAsAdmin()
    await expect(getCurrentPath()).resolves.toBe('/account/security')

    await callTool('navigate_page', { type: 'reload', timeout: 20000 })
    await waitForText('계정 보안 설정', 20000)

    await expect(getCurrentPath()).resolves.toBe('/account/security')
  }, 60000)

  test('register new user and login succeeds', async () => {
    const ts = Date.now().toString().slice(-6)
    const loginId = `e2e-reg-${ts}`
    const password = 'TestPassword123!'
    await registerUser(`E2E User ${ts}`, loginId, password)
    await waitForText('프로젝트', 30000)
    await expect(getCurrentPath()).resolves.toBe('/')
  }, 60000)

  test('invalid login shows error message', async () => {
    await openPage('/login')
    await fillByPattern(/textbox "ID"/, 'nonexistent-user')
    await fillByPattern(/textbox "비밀번호"/, 'wrong-password')
    await clickByPattern(/button "로그인"/)
    await waitForText('ID 또는 비밀번호가 올바르지 않습니다.', 20000)
  }, 60000)
})
