"""Gemini API-based OCR service for structured layout detection.

Sends page images to Google Gemini API and parses structured output
into OmniDocBench-compatible format.
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

_GEMINI_API_BASE = 'https://generativelanguage.googleapis.com/v1beta'


class GeminiOcrProvider:
    """OCR provider using Google Gemini API."""

    def __init__(self, api_key: str, model: str = 'gemini-3-flash-preview') -> None:
        """Initialize Gemini OCR provider.

        Args:
            api_key: Google Gemini API key.
            model: Gemini model name.
        """
        self._api_key = api_key
        self._model = model

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Extract structured layout elements from a page image via Gemini API.

        Args:
            image_path: Path to the page image file.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            OmniDocBench-compatible dict with layout_dets, page_attribute, extra.

        Raises:
            RuntimeError: If Gemini API call fails.
        """
        prompt = STRUCTURED_OCR_PROMPT.format(width=page_width, height=page_height)
        image_data = image_path.read_bytes()
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        # Determine MIME type from extension
        suffix = image_path.suffix.lower()
        mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
        mime_type = mime_map.get(suffix, 'image/png')

        url = f'{_GEMINI_API_BASE}/models/{self._model}:generateContent?key={self._api_key}'
        payload = {
            'contents': [
                {
                    'parts': [
                        {'text': prompt},
                        {
                            'inline_data': {
                                'mime_type': mime_type,
                                'data': image_b64,
                            },
                        },
                    ],
                },
            ],
            'generationConfig': {
                'temperature': 0.1,
                'responseMimeType': 'application/json',
            },
        }

        try:
            with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as exc:
            msg = f'Gemini API returned {exc.response.status_code}: {exc.response.text}'
            raise RuntimeError(msg) from exc
        except httpx.RequestError as exc:
            msg = f'Gemini API request failed: {exc}'
            raise RuntimeError(msg) from exc

        elements = _parse_gemini_response(result)
        return build_omnidocbench_page(elements)


def _parse_gemini_response(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse Gemini API response to extract layout elements.

    Args:
        result: Raw Gemini API JSON response.

    Returns:
        List of element dicts with category_type, bbox, text, order.
    """
    try:
        candidates = result.get('candidates', [])
        if not candidates:
            logger.warning('Gemini response has no candidates')
            return []

        content = candidates[0].get('content', {})
        parts = content.get('parts', [])
        if not parts:
            logger.warning('Gemini response has no parts')
            return []

        text = parts[0].get('text', '')
        if not text.strip():
            return []

        # Parse JSON response (may be wrapped in markdown code block)
        text = text.strip()
        if text.startswith('```'):
            # Remove markdown code fences
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text

        elements = json.loads(text)
        if not isinstance(elements, list):
            logger.warning('Gemini response is not a list: %s', type(elements))
            return []

        return elements

    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.exception('Failed to parse Gemini response: %s', exc)
        return []


class GeminiTextOcrProvider:
    """Text-only OCR provider using Google Gemini API.

    Used in the 2-stage pipeline: receives a cropped region image
    and returns extracted text.
    """

    def __init__(self, api_key: str, model: str = 'gemini-3-flash-preview') -> None:
        """Initialize Gemini text OCR provider.

        Args:
            api_key: Google Gemini API key.
            model: Gemini model name.
        """
        self._api_key = api_key
        self._model = model

    def extract_text(self, image_bytes: bytes, category_hint: str = '') -> str:
        """Extract text from a cropped region image via Gemini API.

        Args:
            image_bytes: Raw image bytes of the cropped region.
            category_hint: OmniDocBench category hint for prompt selection.

        Returns:
            Extracted text string.

        Raises:
            RuntimeError: If Gemini API call fails.
        """
        prompt = get_text_prompt(category_hint)
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        url = f'{_GEMINI_API_BASE}/models/{self._model}:generateContent?key={self._api_key}'
        payload = {
            'contents': [
                {
                    'parts': [
                        {'text': prompt},
                        {
                            'inline_data': {
                                'mime_type': 'image/png',
                                'data': image_b64,
                            },
                        },
                    ],
                },
            ],
            'generationConfig': {
                'temperature': 0.1,
            },
        }

        try:
            with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as exc:
            msg = f'Gemini API returned {exc.response.status_code}: {exc.response.text}'
            raise RuntimeError(msg) from exc
        except httpx.RequestError as exc:
            msg = f'Gemini API request failed: {exc}'
            raise RuntimeError(msg) from exc

        return _extract_text_from_gemini(result)


def _extract_text_from_gemini(result: dict[str, Any]) -> str:
    """Extract plain text from Gemini API response.

    Args:
        result: Raw Gemini API JSON response.

    Returns:
        Extracted text string, empty if parsing fails.
    """
    try:
        candidates = result.get('candidates', [])
        if not candidates:
            return ''
        content = candidates[0].get('content', {})
        parts = content.get('parts', [])
        if not parts:
            return ''
        return parts[0].get('text', '').strip()
    except (KeyError, IndexError) as exc:
        logger.exception('Failed to extract text from Gemini response: %s', exc)
        return ''
