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

// --- Documents ---

export type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'error'

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
  readonly image_url: string
  readonly annotation_data: AnnotationData
  readonly auto_extracted_data: AnnotationData | null
  readonly status: PageStatus
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

// --- Tasks ---

export type TaskAction = 'assigned' | 'started' | 'saved' | 'submitted' | 'approved' | 'rejected'

export interface TaskResponse {
  readonly id: string
  readonly page_id: string
  readonly document_name: string
  readonly page_no: number
  readonly status: PageStatus
  readonly assigned_at: string
}

// --- Export ---

export interface ExportResponse {
  readonly download_url: string
  readonly filename: string
}
