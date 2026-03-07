import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'

const FRONTEND_URL = process.env.E2E_FRONTEND_URL ?? 'http://localhost:23000'

let client: Client | null = null

// --- Client lifecycle ---

export async function connectMcp(): Promise<void> {
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
}

export async function disconnectMcp(): Promise<void> {
  if (client) {
    await client.close()
    client = null
  }
}

export function getClient(): Client {
  if (!client) throw new Error('MCP client is not connected')
  return client
}

// --- Low-level tools ---

export async function callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
  return getClient().callTool({ name, arguments: args })
}

export function snapshotText(result: unknown): string {
  if (!result || typeof result !== 'object' || !('content' in result)) return ''
  const content = (result as { content?: Array<{ type?: string; text?: string }> }).content ?? []
  return content.find((item) => item.type === 'text')?.text ?? ''
}

export function uidFromSnapshot(text: string, pattern: RegExp): string {
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

export function parseJsonCodeFence(text: string): unknown {
  const match = text.match(/```json\s*([\s\S]*?)\s*```/)
  if (!match) {
    throw new Error(`No JSON code fence in response: ${text}`)
  }
  return JSON.parse(match[1])
}

// --- High-level browser actions ---

export function generateContextId(): string {
  return `ctx-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export async function openPage(path: string, contextId?: string): Promise<void> {
  await callTool('new_page', {
    url: `${FRONTEND_URL}${path}`,
    isolatedContext: contextId ?? generateContextId(),
    timeout: 20000,
  })
}

export async function navigateTo(path: string): Promise<void> {
  await callTool('navigate_page', {
    type: 'url',
    url: `${FRONTEND_URL}${path}`,
    timeout: 20000,
  })
}

export async function reloadPage(): Promise<void> {
  await callTool('navigate_page', { type: 'reload', timeout: 20000 })
}

export async function takeSnapshot(): Promise<string> {
  const result = await callTool('take_snapshot', {})
  return snapshotText(result)
}

export async function fillByPattern(pattern: RegExp, value: string): Promise<void> {
  const uid = uidFromSnapshot(await takeSnapshot(), pattern)
  await callTool('fill', { uid, value })
}

export async function clickByPattern(pattern: RegExp): Promise<void> {
  const uid = uidFromSnapshot(await takeSnapshot(), pattern)
  await callTool('click', { uid })
}

export async function waitForText(text: string, timeout = 20000): Promise<void> {
  await callTool('wait_for', { text: [text], timeout })
}

export async function waitForAnyText(texts: string[], timeout = 20000): Promise<void> {
  await callTool('wait_for', { text: texts, timeout })
}

export async function getCurrentPath(): Promise<string> {
  const result = await callTool('evaluate_script', {
    function: '() => window.location.pathname',
  })
  return parseJsonCodeFence(snapshotText(result)) as string
}

export async function evaluateScript<T>(fn: string): Promise<T> {
  const result = await callTool('evaluate_script', { function: fn })
  return parseJsonCodeFence(snapshotText(result)) as T
}

export async function handleDialog(action: 'accept' | 'dismiss'): Promise<void> {
  await callTool('handle_dialog', { action })
}

export async function pressKey(key: string): Promise<void> {
  await callTool('press_key', { key })
}

// --- Common flows ---

export async function loginAs(
  loginId: string,
  password: string,
  contextId?: string,
): Promise<void> {
  await openPage('/login', contextId)
  await fillByPattern(/textbox "ID"/, loginId)
  await fillByPattern(/textbox "비밀번호"/, password)
  await clickByPattern(/button "로그인"/)
}

export async function loginAsAdmin(contextId?: string): Promise<void> {
  await loginAs('admin', 'admin', contextId)
  // Default admin has must_change_password, redirects to /account/security
  await waitForText('계정 보안 설정', 20000)
}

export async function loginAsUser(
  loginId: string,
  password: string,
  contextId?: string,
): Promise<void> {
  await loginAs(loginId, password, contextId)
  // Normal users redirect to project list
  await waitForText('프로젝트', 20000)
}

export async function registerUser(
  name: string,
  loginId: string,
  password: string,
  contextId?: string,
): Promise<void> {
  await openPage('/register', contextId)
  await fillByPattern(/textbox "이름"/, name)
  await fillByPattern(/textbox "ID"/, loginId)
  await fillByPattern(/textbox "비밀번호"/, password)
  await fillByPattern(/textbox "비밀번호 확인"/, password)
  await clickByPattern(/button "회원가입"/)
}

// --- Assertions ---

export async function expectPath(expected: string): Promise<void> {
  const actual = await getCurrentPath()
  if (actual !== expected) {
    throw new Error(`Expected path ${expected}, got ${actual}`)
  }
}

export async function snapshotContains(text: string): Promise<boolean> {
  const snapshot = await takeSnapshot()
  return snapshot.includes(text)
}
