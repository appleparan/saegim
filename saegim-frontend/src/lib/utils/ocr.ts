import type { EngineType } from '$lib/api/types'

export const engineLabels: Record<EngineType, string> = {
  pdfminer: 'pdfminer',
  commercial_api: 'Gemini API',
  vllm: 'vLLM',
  split_pipeline: 'Docling + OCR',
}
