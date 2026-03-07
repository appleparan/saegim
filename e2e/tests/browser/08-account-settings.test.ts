import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsAdmin,
  waitForText,
  clickByPattern,
  fillByPattern,
  takeSnapshot,
  getCurrentPath,
  openPage,
  loginAs,
} from '../../helpers/mcp'
import { waitForBackendReady, register } from '../../helpers/api'

const ts = Date.now().toString().slice(-6)
const CHANGEPW_USER = {
  loginId: `pw-user-${ts}`,
  password: 'TestPassword123!',
  name: `PW User ${ts}`,
}

describe('Browser Account Settings', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    // Register a user for password change test
    await register(CHANGEPW_USER.name, CHANGEPW_USER.loginId, CHANGEPW_USER.password)
    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
  })

  test('security page shows all form fields', async () => {
    await loginAsAdmin()
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('현재 비밀번호')
    expect(snapshot).toContain('새 ID (선택)')
    expect(snapshot).toContain('새 비밀번호 (선택)')
  }, 60000)

  test('submit without changes shows validation error', async () => {
    await loginAsAdmin()
    await fillByPattern(/textbox "현재 비밀번호"/, 'admin')
    await clickByPattern(/button "계정 정보 변경"/)
    await waitForText('변경할 항목', 20000)
  }, 60000)

  test('successful password change redirects to home', async () => {
    const newPassword = `NewPW${ts}!`
    await loginAs(CHANGEPW_USER.loginId, CHANGEPW_USER.password)
    // Non-admin users with no must_change_password go to / but can navigate to /account/security
    await waitForText('프로젝트', 20000)

    // Navigate to account security
    await openPage('/account/security')
    await waitForText('계정 보안 설정', 20000)

    await fillByPattern(/textbox "현재 비밀번호"/, CHANGEPW_USER.password)
    await fillByPattern(/textbox "새 비밀번호 \(선택\)"/, newPassword)
    await fillByPattern(/textbox "새 비밀번호 확인"/, newPassword)
    await clickByPattern(/button "계정 정보 변경"/)
    await waitForText('계정 정보가 변경되었습니다.', 20000)
  }, 60000)
})
