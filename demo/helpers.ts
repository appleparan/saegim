/**
 * Shared utilities for demo recording scripts.
 *
 * - Pause helpers for paced recording
 * - API helpers for headless data setup (login, project, OCR, upload)
 */

import { type Page } from '@playwright/test'
import { fileURLToPath } from 'node:url'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

// ─── Constants ────────────────────────────────────────────────
const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Load .env file if present (for GEMINI_API_KEY etc.)
const envPath = path.resolve(__dirname, '.env')
if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, 'utf-8').split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const eqIdx = trimmed.indexOf('=')
    if (eqIdx < 0) continue
    const key = trimmed.slice(0, eqIdx)
    const value = trimmed.slice(eqIdx + 1)
    if (!process.env[key]) {
      process.env[key] = value
    }
  }
}

export const SAMPLE_PDF = path.resolve(__dirname, '../e2e/sample_data/1706.03762v7_7p_9p.pdf')
export const API_URL = process.env.API_URL ?? 'http://localhost:15000'
export const AUTH_STATE_PATH = path.resolve(__dirname, '.auth/state.json')

export const PAUSE_SHORT = 800
export const PAUSE_MEDIUM = 1500
export const PAUSE_LONG = 2500
export const PAUSE_EXTRA = 4000

export const PASSWORDS_TO_TRY = ['admin', 'DemoPass2025']
export const NEW_PASSWORD = 'DemoPass2025'

export const DEMO_PROJECT_DESC = '논문 PDF 레이블링 데모'

// ─── UI Helpers ───────────────────────────────────────────────

export async function pause(page: Page, ms: number = PAUSE_MEDIUM): Promise<void> {
  await page.waitForTimeout(ms)
}

// ─── API Helpers ──────────────────────────────────────────────

/** Try known passwords and return working { token, password }. */
export async function apiLogin(): Promise<{ token: string; password: string }> {
  for (const pw of PASSWORDS_TO_TRY) {
    const res = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login_id: 'admin', password: pw }),
    })
    if (res.ok) {
      const data = (await res.json()) as { access_token: string }
      return { token: data.access_token, password: pw }
    }
  }
  throw new Error('Cannot login with any known password.')
}

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

/** Create a project. Returns project ID. */
export async function apiCreateProject(
  token: string,
  name: string,
  description: string = DEMO_PROJECT_DESC,
): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/projects`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ name, description }),
  })
  if (!res.ok) throw new Error(`Failed to create project: ${res.status}`)
  const data = (await res.json()) as { id: string }
  return data.id
}

/** Find an existing project by name. Returns project ID or null. */
export async function apiFindProject(token: string, name: string): Promise<string | null> {
  const res = await fetch(`${API_URL}/api/v1/projects`, {
    headers: authHeaders(token),
  })
  if (!res.ok) return null
  const projects = (await res.json()) as Array<{ id: string; name: string }>
  const found = projects.find((p) => p.name === name)
  return found?.id ?? null
}

/** Ensure a project exists (find or create). Returns project ID. */
export async function apiEnsureProject(
  token: string,
  name: string,
  description: string = DEMO_PROJECT_DESC,
): Promise<string> {
  const existing = await apiFindProject(token, name)
  if (existing) return existing
  return apiCreateProject(token, name, description)
}

/** Add Gemini OCR engine to a project (skips if already configured). */
export async function apiAddOcrEngine(
  token: string,
  projectId: string,
  geminiApiKey?: string,
): Promise<void> {
  // Check if engines already exist
  const configRes = await fetch(`${API_URL}/api/v1/projects/${projectId}/ocr-config`, {
    headers: authHeaders(token),
  })
  if (configRes.ok) {
    const config = (await configRes.json()) as { engines: Record<string, unknown> }
    if (Object.keys(config.engines).length > 0) return
  }

  const apiKey = geminiApiKey ?? process.env.GEMINI_API_KEY ?? ''
  if (!apiKey) {
    throw new Error('GEMINI_API_KEY not set. Add it to demo/.env or set as environment variable.')
  }

  const res = await fetch(`${API_URL}/api/v1/projects/${projectId}/ocr-config/engines`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({
      engine_type: 'commercial_api',
      name: 'Gemini Flash',
      config: {
        provider: 'gemini',
        api_key: apiKey,
        model: 'gemini-3-flash-preview',
      },
    }),
  })
  if (!res.ok) {
    const text = await res.text()
    if (!text.includes('already') && res.status !== 409) {
      throw new Error(`Failed to add OCR engine: ${res.status} ${text}`)
    }
  }
}

/** Upload a PDF document to a project. Returns document ID. */
export async function apiUploadDocument(
  token: string,
  projectId: string,
  filePath: string = SAMPLE_PDF,
): Promise<string> {
  const fileBuffer = readFileSync(filePath)
  const fileName = path.basename(filePath)

  const formData = new FormData()
  formData.append('file', new Blob([fileBuffer], { type: 'application/pdf' }), fileName)

  const res = await fetch(`${API_URL}/api/v1/projects/${projectId}/documents`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })
  if (!res.ok) throw new Error(`Failed to upload document: ${res.status}`)
  const data = (await res.json()) as { id: string }
  return data.id
}

/** Poll document status until 'ready'. */
export async function apiWaitDocumentReady(
  token: string,
  documentId: string,
  timeoutMs: number = 60_000,
): Promise<void> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const res = await fetch(`${API_URL}/api/v1/documents/${documentId}/status`, {
      headers: authHeaders(token),
    })
    if (res.ok) {
      const data = (await res.json()) as { status: string }
      if (data.status === 'ready') return
      if (data.status === 'error') throw new Error('Document processing failed')
    }
    await new Promise((r) => setTimeout(r, 1_000))
  }
  throw new Error('Timed out waiting for document to be ready')
}

/** List pages of a document. */
export async function apiGetPages(
  token: string,
  documentId: string,
): Promise<Array<{ id: string; page_no: number }>> {
  const res = await fetch(`${API_URL}/api/v1/documents/${documentId}/pages`, {
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error(`Failed to get pages: ${res.status}`)
  return (await res.json()) as Array<{ id: string; page_no: number }>
}

/** Find first document in a project. Returns document ID or null. */
export async function apiFindDocument(token: string, projectId: string): Promise<string | null> {
  const res = await fetch(`${API_URL}/api/v1/projects/${projectId}/documents`, {
    headers: authHeaders(token),
  })
  if (!res.ok) return null
  const docs = (await res.json()) as Array<{ id: string }>
  return docs[0]?.id ?? null
}

/**
 * Ensure project has a document uploaded and ready.
 * Returns { projectId, documentId }.
 */
export async function apiEnsureFullSetup(token: string, projectName: string): Promise<{
  projectId: string
  documentId: string
}> {
  const projectId = await apiEnsureProject(token, projectName)
  await apiAddOcrEngine(token, projectId)

  let documentId = await apiFindDocument(token, projectId)
  if (!documentId) {
    documentId = await apiUploadDocument(token, projectId)
    await apiWaitDocumentReady(token, documentId)
  }

  return { projectId, documentId }
}
