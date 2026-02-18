"""vLLM-based OCR service for structured layout detection.

Sends page images to a local vLLM server (OpenAI-compatible API)
and parses structured output into OmniDocBench-compatible format.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from saegim.services.ocr_provider import (
    STRUCTURED_OCR_PROMPT,
    build_omnidocbench_page,
    get_text_prompt,
)

logger = logging.getLogger(__name__)


class VllmOcrProvider:
    """OCR provider using local vLLM server (OpenAI-compatible API)."""

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 8000,
        model: str = 'allenai/olmOCR-2-7B-1025',
    ) -> None:
        """Initialize vLLM OCR provider.

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
        prompt = STRUCTURED_OCR_PROMPT.format(width=page_width, height=page_height)
        image_data = image_path.read_bytes()
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        suffix = image_path.suffix.lower()
        mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
        mime_type = mime_map.get(suffix, 'image/png')

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
                                'url': f'data:{mime_type};base64,{image_b64}',
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

        elements = _parse_vllm_response(result)
        return build_omnidocbench_page(elements)


def _parse_vllm_response(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse vLLM OpenAI-compatible response to extract layout elements.

    Args:
        result: Raw vLLM API JSON response.

    Returns:
        List of element dicts with category_type, bbox, text, order.
    """
    try:
        choices = result.get('choices', [])
        if not choices:
            logger.warning('vLLM response has no choices')
            return []

        message = choices[0].get('message', {})
        text = message.get('content', '')
        if not text.strip():
            return []

        # Parse JSON response (may be wrapped in markdown code block)
        text = text.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text

        elements = json.loads(text)
        if not isinstance(elements, list):
            logger.warning('vLLM response is not a list: %s', type(elements))
            return []

        return elements

    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.exception('Failed to parse vLLM response: %s', exc)
        return []


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
