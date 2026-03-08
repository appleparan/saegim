/**
 * Element CRUD API calls.
 */

import { api } from './client'
import type { CreateElementRequest, ElementResponse } from './types'

export async function createElement(
  pageId: string,
  data: CreateElementRequest,
): Promise<ElementResponse> {
  return api.post<ElementResponse>(`/api/v1/pages/${pageId}/elements`, data)
}
