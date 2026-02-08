/**
 * Project API calls.
 */

import { api } from './client'
import type { ProjectResponse, CreateProjectRequest } from './types'

export async function listProjects(): Promise<readonly ProjectResponse[]> {
  return api.get<ProjectResponse[]>('/api/projects')
}

export async function getProject(id: string): Promise<ProjectResponse> {
  return api.get<ProjectResponse>(`/api/projects/${id}`)
}

export async function createProject(data: CreateProjectRequest): Promise<ProjectResponse> {
  return api.post<ProjectResponse>('/api/projects', data)
}
