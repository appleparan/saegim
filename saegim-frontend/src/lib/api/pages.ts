/**
 * Page/labeling API calls.
 */

import { api } from './client'
import type {
  PageResponse,
  SavePageRequest,
  SavePageAttributesRequest,
} from './types'

export async function getPage(pageId: string): Promise<PageResponse> {
  return api.get<PageResponse>(`/api/pages/${pageId}`)
}

export async function savePage(
  pageId: string,
  data: SavePageRequest,
): Promise<void> {
  await api.put(`/api/pages/${pageId}`, data)
}

export async function savePageAttributes(
  pageId: string,
  data: SavePageAttributesRequest,
): Promise<void> {
  await api.put(`/api/pages/${pageId}/attributes`, data)
}
