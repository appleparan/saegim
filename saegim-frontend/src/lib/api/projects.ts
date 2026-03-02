/**
 * Project API calls.
 */

import { api } from './client'
import type {
  ProjectResponse,
  CreateProjectRequest,
  AvailableEnginesResponse,
  DefaultEngineUpdate,
  EngineInstanceCreate,
  EngineInstanceUpdate,
  OcrConfigResponse,
  OcrConnectionTestRequest,
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

export async function addEngine(
  projectId: string,
  data: EngineInstanceCreate,
): Promise<OcrConfigResponse> {
  return api.post<OcrConfigResponse>(`/api/v1/projects/${projectId}/ocr-config/engines`, data)
}

export async function updateEngine(
  projectId: string,
  engineId: string,
  data: EngineInstanceUpdate,
): Promise<OcrConfigResponse> {
  return api.put<OcrConfigResponse>(
    `/api/v1/projects/${projectId}/ocr-config/engines/${engineId}`,
    data,
  )
}

export async function deleteEngine(
  projectId: string,
  engineId: string,
): Promise<OcrConfigResponse> {
  return api.delete(
    `/api/v1/projects/${projectId}/ocr-config/engines/${engineId}`,
  ) as Promise<OcrConfigResponse>
}

export async function setDefaultEngine(
  projectId: string,
  data: DefaultEngineUpdate,
): Promise<OcrConfigResponse> {
  return api.put<OcrConfigResponse>(`/api/v1/projects/${projectId}/ocr-config/default-engine`, data)
}

export async function testEngineConnection(
  projectId: string,
  data: OcrConnectionTestRequest,
): Promise<OcrConnectionTestResponse> {
  return api.post<OcrConnectionTestResponse>(`/api/v1/projects/${projectId}/ocr-config/test`, data)
}

export async function getAvailableEngines(projectId: string): Promise<AvailableEnginesResponse> {
  return api.get<AvailableEnginesResponse>(`/api/v1/projects/${projectId}/available-engines`)
}
