/**
 * Project API calls.
 */

import { api } from './client'
import type {
  ProjectResponse,
  CreateProjectRequest,
  OcrConfigResponse,
  OcrConfigUpdate,
  OcrConnectionTestResponse,
} from './types'

export async function listProjects(): Promise<readonly ProjectResponse[]> {
  return api.get<ProjectResponse[]>('/api/v1/projects')
}

export async function getProject(id: string): Promise<ProjectResponse> {
  return api.get<ProjectResponse>(`/api/v1/projects/${id}`)
}

export async function createProject(data: CreateProjectRequest): Promise<ProjectResponse> {
  return api.post<ProjectResponse>('/api/v1/projects', data)
}

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`/api/v1/projects/${id}`)
}

export async function getOcrConfig(projectId: string): Promise<OcrConfigResponse> {
  return api.get<OcrConfigResponse>(`/api/v1/projects/${projectId}/ocr-config`)
}

export async function updateOcrConfig(
  projectId: string,
  data: OcrConfigUpdate,
): Promise<OcrConfigResponse> {
  return api.put<OcrConfigResponse>(`/api/v1/projects/${projectId}/ocr-config`, data)
}

export async function testOcrConnection(
  projectId: string,
  data: OcrConfigUpdate,
): Promise<OcrConnectionTestResponse> {
  return api.post<OcrConnectionTestResponse>(
    `/api/v1/projects/${projectId}/ocr-config/test`,
    data,
  )
}
