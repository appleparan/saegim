"""Split pipeline engine (Type 3).

Uses separate servers for layout detection and text recognition:
- Layout Server: PP-StructureV3 (detects BBox + category)
- OCR Server: Gemini API or vLLM (extracts text from cropped regions)

The backend crops regions from the original image and sends them
to the OCR server in sequence.
"""

import logging
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from saegim.services.engines.base import BaseOCREngine
from saegim.services.gemini_ocr_service import GeminiTextOcrProvider
from saegim.services.ocr_connection_test import (
    check_gemini_connection,
    check_ppstructure_connection,
    check_vllm_connection,
)
from saegim.services.ocr_pipeline import OcrPipeline
from saegim.services.ppstructure_service import PpstructureClient
from saegim.services.vllm_ocr_service import VllmTextOcrProvider

logger = logging.getLogger(__name__)

SplitOcrProvider = Literal['gemini', 'vllm']


class SplitPipelineEngine(BaseOCREngine):
    """OCR engine using separate layout and OCR servers.

    Stage 1: Layout server detects regions (BBox + category).
    Stage 2: Each region is cropped and sent to the OCR server for text.

    Args:
        layout_server_url: Layout detection server URL.
        ocr_provider: OCR text provider ('gemini' or 'vllm').
        ocr_config: OCR provider configuration dict.
    """

    def __init__(
        self,
        layout_server_url: str,
        ocr_provider: SplitOcrProvider,
        ocr_config: dict[str, Any],
    ) -> None:
        """Initialize the split pipeline engine.

        Args:
            layout_server_url: Layout server URL.
            ocr_provider: OCR provider type.
            ocr_config: OCR provider configuration.

        Raises:
            ValueError: If ocr_provider is unknown.
        """
        self._layout_url = layout_server_url
        self._ocr_provider_name = ocr_provider
        self._ocr_config = ocr_config

        layout_host, layout_port = _parse_url(layout_server_url)
        self._layout_host = layout_host
        self._layout_port = layout_port

        layout_client = PpstructureClient(host=layout_host, port=layout_port)
        text_provider = _create_text_provider(ocr_provider, ocr_config)
        self._pipeline = OcrPipeline(layout_client, text_provider)

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
        """Test both layout server and OCR provider connectivity.

        Returns:
            Tuple of (success, combined message).
        """
        layout_ok, layout_msg = check_ppstructure_connection(
            {'host': self._layout_host, 'port': self._layout_port}
        )
        if not layout_ok:
            return (False, f'Layout server: {layout_msg}')

        ocr_ok, ocr_msg = _check_ocr_provider(self._ocr_provider_name, self._ocr_config)
        if not ocr_ok:
            return (False, f'OCR provider: {ocr_msg}')

        return (True, f'{layout_msg} | {ocr_msg}')


def _parse_url(url: str) -> tuple[str, int]:
    """Parse host and port from a URL string.

    Args:
        url: URL string.

    Returns:
        Tuple of (host, port).
    """
    parsed = urlparse(url)
    host = parsed.hostname or 'localhost'
    port = parsed.port or 18811
    return (host, port)


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
