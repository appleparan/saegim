import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'
import { waitForBackendReady } from '../helpers/api'

const FRONTEND_URL = process.env.E2E_FRONTEND_URL ?? 'http://localhost:23000'

let client: Client | null = null

function snapshotText(result: unknown): string {
  if (!result || typeof result !== 'object' || !('content' in result)) return ''
  const content = (result as { content?: Array<{ type?: string; text?: string }> }).content ?? []
  return content.find((item) => item.type === 'text')?.text ?? ''
}

function uidFromSnapshot(text: string, pattern: RegExp): string {
  const line = text.split('\n').find((candidate) => pattern.test(candidate))
  if (!line) {
    throw new Error(`Element not found for pattern: ${pattern}`)
  }

  const match = line.match(/uid=([^\s]+)/)
  if (!match) {
    throw new Error(`UID parse failed for line: ${line}`)
  }
  return match[1]
}

function parseJsonCodeFence(text: string): unknown {
  const match = text.match(/```json\s*([\s\S]*?)\s*```/)
  if (!match) {
    throw new Error(`No JSON code fence in response: ${text}`)
  }
  return JSON.parse(match[1])
}

async function callTool(name: string, args: Record<string, unknown>) {
  if (!client) throw new Error('MCP client is not connected')
  return client.callTool({ name, arguments: args })
}

async function openPage(path: string): Promise<void> {
  await callTool('new_page', {
    url: `${FRONTEND_URL}${path}`,
    isolatedContext: `ctx-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    timeout: 20000,
  })
}

async function takeSnapshot(): Promise<string> {
  const result = await callTool('take_snapshot', {})
  return snapshotText(result)
}

async function fillByPattern(pattern: RegExp, value: string): Promise<void> {
  const uid = uidFromSnapshot(await takeSnapshot(), pattern)
  await callTool('fill', { uid, value })
}

async function clickByPattern(pattern: RegExp): Promise<void> {
  const uid = uidFromSnapshot(await takeSnapshot(), pattern)
  await callTool('click', { uid })
}

async function waitForText(text: string, timeout = 20000): Promise<void> {
  await callTool('wait_for', { text: [text], timeout })
}

async function getCurrentPath(): Promise<string> {
  const result = await callTool('evaluate_script', { function: '() => window.location.pathname' })
  const text = snapshotText(result)
  return parseJsonCodeFence(text) as string
}

async function loginAsAdmin(): Promise<void> {
  await openPage('/login')
  await fillByPattern(/textbox "ID"/, 'admin')
  await fillByPattern(/textbox "비밀번호"/, 'admin')
  await clickByPattern(/button "로그인"/)
  await waitForText('계정 보안 설정', 20000)
}

describe('Browser Auth E2E (chrome-devtools MCP)', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    const transport = new StdioClientTransport({
      command: 'bunx',
      args: ['chrome-devtools-mcp@latest', '--headless', '--isolated', '--no-usage-statistics'],
      stderr: 'ignore',
    })

    client = new Client(
      { name: 'saegim-browser-e2e', version: '0.1.0' },
      { capabilities: {} },
    )

    await client.connect(transport)
  }, 120000)

  afterAll(async () => {
    if (client) {
      await client.close()
      client = null
    }
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

    const result = await callTool('evaluate_script', {
      function: '() => localStorage.getItem("saegim_auth_token")',
    })
    const value = parseJsonCodeFence(snapshotText(result))
    expect(value).toBeNull()
  }, 60000)

  test('page reload restores auth via silent refresh', async () => {
    await loginAsAdmin()
    await expect(getCurrentPath()).resolves.toBe('/account/security')

    // Reload the page — auth should be restored via HttpOnly cookie refresh
    await callTool('navigate_page', { type: 'reload', timeout: 20000 })
    await waitForText('계정 보안 설정', 20000)

    // Should still be on the security page, not redirected to /login
    await expect(getCurrentPath()).resolves.toBe('/account/security')
  }, 60000)
})
