/**
 * Relation API calls.
 */

import { api } from './client'
import type { CreateRelationRequest, RelationResponse } from './types'

export async function createRelation(
  pageId: string,
  data: CreateRelationRequest,
): Promise<RelationResponse> {
  return api.post<RelationResponse>(`/api/pages/${pageId}/relations`, data)
}

export async function deleteRelation(relationId: string): Promise<void> {
  await api.delete(`/api/relations/${relationId}`)
}
