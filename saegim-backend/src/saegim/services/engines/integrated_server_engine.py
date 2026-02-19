"""Integrated pipeline server engine (Type 2).

Uses a self-hosted framework (e.g., PP-StructureV3 + PP-OCR) that
performs both layout detection and text recognition in a single server.
"""

import logging
from pathlib import Path
from typing import Any

from saegim.services.engines.base import BaseOCREngine
from saegim.services.ocr_connection_test import check_ppstructure_connection
from saegim.services.ocr_pipeline import OcrPipeline
from saegim.services.ppstructure_service import PpstructureClient

logger = logging.getLogger(__name__)


class IntegratedServerEngine(BaseOCREngine):
    """OCR engine using an integrated pipeline server.

    The server receives a page image and returns layout regions
    with built-in OCR text in a single response.

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
        self._layout_client = PpstructureClient(host=host, port=port)
        self._pipeline = OcrPipeline(self._layout_client, use_builtin_ocr=True)

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
        return self._pipeline.extract_page(image_path, page_width, page_height)

    def test_connection(self) -> tuple[bool, str]:
        """Test integrated server connectivity.

        Returns:
            Tuple of (success, message).
        """
        return check_ppstructure_connection({'host': self._host, 'port': self._port})
