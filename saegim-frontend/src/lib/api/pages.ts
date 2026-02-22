/**
 * Page/labeling API calls.
 */

import { api } from './client'
import type { PageResponse, SavePageRequest, SavePageAttributesRequest } from './types'

export async function getPage(pageId: string): Promise<PageResponse> {
  return api.get<PageResponse>(`/api/v1/pages/${pageId}`)
}

export async function savePage(pageId: string, data: SavePageRequest): Promise<void> {
  await api.put(`/api/v1/pages/${pageId}`, data)
}

export async function savePageAttributes(
  pageId: string,
  data: SavePageAttributesRequest,
): Promise<void> {
  await api.put(`/api/v1/pages/${pageId}/attributes`, data)
}

export async function acceptExtraction(pageId: string): Promise<PageResponse> {
  return api.post<PageResponse>(`/api/v1/pages/${pageId}/accept-extraction`)
}

/** Request OCR text extraction for a specific region on the page. */
export async function extractElementText(
  pageId: string,
  poly: number[],
): Promise<{ text: string }> {
  return api.post<{ text: string }>(`/api/v1/pages/${pageId}/extract-text`, { poly })
}
