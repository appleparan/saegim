/**
 * Relation API calls.
 */

import { api } from './client'
import type { CreateRelationRequest, PageResponse } from './types'

export async function createRelation(
  pageId: string,
  data: CreateRelationRequest,
): Promise<PageResponse> {
  return api.post<PageResponse>(`/api/v1/pages/${pageId}/relations`, data)
}

export async function deleteRelation(
  pageId: string,
  sourceAnnoId: number,
  targetAnnoId: number,
): Promise<PageResponse> {
  return api.delete<PageResponse>(`/api/v1/pages/${pageId}/relations`, {
    source_anno_id: sourceAnnoId,
    target_anno_id: targetAnnoId,
  })
}
