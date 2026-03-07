/**
 * Document API calls.
 */

import { api, API_BASE } from './client'
import { authStore } from '$lib/stores/auth.svelte'
import type { DocumentResponse, DocumentStatusResponse, PageSummary } from './types'

export async function listDocuments(projectId: string): Promise<readonly DocumentResponse[]> {
  return api.get<DocumentResponse[]>(`/api/v1/projects/${projectId}/documents`)
}

export async function uploadDocument(projectId: string, file: File): Promise<DocumentResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.upload(`/api/v1/projects/${projectId}/documents`, formData)
  return (await res.json()) as DocumentResponse
}

export async function getDocumentStatus(documentId: string): Promise<DocumentStatusResponse> {
  return api.get<DocumentStatusResponse>(`/api/v1/documents/${documentId}/status`)
}

export async function reExtractDocument(documentId: string): Promise<DocumentStatusResponse> {
  return api.post<DocumentStatusResponse>(`/api/v1/documents/${documentId}/re-extract`)
}

export async function deleteDocument(documentId: string): Promise<void> {
  await api.delete(`/api/v1/documents/${documentId}`)
}

export async function listPages(documentId: string): Promise<readonly PageSummary[]> {
  return api.get<PageSummary[]>(`/api/v1/documents/${documentId}/pages`)
}

export async function exportDocumentZip(projectId: string, documentId: string): Promise<void> {
  const headers: Record<string, string> = {}
  if (authStore.token) {
    headers['Authorization'] = `Bearer ${authStore.token}`
  }

  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/documents/${documentId}/export/zip`,
    {
      credentials: 'include',
      headers,
    },
  )

  if (!res.ok) {
    throw new Error(`Export failed: ${res.status}`)
  }

  const disposition = res.headers.get('Content-Disposition') ?? ''
  const match = disposition.match(/filename="(.+)"/)
  const filename = match?.[1] ?? `${documentId}.zip`

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
