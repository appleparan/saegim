"""OCR engine abstraction layer.

Provides a unified interface for different OCR engine types:
- commercial_api: Commercial VLM API (Gemini)
- vllm: vLLM server (OpenAI-compatible)
- split_pipeline: Docling layout detection + Gemini/vLLM text OCR
- pdfminer: Fallback (no GPU required)
"""

from saegim.services.engines.base import BaseOCREngine
from saegim.services.engines.factory import build_engine

__all__ = ['BaseOCREngine', 'build_engine']
