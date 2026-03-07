import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  clickByPattern,
  fillByPattern,
  takeSnapshot,
  navigateTo,
} from '../../helpers/mcp'
import { waitForBackendReady, register } from '../../helpers/api'

const ts = Date.now().toString().slice(-6)
const ACCT_USER = {
  loginId: `acct-user-${ts}`,
  password: 'TestPassword123!',
  name: `Account User ${ts}`,
}
const CHANGEPW_USER = {
  loginId: `pw-user-${ts}`,
  password: 'TestPassword123!',
  name: `PW User ${ts}`,
}

describe('Browser Account Settings', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    await register(ACCT_USER.name, ACCT_USER.loginId, ACCT_USER.password)
    await register(CHANGEPW_USER.name, CHANGEPW_USER.loginId, CHANGEPW_USER.password)
    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
  })

  test('security page shows all form fields', async () => {
    await loginAsUser(ACCT_USER.loginId, ACCT_USER.password)
    await navigateTo('/account/security')
    await waitForText('계정 보안 설정', 20000)
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('현재 비밀번호')
    expect(snapshot).toContain('새 ID (선택)')
    expect(snapshot).toContain('새 비밀번호 (선택)')
  }, 60000)

  test('submit without changes shows validation error', async () => {
    await loginAsUser(ACCT_USER.loginId, ACCT_USER.password)
    await navigateTo('/account/security')
    await waitForText('계정 보안 설정', 20000)
    await fillByPattern(/textbox "현재 비밀번호"/, ACCT_USER.password)
    await clickByPattern(/button "계정 정보 변경"/)
    await waitForText('변경할 항목', 20000)
  }, 60000)

  test('successful password change redirects to home', async () => {
    const newPassword = `NewPW${ts}!`
    await loginAsUser(CHANGEPW_USER.loginId, CHANGEPW_USER.password)
    await navigateTo('/account/security')
    await waitForText('계정 보안 설정', 20000)

    await fillByPattern(/textbox "현재 비밀번호"/, CHANGEPW_USER.password)
    await fillByPattern(/textbox "새 비밀번호 \(선택\)"/, newPassword)
    await fillByPattern(/textbox "새 비밀번호 확인"/, newPassword)
    await clickByPattern(/button "계정 정보 변경"/)
    await waitForText('계정 정보가 변경되었습니다.', 20000)
  }, 60000)
})
