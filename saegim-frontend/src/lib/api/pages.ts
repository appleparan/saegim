/**
 * Page/labeling API calls.
 */

import { api } from './client'
import type {
  PageResponse,
  ReviewRequest,
  SavePageAttributesRequest,
  SavePageRequest,
} from './types'

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

/** Force-accept auto-extracted data, overwriting existing annotations. */
export async function forceAcceptExtraction(pageId: string): Promise<PageResponse> {
  return api.post<PageResponse>(`/api/v1/pages/${pageId}/force-accept-extraction`)
}

/** Update reading order of layout elements. */
export async function updateReadingOrder(
  pageId: string,
  orderMap: Record<string, number>,
): Promise<PageResponse> {
  return api.put<PageResponse>(`/api/v1/pages/${pageId}/reading-order`, {
    order_map: orderMap,
  })
}

/** Submit a page for review. Only the assigned user can submit. */
export async function submitPage(pageId: string): Promise<PageResponse> {
  return api.post<PageResponse>(`/api/v1/pages/${pageId}/submit`)
}

/** Review a submitted page (approve or reject). */
export async function reviewPage(
  pageId: string,
  data: ReviewRequest,
): Promise<PageResponse> {
  return api.post<PageResponse>(`/api/v1/pages/${pageId}/review`, data)
}

/** Request OCR text extraction for a specific region on the page. */
export async function extractElementText(
  pageId: string,
  poly: number[],
  engineId?: string,
): Promise<{ text: string }> {
  return api.post<{ text: string }>(`/api/v1/pages/${pageId}/extract-text`, {
    poly,
    ...(engineId ? { engine_id: engineId } : {}),
  })
}
