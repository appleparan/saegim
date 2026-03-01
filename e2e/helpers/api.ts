import { readFileSync } from 'node:fs'

const BASE_URL = process.env.E2E_BACKEND_URL ?? 'http://localhost:25000'
const API_URL = `${BASE_URL}/api/v1`
const TIMEOUT = 60_000

interface ProjectResponse {
  id: string
  name: string
  description: string
  created_at: string
}

interface DocumentUploadResponse {
  id: string
  filename: string
  total_pages: number
  status: string
  message: string
}

interface DocumentResponse {
  id: string
  project_id: string
  filename: string
  pdf_path: string
  total_pages: number
  status: string
  created_at: string
}

interface PageListResponse {
  id: string
  page_no: number
  width: number
  height: number
  status: string
  assigned_to: string | null
  updated_at: string
}

interface PageResponse {
  id: string
  document_id: string
  page_no: number
  width: number
  height: number
  image_path: string
  annotation_data: Record<string, unknown>
  auto_extracted_data: Record<string, unknown> | null
  status: string
  assigned_to: string | null
  updated_at: string
}

interface ExportResponse {
  project_name: string
  total_pages: number
  data: Record<string, unknown>[]
}

interface OcrConfigResponse {
  engine_type: 'commercial_api' | 'vllm' | 'split_pipeline' | 'pdfminer'
  commercial_api?: { provider: string; api_key?: string; model: string } | null
  vllm?: { host: string; port: number; model?: string } | null
  split_pipeline?: {
    docling_model_name: string
    ocr_provider: string
    ocr_api_key?: string
    ocr_host?: string
    ocr_port?: number
    ocr_model?: string
  } | null
  env_gemini_api_key?: string
}

interface OcrConnectionTestResponse {
  success: boolean
  message: string
}

async function request<T>(
  method: string,
  path: string,
  options?: { body?: unknown; formData?: FormData },
): Promise<{ data: T; status: number; duration: number }> {
  const url = `${API_URL}${path}`
  const start = performance.now()

  const init: RequestInit = {
    method,
    signal: AbortSignal.timeout(TIMEOUT),
  }

  if (options?.formData) {
    init.body = options.formData
  } else if (options?.body) {
    init.headers = { 'Content-Type': 'application/json' }
    init.body = JSON.stringify(options.body)
  }

  const response = await fetch(url, init)
  const duration = performance.now() - start

  if (response.status === 204) {
    return { data: undefined as T, status: response.status, duration }
  }

  const data = (await response.json()) as T
  return { data, status: response.status, duration }
}

export async function healthCheck(): Promise<{ status: number; duration: number }> {
  const { status, duration } = await request<unknown>('GET', '/health')
  return { status, duration }
}

export async function createProject(
  name: string,
  description = '',
): Promise<{ data: ProjectResponse; duration: number }> {
  const { data, duration } = await request<ProjectResponse>('POST', '/projects', {
    body: { name, description },
  })
  return { data, duration }
}

export async function getProject(
  id: string,
): Promise<{ data: ProjectResponse; duration: number }> {
  const { data, duration } = await request<ProjectResponse>('GET', `/projects/${id}`)
  return { data, duration }
}

export async function listProjects(): Promise<{
  data: ProjectResponse[]
  duration: number
}> {
  const { data, duration } = await request<ProjectResponse[]>('GET', '/projects')
  return { data, duration }
}

export async function deleteProject(id: string): Promise<{ duration: number }> {
  const { duration } = await request<void>('DELETE', `/projects/${id}`)
  return { duration }
}

export async function uploadPdf(
  projectId: string,
  pdfPath: string,
): Promise<{ data: DocumentUploadResponse; duration: number }> {
  const fileBuffer = readFileSync(pdfPath)
  const blob = new Blob([fileBuffer], { type: 'application/pdf' })
  const filename = pdfPath.split('/').pop() ?? 'test.pdf'

  const formData = new FormData()
  formData.append('file', blob, filename)

  const { data, duration } = await request<DocumentUploadResponse>(
    'POST',
    `/projects/${projectId}/documents`,
    { formData },
  )
  return { data, duration }
}

export async function getDocument(
  id: string,
): Promise<{ data: DocumentResponse; duration: number }> {
  const { data, duration } = await request<DocumentResponse>('GET', `/documents/${id}`)
  return { data, duration }
}

export async function listDocuments(
  projectId: string,
): Promise<{ data: DocumentResponse[]; duration: number }> {
  const { data, duration } = await request<DocumentResponse[]>(
    'GET',
    `/projects/${projectId}/documents`,
  )
  return { data, duration }
}

export async function deleteDocument(id: string): Promise<{ duration: number }> {
  const { duration } = await request<void>('DELETE', `/documents/${id}`)
  return { duration }
}

export async function listPages(
  documentId: string,
): Promise<{ data: PageListResponse[]; duration: number }> {
  const { data, duration } = await request<PageListResponse[]>(
    'GET',
    `/documents/${documentId}/pages`,
  )
  return { data, duration }
}

export async function getPage(id: string): Promise<{ data: PageResponse; duration: number }> {
  const { data, duration } = await request<PageResponse>('GET', `/pages/${id}`)
  return { data, duration }
}

