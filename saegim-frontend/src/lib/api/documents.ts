/**
 * Document API calls.
 */

import { api } from './client'
import type {
  DocumentResponse,
  DocumentStatusResponse,
  PageSummary,
} from './types'

export async function listDocuments(
  projectId: string,
): Promise<readonly DocumentResponse[]> {
  return api.get<DocumentResponse[]>(`/api/v1/projects/${projectId}/documents`)
}

export async function uploadDocument(
  projectId: string,
  file: File,
): Promise<DocumentResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.upload(`/api/v1/projects/${projectId}/documents`, formData)
  return (await res.json()) as DocumentResponse
}

export async function getDocumentStatus(
  documentId: string,
): Promise<DocumentStatusResponse> {
  return api.get<DocumentStatusResponse>(
    `/api/v1/documents/${documentId}/status`,
  )
}

export async function listPages(
  documentId: string,
): Promise<readonly PageSummary[]> {
  return api.get<PageSummary[]>(`/api/v1/documents/${documentId}/pages`)
}
