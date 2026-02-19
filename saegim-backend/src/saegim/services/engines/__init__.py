"""OCR engine abstraction layer.

Provides a unified interface for different OCR engine types:
- Type 1: Commercial VLM API (Gemini, vLLM)
- Type 2: Integrated Pipeline Server (PP-StructureV3 + PP-OCR)
- Type 3: Split Pipeline (Layout Server + OCR Server)
- Type 4: PyMuPDF Fallback (no GPU required)
"""

from saegim.services.engines.base import BaseOCREngine

__all__ = ['BaseOCREngine']
