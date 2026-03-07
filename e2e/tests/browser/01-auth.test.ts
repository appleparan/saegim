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
  loginAsUser,
  registerUser,
  reloadPage,
  evaluateScript,
  navigateTo,
} from '../../helpers/mcp'
import { waitForBackendReady, login, register, setAuthToken } from '../../helpers/api'

const ts = Date.now().toString().slice(-6)
const TEST_USER = {
  loginId: `auth-user-${ts}`,
  password: 'TestPassword123!',
  name: `Auth User ${ts}`,
}

// Track whether default admin credentials work (fresh DB)
let adminAvailable = false

describe('Browser Auth Flow', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Check if admin has default credentials (fresh DB)
    try {
      const { status } = await login('admin', 'admin')
      adminAvailable = status === 200
    } catch {
      adminAvailable = false
    }
    setAuthToken(null)

    // Register a test user for non-admin tests
    await register(TEST_USER.name, TEST_USER.loginId, TEST_USER.password)

    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
  })

  test('default admin login redirects to /account/security', async (ctx) => {
    if (!adminAvailable) {
      ctx.skip()
      return
    }
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
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await navigateTo('/account/security')
    await waitForText('계정 보안 설정', 20000)

    await fillByPattern(/textbox "새 ID \(선택\)"/, 'admin')
    await waitForText('이미 사용 중인 ID입니다.', 20000)

    const uniqueLoginId = `admin-${Date.now().toString().slice(-6)}`
    await fillByPattern(/textbox "새 ID \(선택\)"/, uniqueLoginId)
    await waitForText('사용 가능한 ID입니다.', 20000)
  }, 60000)

  test('access token is stored in memory, not localStorage', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)

    const value = await evaluateScript<null>(
      '() => localStorage.getItem("saegim_auth_token")',
    )
    expect(value).toBeNull()
  }, 60000)

  test('page reload restores auth via silent refresh', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await navigateTo('/account/security')
    await waitForText('계정 보안 설정', 20000)
    await expect(getCurrentPath()).resolves.toBe('/account/security')

    await reloadPage()
    await waitForText('계정 보안 설정', 20000)

    await expect(getCurrentPath()).resolves.toBe('/account/security')
  }, 60000)

  test('register new user and login succeeds', async () => {
    const regTs = Date.now().toString().slice(-6)
    const loginId = `e2e-reg-${regTs}`
    const password = 'TestPassword123!'
    await registerUser(`E2E User ${regTs}`, loginId, password)
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
