/**
 * API request/response type definitions matching the backend schemas.
 */

import type { AnnotationData, PageAttribute } from '$lib/types/omnidocbench'

// --- Projects ---

export interface ProjectResponse {
  readonly id: string
  readonly name: string
  readonly description: string
  readonly created_at: string
}

export interface CreateProjectRequest {
  readonly name: string
  readonly description?: string
}

// --- OCR Config (multi-instance engine registry) ---

export type EngineType = 'commercial_api' | 'vllm' | 'split_pipeline' | 'pdfminer'
export type RegisterableEngineType = 'commercial_api' | 'vllm' | 'split_pipeline'
export type CommercialApiProvider = 'gemini' | 'vllm'
export type SplitPipelineOcrProvider = 'gemini' | 'vllm'
export type SplitPipelineLayoutProvider = 'docling' | 'pp_doclayout'

export interface CommercialApiConfig {
  readonly provider: CommercialApiProvider
  readonly api_key?: string
  readonly model: string
  readonly prompt?: string
}

export interface VllmServerConfig {
  readonly host: string
  readonly port: number
  readonly model?: string
}

export interface SplitPipelineConfig {
  readonly layout_provider?: SplitPipelineLayoutProvider
  readonly docling_model_name: string
  readonly ocr_provider: SplitPipelineOcrProvider
  readonly ocr_api_key?: string
  readonly ocr_host?: string
  readonly ocr_port?: number
  readonly ocr_model?: string
}

export interface EngineInstance {
  readonly engine_type: RegisterableEngineType
  readonly name: string
  readonly config: Record<string, unknown>
}

export interface EngineInstanceCreate {
  readonly engine_id?: string
  readonly engine_type: RegisterableEngineType
  readonly name: string
  readonly config: Record<string, unknown>
}

export interface EngineInstanceUpdate {
  readonly name?: string
  readonly config?: Record<string, unknown>
}

export interface OcrConfigResponse {
  readonly default_engine_id: string | null
  readonly engines: Record<string, EngineInstance>
  readonly env_gemini_api_key?: string
}

export interface DefaultEngineUpdate {
  readonly engine_id: string | null
}

export interface OcrConnectionTestRequest {
  readonly engine_id: string
}

// --- Available Engines (for per-element OCR) ---

export interface AvailableEngine {
  readonly engine_id: string
  readonly engine_type: RegisterableEngineType
  readonly name: string
}

export interface AvailableEnginesResponse {
  readonly engines: readonly AvailableEngine[]
}

export interface OcrConnectionTestResponse {
  readonly success: boolean
  readonly message: string
}

// --- Documents ---

export type DocumentStatus =
  | 'uploading'
  | 'processing'
  | 'extracting'
  | 'ready'
  | 'error'
  | 'extraction_failed'

export interface DocumentResponse {
  readonly id: string
  readonly project_id: string
  readonly filename: string
  readonly total_pages: number
  readonly status: DocumentStatus
  readonly created_at: string
}

export interface DocumentStatusResponse {
  readonly id: string
  readonly status: DocumentStatus
  readonly total_pages: number
  readonly processed_pages: number
}

// --- Pages ---

export type PageStatus = 'pending' | 'in_progress' | 'submitted' | 'reviewed'

export interface PageResponse {
  readonly id: string
  readonly document_id: string
  readonly page_no: number
  readonly width: number
  readonly height: number
  readonly image_path?: string
  readonly image_url: string
  readonly pdf_path?: string | null
  readonly pdf_url: string
  readonly annotation_data: AnnotationData
  readonly auto_extracted_data: AnnotationData | null
  readonly status: PageStatus
  readonly assigned_to?: string | null
  readonly project_id?: string
  readonly project_name?: string
  readonly document_filename?: string
}

export interface PageSummary {
  readonly id: string
  readonly page_no: number
  readonly status: PageStatus
}

export interface SavePageRequest {
  readonly annotation_data: AnnotationData
}

export interface SavePageAttributesRequest {
  readonly page_attribute: PageAttribute
}

// --- Elements ---

export interface CreateElementRequest {
  readonly category_type: string
  readonly poly: readonly number[]
  readonly text?: string
}

export interface UpdateElementRequest {
  readonly category_type?: string
  readonly poly?: readonly number[]
  readonly text?: string
  readonly latex?: string
  readonly html?: string
  readonly attribute?: Record<string, string | boolean>
  readonly ignore?: boolean
  readonly order?: number
}

export interface ElementResponse {
  readonly anno_id: number
  readonly category_type: string
  readonly poly: readonly number[]
}

// --- Relations ---

export interface CreateRelationRequest {
  readonly source_anno_id: number
  readonly target_anno_id: number
  readonly relation_type: string
}

export interface RelationResponse {
  readonly id: string
  readonly source_anno_id: number
  readonly target_anno_id: number
  readonly relation_type: string
}

// --- Project Members ---

export type ProjectMemberRole = 'owner' | 'annotator' | 'reviewer'

export interface ProjectMemberResponse {
  readonly user_id: string
  readonly user_name: string
  readonly user_email: string
  readonly role: ProjectMemberRole
  readonly joined_at: string
}

export interface AddProjectMemberRequest {
  readonly user_id: string
  readonly role: ProjectMemberRole
}

export interface UpdateProjectMemberRequest {
  readonly role: ProjectMemberRole
}

// --- Tasks ---

export type TaskAction = 'assigned' | 'started' | 'saved' | 'submitted' | 'approved' | 'rejected'

export interface TaskResponse {
  readonly page_id: string
  readonly page_no: number
  readonly document_id: string
  readonly document_filename: string
  readonly project_id: string
  readonly project_name: string
  readonly status: PageStatus
  readonly assigned_at: string
}

export interface ReviewQueueItem {
  readonly page_id: string
  readonly page_no: number
  readonly document_id: string
  readonly document_filename: string
  readonly assigned_to: string | null
  readonly assigned_to_name: string | null
  readonly submitted_at: string
}

export type ReviewAction = 'approved' | 'rejected'

export interface ReviewRequest {
  readonly action: ReviewAction
  readonly comment?: string
}

// --- Export ---

export interface ExportResponse {
  readonly project_name: string
  readonly total_pages: number
  readonly data: readonly Record<string, unknown>[]
}

// --- Admin ---

export type UserRole = 'admin' | 'annotator' | 'reviewer'

export interface AdminUserResponse {
  readonly id: string
  readonly name: string
  readonly login_id: string
  readonly email: string
  readonly role: UserRole
  readonly must_change_password: boolean
  readonly is_active: boolean
  readonly created_at: string
}

export interface AdminUserUpdateRequest {
  readonly role?: UserRole
  readonly is_active?: boolean
}

export interface AdminProjectResponse {
  readonly id: string
  readonly name: string
  readonly description: string
  readonly member_count: number
  readonly total_pages: number
  readonly completed_pages: number
  readonly submitted_pages: number
  readonly created_at: string
}

export interface AdminStatsResponse {
  readonly total_users: number
  readonly active_users: number
  readonly total_projects: number
  readonly total_pages: number
  readonly completed_pages: number
  readonly submitted_pages: number
  readonly completion_rate: number
}
