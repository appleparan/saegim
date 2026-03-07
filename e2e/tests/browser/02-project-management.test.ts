import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  clickByPattern,
  fillByPattern,
  getCurrentPath,
  takeSnapshot,
  handleDialog,
  openPage,
} from '../../helpers/mcp'
import { waitForBackendReady, register, setAuthToken } from '../../helpers/api'

const ts = Date.now().toString().slice(-6)
const TEST_USER = {
  loginId: `proj-user-${ts}`,
  password: 'TestPassword123!',
  name: `Proj User ${ts}`,
}

describe('Browser Project Management', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    const { data } = await register(TEST_USER.name, TEST_USER.loginId, TEST_USER.password)
    setAuthToken(data.access_token)
    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
  })

  test('empty project list shows empty state', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await waitForText('아직 프로젝트가 없습니다', 20000)
  }, 60000)

  test('create project via UI dialog', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await clickByPattern(/button "새 프로젝트"/)
    await waitForText('새 프로젝트 만들기', 10000)
    await fillByPattern(/textbox "프로젝트 이름"/, `MCP Test ${ts}`)
    await clickByPattern(/button "생성"/)
    await waitForText(`MCP Test ${ts}`, 20000)
  }, 60000)

  test('project appears in list after creation', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await waitForText(`MCP Test ${ts}`, 20000)
  }, 60000)

  test('click project navigates to detail page', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await waitForText(`MCP Test ${ts}`, 20000)
    await clickByPattern(new RegExp(`MCP Test ${ts}`))
    await waitForText('아직 문서가 없습니다', 20000)
    const path = await getCurrentPath()
    expect(path).toMatch(/^\/projects\/[a-f0-9-]+$/)
  }, 60000)

  test('delete project via UI with confirm dialog', async () => {
    await loginAsUser(TEST_USER.loginId, TEST_USER.password)
    await waitForText(`MCP Test ${ts}`, 20000)
    await clickByPattern(/button "삭제"/)
    await handleDialog('accept')
    await waitForText('아직 프로젝트가 없습니다', 20000)
  }, 60000)
})
