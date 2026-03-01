"""vLLM server engine.

Uses a vLLM-compatible server for full-page OCR via the OpenAI chat completions API.
"""

import logging
from pathlib import Path
from typing import Any

from saegim.services.engines.base import BaseOCREngine
from saegim.services.ocr_connection_test import check_vllm_connection
from saegim.services.vllm_ocr_service import VllmOcrProvider

logger = logging.getLogger(__name__)


class VllmEngine(BaseOCREngine):
    """OCR engine using a vLLM-compatible server.

    Sends page images to a vLLM server (OpenAI-compatible API) and returns
    structured layout elements.

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
        """Initialize the vLLM engine.

        Args:
            host: Server hostname.
            port: Server port number.
            model: Model name running on the server.
        """
        self._host = host
        self._port = port
        self._model = model
        self._provider = VllmOcrProvider(host=host, port=port, model=model)

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Extract layout elements via vLLM server.

        Args:
            image_path: Path to the page image file.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            OmniDocBench-compatible dict.
        """
        return self._provider.extract_page(image_path, page_width, page_height)

    def test_connection(self) -> tuple[bool, str]:
        """Test vLLM server connectivity.

        Returns:
            Tuple of (success, message).
        """
        return check_vllm_connection({'host': self._host, 'port': self._port})
