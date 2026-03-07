import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  clickByPattern,
  takeSnapshot,
  navigateTo,
  getCurrentPath,
} from '../../helpers/mcp'
import {
  waitForBackendReady,
  register,
  setAuthToken,
  login,
  updateMyCredentials,
} from '../../helpers/api'

const ts = Date.now().toString().slice(-6)
const NORMAL_USER = {
  loginId: `normal-${ts}`,
  password: 'TestPassword123!',
  name: `Normal User ${ts}`,
}

// Track admin credential changes
let adminLoginId = 'admin'
let adminPassword = 'admin'
const newAdminPassword = `AdminNew${ts}!`

async function openAdminDashboard(): Promise<void> {
  await loginAsUser(adminLoginId, adminPassword)
  await navigateTo('/admin')
  await waitForText('관리자 대시보드', 20000)
}

describe('Browser Admin Dashboard', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Register a normal user for non-admin test
    await register(NORMAL_USER.name, NORMAL_USER.loginId, NORMAL_USER.password)

    // Login as admin and change password via API to bypass must_change_password
    const { data: adminAuth, status: loginStatus } = await login(adminLoginId, adminPassword)
    if (loginStatus !== 200 || !adminAuth.access_token) {
      throw new Error('Admin login failed in test setup. Rebuild E2E stack for a fresh state.')
    }
    setAuthToken(adminAuth.access_token)
    const { data: updatedAuth, status: updateStatus } = await updateMyCredentials(adminPassword, {
      new_password: newAdminPassword,
    })
    if (updateStatus !== 200 || !updatedAuth.access_token) {
      throw new Error('Admin password update failed in test setup.')
    }
    setAuthToken(updatedAuth.access_token)
    adminPassword = newAdminPassword

    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
  })

  test('admin can access admin dashboard', async () => {
    await openAdminDashboard()
  }, 60000)

  test('user management tab shows users', async () => {
    await openAdminDashboard()
    await waitForText('사용자 관리', 10000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain(NORMAL_USER.name)
  }, 60000)

  test('tab switching between management panels', async () => {
    await openAdminDashboard()

    // Switch to project management
    await clickByPattern(/프로젝트 관리/)
    const snap1 = await takeSnapshot()
    expect(snap1).toContain('프로젝트 관리')

    // Switch to system stats
    await clickByPattern(/시스템 현황/)
    const snap2 = await takeSnapshot()
    expect(snap2).toContain('시스템 현황')
  }, 60000)

  test('non-admin user is redirected from admin page', async () => {
    await loginAsUser(NORMAL_USER.loginId, NORMAL_USER.password)
    await navigateTo('/admin')
    // Non-admin should be redirected to home
    const path = await getCurrentPath()
    expect(path).toBe('/')
  }, 60000)
})