export async function updateAnnotation(
  pageId: string,
  annotationData: Record<string, unknown>,
): Promise<{ data: PageResponse; duration: number }> {
  const { data, duration } = await request<PageResponse>('PUT', `/pages/${pageId}`, {
    body: { annotation_data: annotationData },
  })
  return { data, duration }
}

export async function updatePageAttributes(
  pageId: string,
  pageAttribute: Record<string, unknown>,
): Promise<{ data: PageResponse; duration: number }> {
  const { data, duration } = await request<PageResponse>('PUT', `/pages/${pageId}/attributes`, {
    body: { page_attribute: pageAttribute },
  })
  return { data, duration }
}

export async function addElement(
  pageId: string,
  element: {
    category_type: string
    poly: number[]
    text?: string
    ignore?: boolean
  },
): Promise<{ data: PageResponse; duration: number }> {
  const { data, duration } = await request<PageResponse>('POST', `/pages/${pageId}/elements`, {
    body: element,
  })
  return { data, duration }
}

export async function deleteElement(
  pageId: string,
  annoId: number,
): Promise<{ data: PageResponse; duration: number }> {
  const { data, duration } = await request<PageResponse>(
    'DELETE',
    `/pages/${pageId}/elements/${annoId}`,
  )
  return { data, duration }
}

export async function addRelation(
  pageId: string,
  sourceAnnoId: number,
  targetAnnoId: number,
  relationType: string,
): Promise<{ data: PageResponse; status: number; duration: number }> {
  return request<PageResponse>('POST', `/pages/${pageId}/relations`, {
    body: { source_anno_id: sourceAnnoId, target_anno_id: targetAnnoId, relation_type: relationType },
  })
}

export async function deleteRelation(
  pageId: string,
  sourceAnnoId: number,
  targetAnnoId: number,
): Promise<{ data: PageResponse; status: number; duration: number }> {
  return request<PageResponse>('DELETE', `/pages/${pageId}/relations`, {
    body: { source_anno_id: sourceAnnoId, target_anno_id: targetAnnoId },
  })
}

export async function updateReadingOrder(
  pageId: string,
  orderMap: Record<string, number>,
): Promise<{ data: PageResponse; status: number; duration: number }> {
  return request<PageResponse>('PUT', `/pages/${pageId}/reading-order`, {
    body: { order_map: orderMap },
  })
}

export async function acceptExtraction(
  pageId: string,
): Promise<{ data: PageResponse; duration: number }> {
  const { data, duration } = await request<PageResponse>(
    'POST',
    `/pages/${pageId}/accept-extraction`,
  )
  return { data, duration }
}

export async function forceAcceptExtraction(
  pageId: string,
): Promise<{ data: PageResponse; status: number; duration: number }> {
  return request<PageResponse>('POST', `/pages/${pageId}/force-accept-extraction`)
}

interface DocumentStatusResponse {
  id: string
  status: string
  total_pages: number
  processed_pages: number
}

export async function getDocumentStatus(
  documentId: string,
): Promise<{ data: DocumentStatusResponse; status: number; duration: number }> {
  return request<DocumentStatusResponse>('GET', `/documents/${documentId}/status`)
}

export async function reExtractDocument(
  documentId: string,
): Promise<{ data: DocumentStatusResponse; status: number; duration: number }> {
  return request<DocumentStatusResponse>('POST', `/documents/${documentId}/re-extract`)
}

export async function exportProject(
  projectId: string,
): Promise<{ data: ExportResponse; duration: number }> {
  const { data, duration } = await request<ExportResponse>(
    'POST',
    `/projects/${projectId}/export`,
  )
  return { data, duration }
}

export async function getOcrConfig(
  projectId: string,
): Promise<{ data: OcrConfigResponse; status: number; duration: number }> {
  return request<OcrConfigResponse>('GET', `/projects/${projectId}/ocr-config`)
}

export async function updateOcrConfig(
  projectId: string,
  config: Record<string, unknown>,
): Promise<{ data: OcrConfigResponse; status: number; duration: number }> {
  return request<OcrConfigResponse>('PUT', `/projects/${projectId}/ocr-config`, {
    body: config,
  })
}

export async function testOcrConnection(
  projectId: string,
  config: Record<string, unknown>,
): Promise<{ data: OcrConnectionTestResponse; status: number; duration: number }> {
  return request<OcrConnectionTestResponse>('POST', `/projects/${projectId}/ocr-config/test`, {
    body: config,
  })
}

export async function waitForBackendReady(
  maxWaitMs = 60_000,
  intervalMs = 2_000,
): Promise<void> {
  const deadline = Date.now() + maxWaitMs
  while (Date.now() < deadline) {
    try {
      const { status } = await healthCheck()
      if (status === 200) return
    } catch {
      // backend not ready yet
    }
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error(`Backend not ready after ${maxWaitMs}ms`)
}

const VLLM_URL = process.env.E2E_VLLM_URL ?? 'http://localhost:28000'

export async function waitForVllmReady(
  maxWaitMs = 300_000,
  intervalMs = 10_000,
): Promise<void> {
  const url = `${VLLM_URL}/v1/models`
  const deadline = Date.now() + maxWaitMs
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(10_000) })
      if (response.ok) return
    } catch {
      // vLLM not ready yet (model loading)
    }
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error(`vLLM not ready after ${maxWaitMs}ms`)
}
