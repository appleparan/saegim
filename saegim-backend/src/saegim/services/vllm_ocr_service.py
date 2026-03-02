"""vLLM-based OCR service for structured layout detection.

Sends page images to a local vLLM server (OpenAI-compatible API)
and parses structured output into OmniDocBench-compatible format
via the adapter → exporter pipeline.
"""

import base64
import logging
from pathlib import Path
from typing import Any

import httpx

from saegim.services.adapters.base import ModelAdapter
from saegim.services.adapters.resolver import resolve_adapter
from saegim.services.exporters.omnidocbench import export_page
from saegim.services.ocr_provider import get_text_prompt

logger = logging.getLogger(__name__)

_MIME_MAP = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}


class VllmOcrProvider:
    """OCR provider using local vLLM server (OpenAI-compatible API)."""

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 8000,
        model: str = 'allenai/olmOCR-2-7B-1025',
        *,
        adapter: ModelAdapter | None = None,
    ) -> None:
        """Initialize vLLM OCR provider.

        Args:
            host: vLLM server host.
            port: vLLM server port.
            model: Model name to use.
            adapter: Model adapter override. Resolved from model name if None.
        """
        self._host = host
        self._port = port
        self._model = model
        self._adapter = adapter or resolve_adapter(model)

    @property
    def base_url(self) -> str:
        """Build vLLM API base URL.

        Returns:
            Base URL string.
        """
        return f'http://{self._host}:{self._port}'

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Extract structured layout elements from a page image via vLLM.

        Args:
            image_path: Path to the page image file.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            OmniDocBench-compatible dict with layout_dets, page_attribute, extra.

        Raises:
            RuntimeError: If vLLM API call fails.
        """
        image_data = image_path.read_bytes()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        mime_type = _MIME_MAP.get(image_path.suffix.lower(), 'image/png')

        messages = self._adapter.build_messages(image_b64, mime_type, page_width, page_height)
        url = f'{self.base_url}/v1/chat/completions'
        payload = {
            'model': self._model,
            'messages': messages,
            'temperature': 0.1,
            'max_tokens': 4096,
        }

        try:
            with httpx.Client(timeout=httpx.Timeout(300.0)) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as exc:
            msg = f'vLLM API returned {exc.response.status_code}: {exc.response.text}'
            raise RuntimeError(msg) from exc
        except httpx.RequestError as exc:
            msg = f'vLLM API request failed: {exc}'
            raise RuntimeError(msg) from exc

        page_ir = self._adapter.parse_response(result, page_width, page_height)
        return export_page(page_ir)


class VllmTextOcrProvider:
    """Text-only OCR provider using local vLLM server.

    Used in the 2-stage pipeline: receives a cropped region image
    and returns extracted text via OpenAI-compatible API.
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 8000,
        model: str = 'allenai/olmOCR-2-7B-1025',
    ) -> None:
        """Initialize vLLM text OCR provider.

        Args:
            host: vLLM server host.
            port: vLLM server port.
            model: Model name to use.
        """
        self._host = host
        self._port = port
        self._model = model

    @property
    def base_url(self) -> str:
        """Build vLLM API base URL.

        Returns:
            Base URL string.
        """
        return f'http://{self._host}:{self._port}'

    def extract_text(self, image_bytes: bytes, category_hint: str = '') -> str:
        """Extract text from a cropped region image via vLLM.

        Args:
            image_bytes: Raw image bytes of the cropped region.
            category_hint: OmniDocBench category hint for prompt selection.

        Returns:
            Extracted text string.

        Raises:
            RuntimeError: If vLLM API call fails.
        """
        prompt = get_text_prompt(category_hint)
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        url = f'{self.base_url}/v1/chat/completions'
        payload = {
            'model': self._model,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/png;base64,{image_b64}',
                            },
                        },
                    ],
                },
            ],
            'temperature': 0.1,
            'max_tokens': 4096,
        }

        try:
            with httpx.Client(timeout=httpx.Timeout(300.0)) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as exc:
            msg = f'vLLM API returned {exc.response.status_code}: {exc.response.text}'
            raise RuntimeError(msg) from exc
        except httpx.RequestError as exc:
            msg = f'vLLM API request failed: {exc}'
            raise RuntimeError(msg) from exc

        return _extract_text_from_vllm(result)


def _extract_text_from_vllm(result: dict[str, Any]) -> str:
    """Extract plain text from vLLM OpenAI-compatible response.

    Args:
        result: Raw vLLM API JSON response.

    Returns:
        Extracted text string, empty if parsing fails.
    """
    try:
        choices = result.get('choices', [])
        if not choices:
            return ''
        message = choices[0].get('message', {})
        return message.get('content', '').strip()
    except (KeyError, IndexError) as exc:
        logger.exception('Failed to extract text from vLLM response: %s', exc)
        return ''
