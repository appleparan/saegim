"""Chandra adapter for STRUCTURED_OCR_PROMPT-based models.

Works with: datalab-to/chandra, allenai/olmOCR-*, and other models
that accept the shared structured OCR prompt and return JSON arrays
of layout elements via OpenAI-compatible chat completions API.
"""

import json
import logging
from typing import Any

from partialjson import JSONParser

from saegim.services.docir import ElementIR, Geometry, PageIR
from saegim.services.ocr_provider import STRUCTURED_OCR_PROMPT

logger = logging.getLogger(__name__)

_partial_parser = JSONParser(strict=False)


class ChandraAdapter:
    """Adapter for Chandra and STRUCTURED_OCR_PROMPT-compatible models."""

    def build_messages(
        self,
        image_b64: str,
        mime_type: str,
        page_width: int,
        page_height: int,
    ) -> list[dict[str, Any]]:
        """Build OpenAI-compatible chat messages.

        Args:
            image_b64: Base64-encoded image data.
            mime_type: Image MIME type.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            List of message dicts for the chat completions API.
        """
        prompt = STRUCTURED_OCR_PROMPT.format(width=page_width, height=page_height)
        return [
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {
                        'type': 'image_url',
                        'image_url': {'url': f'data:{mime_type};base64,{image_b64}'},
                    },
                ],
            },
        ]

    def parse_response(
        self,
        result: dict[str, Any],
        page_width: int,
        page_height: int,
    ) -> PageIR:
        """Parse OpenAI-compatible response into PageIR.

        Args:
            result: Raw API response dict.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            Parsed PageIR.
        """
        elements = parse_openai_response(result)
        return elements_to_page_ir(elements, page_width, page_height)


def parse_openai_response(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse OpenAI-compatible chat response to extract layout elements.

    Args:
        result: Raw API response dict with choices[0].message.content.

    Returns:
        List of element dicts with category_type, bbox, text, order.
    """
    text = ''
    try:
        choices = result.get('choices', [])
        if not choices:
            logger.warning('Response has no choices')
            return []

        message = choices[0].get('message', {})
        text = message.get('content', '')
        if not text.strip():
            return []

        text = strip_markdown_fences(text)
        text = text.strip()
        if not text:
            logger.warning('Response empty after stripping markdown fences')
            return []

        elements = loads_lenient(text)
        if not isinstance(elements, list):
            logger.warning('Response is not a list: %s', type(elements))
            return []

        return elements

    except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
        raw_preview = text[:200] if text else '(empty)'
        logger.warning('Failed to parse response: %s | raw preview: %s', exc, raw_preview)
        return []


def loads_lenient(text: str) -> list | dict | str | int | float | bool | None:
    r"""Parse JSON with lenient handling of LLM output quirks.

    Handles common JSON issues:
    - Control characters (tabs, newlines) inside strings
    - Invalid escape sequences (``\R``, ``\U``)
    - Missing commas, unclosed brackets
    - Extra trailing data after valid JSON

    Args:
        text: Raw JSON string from LLM.

    Returns:
        Parsed JSON value.

    Raises:
        json.JSONDecodeError: If text cannot be parsed even with repair.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass

    return _partial_parser.parse(text)


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from LLM output.

    Args:
        text: Raw text that may be wrapped in markdown code fences.

    Returns:
        Inner content with fences removed, or original text if no fences.
    """
    text = text.strip()
    if not text.startswith('```'):
        return text
    lines = text.split('\n')
    if len(lines) > 2 and lines[-1].strip() == '```':
        return '\n'.join(lines[1:-1])
    if len(lines) > 1:
        return '\n'.join(lines[1:])
    return text


def elements_to_page_ir(
    elements: list[dict[str, Any]],
    page_width: int,
    page_height: int,
) -> PageIR:
    """Convert raw element dicts to PageIR.

    Args:
        elements: List of element dicts from LLM response.
        page_width: Image width in pixels.
        page_height: Image height in pixels.

    Returns:
        PageIR with converted elements.
    """
    ir_elements = []
    for i, elem in enumerate(elements):
        bbox_raw = elem.get('bbox')
        geometry = None
        if bbox_raw and len(bbox_raw) >= 4:
            geometry = Geometry(
                bbox=(
                    float(bbox_raw[0]),
                    float(bbox_raw[1]),
                    float(bbox_raw[2]),
                    float(bbox_raw[3]),
                )
            )

        ir_elements.append(
            ElementIR(
                id=f'e{i}',
                kind=elem.get('category_type', 'unknown'),
                geometry=geometry,
                text=elem.get('text'),
                reading_order=elem.get('order', i),
            )
        )

    return PageIR(
        page_id='unknown',
        width_px=page_width,
        height_px=page_height,
        elements=tuple(ir_elements),
    )
