"""Integrated pipeline server engine (Type 2).

Uses a self-hosted framework that performs both layout detection and text
recognition in a single server. Supports two backends:

- PP-StructureV3: PaddleOCR-based server (model starts with 'PP-')
- vLLM: OpenAI-compatible VLM server (HuggingFace models like datalab-to/chandra)
"""

import logging
from pathlib import Path
from typing import Any

from saegim.services.engines.base import BaseOCREngine
from saegim.services.ocr_connection_test import (
    check_ppstructure_connection,
    check_vllm_connection,
)
from saegim.services.ocr_pipeline import OcrPipeline
from saegim.services.ppstructure_service import PpstructureClient
from saegim.services.vllm_ocr_service import VllmOcrProvider

logger = logging.getLogger(__name__)

_PPSTRUCTURE_MODEL_PREFIXES = ('PP-',)


def _is_ppstructure_model(model: str) -> bool:
    """Check if the model name indicates a PP-StructureV3 server.

    Args:
        model: Model name string.

    Returns:
        True if the model is a PP-StructureV3 model.
    """
    return any(model.startswith(prefix) for prefix in _PPSTRUCTURE_MODEL_PREFIXES)


class IntegratedServerEngine(BaseOCREngine):
    """OCR engine using an integrated pipeline server.

    The server receives a page image and returns layout regions
    with built-in OCR text in a single response.

    Automatically selects the appropriate backend based on the model name:
    - PP-StructureV3 models (prefix 'PP-'): uses PpstructureClient
    - Other models (e.g. datalab-to/chandra): uses VllmOcrProvider

    Args:
        host: Server hostname.
        port: Server port.
        model: Model name running on the server.
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 8000,
        model: str = 'datalab-to/chandra',
    ) -> None:
        """Initialize the integrated server engine.

        Args:
            host: Server hostname.
            port: Server port number.
            model: Model name running on the server.
        """
        self._host = host
        self._port = port
        self._model = model
        self._use_ppstructure = _is_ppstructure_model(model)

        self._layout_client: PpstructureClient | None = None
        self._pipeline: OcrPipeline | None = None
        self._vllm_provider: VllmOcrProvider | None = None

        if self._use_ppstructure:
            self._layout_client = PpstructureClient(host=host, port=port)
            self._pipeline = OcrPipeline(self._layout_client, use_builtin_ocr=True)
        else:
            self._vllm_provider = VllmOcrProvider(host=host, port=port, model=model)

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Extract layout elements via integrated server.

        Args:
            image_path: Path to the page image file.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            OmniDocBench-compatible dict.
        """
        if self._use_ppstructure:
            assert self._pipeline is not None
            return self._pipeline.extract_page(image_path, page_width, page_height)
        assert self._vllm_provider is not None
        return self._vllm_provider.extract_page(image_path, page_width, page_height)

    def test_connection(self) -> tuple[bool, str]:
        """Test integrated server connectivity.

        Uses PP-StructureV3 health check or vLLM model list depending
        on the configured model type.

        Returns:
            Tuple of (success, message).
        """
        config = {'host': self._host, 'port': self._port}
        if self._use_ppstructure:
            return check_ppstructure_connection(config)
        return check_vllm_connection(config)
