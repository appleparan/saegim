/**
 * Admin dashboard API calls.
 */

import { api } from './client'
import type {
  AdminUserResponse,
  AdminUserUpdateRequest,
  AdminProjectResponse,
  AdminStatsResponse,
} from './types'

export async function listAdminUsers(): Promise<readonly AdminUserResponse[]> {
  return api.get<AdminUserResponse[]>('/api/v1/admin/users')
}

export async function updateAdminUser(
  userId: string,
  data: AdminUserUpdateRequest,
): Promise<AdminUserResponse> {
  return api.patch<AdminUserResponse>(`/api/v1/admin/users/${userId}`, data)
}

export async function listAdminProjects(): Promise<readonly AdminProjectResponse[]> {
  return api.get<AdminProjectResponse[]>('/api/v1/admin/projects')
}

export async function getAdminStats(): Promise<AdminStatsResponse> {
  return api.get<AdminStatsResponse>('/api/v1/admin/stats')
}
