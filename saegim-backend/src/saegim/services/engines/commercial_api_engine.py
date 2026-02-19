"""Commercial VLM API engine (Type 1).

Uses an external VLM API (Gemini, vLLM) that performs both layout analysis
and text recognition in a single request.
"""

import logging
from pathlib import Path
from typing import Any, Literal

from saegim.services.engines.base import BaseOCREngine
from saegim.services.gemini_ocr_service import GeminiOcrProvider
from saegim.services.ocr_connection_test import (
    check_gemini_connection,
    check_vllm_connection,
)
from saegim.services.vllm_ocr_service import VllmOcrProvider

logger = logging.getLogger(__name__)

CommercialProvider = Literal['gemini', 'vllm']


class CommercialApiEngine(BaseOCREngine):
    """OCR engine using a commercial or self-hosted VLM API.

    The VLM receives a full page image and returns structured layout
    elements with text content in a single API call.

    Args:
        provider: VLM provider type ('gemini' or 'vllm').
        config: Provider-specific configuration dict.
            For gemini: {'api_key': str, 'model': str}
            For vllm: {'host': str, 'port': int, 'model': str}
    """

    def __init__(self, provider: CommercialProvider, config: dict[str, Any]) -> None:
        """Initialize the commercial API engine.

        Args:
            provider: VLM provider type.
            config: Provider-specific configuration.

        Raises:
            ValueError: If provider is unknown.
        """
        self._provider_name = provider
        self._config = config
        self._provider = _create_provider(provider, config)

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Extract layout elements via VLM API.

        Args:
            image_path: Path to the page image file.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            OmniDocBench-compatible dict.
        """
        return self._provider.extract_page(image_path, page_width, page_height)

    def test_connection(self) -> tuple[bool, str]:
        """Test VLM API connectivity.

        Returns:
            Tuple of (success, message).
        """
        if self._provider_name == 'gemini':
            return check_gemini_connection(self._config)

        if self._provider_name == 'vllm':
            return check_vllm_connection(self._config)

        return (False, f'Unknown provider: {self._provider_name}')


def _create_provider(
    provider: str,
    config: dict[str, Any],
) -> GeminiOcrProvider | VllmOcrProvider:
    """Create the underlying OCR provider instance.

    Args:
        provider: Provider type string.
        config: Provider configuration dict.

    Returns:
        Provider instance with extract_page() method.

    Raises:
        ValueError: If provider is unknown.
    """
    if provider == 'gemini':
        return GeminiOcrProvider(
            api_key=config['api_key'],
            model=config.get('model', 'gemini-2.0-flash'),
        )

    if provider == 'vllm':
        return VllmOcrProvider(
            host=config.get('host', 'localhost'),
            port=config.get('port', 8000),
            model=config.get('model', 'allenai/olmOCR-2-7B-1025'),
        )

    msg = f"Unknown commercial API provider: '{provider}'. Use 'gemini' or 'vllm'."
    raise ValueError(msg)
