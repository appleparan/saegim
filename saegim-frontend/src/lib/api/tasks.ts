/**
 * Task and review queue API calls.
 */

import { api } from './client'
import type { TaskResponse, ReviewQueueItem } from './types'

export async function getMyTasks(): Promise<readonly TaskResponse[]> {
  return api.get<TaskResponse[]>('/api/v1/users/me/tasks')
}

export async function getReviewQueue(projectId: string): Promise<readonly ReviewQueueItem[]> {
  return api.get<ReviewQueueItem[]>(`/api/v1/projects/${projectId}/review-queue`)
}
