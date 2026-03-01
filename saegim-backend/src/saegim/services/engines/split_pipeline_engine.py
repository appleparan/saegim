"""Split pipeline engine.

Uses Docling for layout detection and a separate OCR provider for text:
- Layout: DoclingLayoutDetector (IBM granite-docling-258M)
- OCR: Gemini API or vLLM (extracts text from cropped regions)

The engine crops regions from the original image and sends them
to the OCR provider in sequence.
"""

import logging
from pathlib import Path
from typing import Any, Literal

from saegim.services.docling_layout_service import DoclingLayoutDetector
from saegim.services.engines.base import BaseOCREngine
from saegim.services.gemini_ocr_service import GeminiTextOcrProvider
from saegim.services.ocr_connection_test import (
    check_gemini_connection,
    check_vllm_connection,
)
from saegim.services.ocr_pipeline import OcrPipeline
from saegim.services.vllm_ocr_service import VllmTextOcrProvider

logger = logging.getLogger(__name__)

SplitOcrProvider = Literal['gemini', 'vllm']


class SplitPipelineEngine(BaseOCREngine):
    """OCR engine using Docling layout detection + separate text OCR.

    Stage 1: DoclingLayoutDetector detects regions (BBox + category).
    Stage 2: Each region is cropped and sent to the OCR provider for text.

    Args:
        docling_model_name: HuggingFace model identifier for Docling.
        ocr_provider: OCR text provider ('gemini' or 'vllm').
        ocr_config: OCR provider configuration dict.
    """

    def __init__(
        self,
        docling_model_name: str,
        ocr_provider: SplitOcrProvider,
        ocr_config: dict[str, Any],
    ) -> None:
        """Initialize the split pipeline engine.

        Args:
            docling_model_name: HuggingFace model identifier for Docling.
            ocr_provider: OCR provider type.
            ocr_config: OCR provider configuration.

        Raises:
            ValueError: If ocr_provider is unknown.
        """
        self._docling_model_name = docling_model_name
        self._ocr_provider_name = ocr_provider
        self._ocr_config = ocr_config

        layout_detector = DoclingLayoutDetector(model_name=docling_model_name)
        text_provider = _create_text_provider(ocr_provider, ocr_config)
        self._layout_detector = layout_detector
        self._pipeline = OcrPipeline(layout_detector, text_provider)

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Extract layout elements via split pipeline.

        Args:
            image_path: Path to the page image file.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            OmniDocBench-compatible dict.
        """
        return self._pipeline.extract_page(image_path, page_width, page_height)

    def test_connection(self) -> tuple[bool, str]:
        """Test Docling availability and OCR provider connectivity.

        Returns:
            Tuple of (success, combined message).
        """
        layout_ok, layout_msg = self._layout_detector.test_connection()
        if not layout_ok:
            return (False, f'Layout (Docling): {layout_msg}')

        ocr_ok, ocr_msg = _check_ocr_provider(self._ocr_provider_name, self._ocr_config)
        if not ocr_ok:
            return (False, f'OCR provider: {ocr_msg}')

        return (True, f'{layout_msg} | {ocr_msg}')


def _create_text_provider(
    provider: str,
    config: dict[str, Any],
) -> GeminiTextOcrProvider | VllmTextOcrProvider:
    """Create a text-only OCR provider for the split pipeline.

    Args:
        provider: Provider type string.
        config: Provider configuration dict.

    Returns:
        Text OCR provider instance.

    Raises:
        ValueError: If provider is unknown.
    """
    if provider == 'gemini':
        return GeminiTextOcrProvider(
            api_key=config['api_key'],
            model=config.get('model', 'gemini-3-flash-preview'),
        )

    if provider == 'vllm':
        return VllmTextOcrProvider(
            host=config.get('host', 'localhost'),
            port=config.get('port', 8000),
            model=config.get('model', 'allenai/olmOCR-2-7B-1025-FP8'),
        )

    msg = f"Unknown split pipeline OCR provider: '{provider}'. Use 'gemini' or 'vllm'."
    raise ValueError(msg)


def _check_ocr_provider(
    provider: str,
    config: dict[str, Any],
) -> tuple[bool, str]:
    """Check OCR provider connectivity.

    Args:
        provider: Provider type string.
        config: Provider configuration dict.

    Returns:
        Tuple of (success, message).
    """
    if provider == 'gemini':
        return check_gemini_connection(config)

    if provider == 'vllm':
        return check_vllm_connection(config)

    return (False, f'Unknown OCR provider: {provider}')
