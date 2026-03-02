"""PaddleOCR-VL adapter for task-prompt-based VLM OCR models.

Works with: PaddlePaddle/PaddleOCR-VL and similar models that accept
a simple task prompt (e.g. ``"OCR:"``) plus an image and return plain
text without any geometry or coordinate information.
"""

import logging
from typing import Any

from saegim.services.docir import ElementIR, PageIR

logger = logging.getLogger(__name__)

_DEFAULT_PROMPT = 'OCR:'


class PaddleOcrVlAdapter:
    """Adapter for PaddleOCR-VL and task-prompt-based VLM models.

    Args:
        prompt: Task prompt to send with the image.
    """

    def __init__(self, prompt: str = _DEFAULT_PROMPT) -> None:
        """Initialize PaddleOCR-VL adapter.

        Args:
            prompt: Task prompt to send with the image.
        """
        self._prompt = prompt

    def build_messages(
        self,
        image_b64: str,
        mime_type: str,
        page_width: int,  # noqa: ARG002
        page_height: int,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Build API messages with task prompt and image.

        Args:
            image_b64: Base64-encoded image data.
            mime_type: Image MIME type.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            List of message dicts for the chat completions API.
        """
        return [
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': self._prompt},
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
        """Parse PaddleOCR-VL response into PageIR.

        Args:
            result: Raw API response dict.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            Parsed PageIR with geometry-free elements.
        """
        text = _extract_content(result)
        return _parse_paddleocr_output(text, page_width, page_height, self._prompt)


def _extract_content(result: dict[str, Any]) -> str:
    """Extract text content from OpenAI-compatible response.

    Args:
        result: Raw API response dict.

    Returns:
        Text content string, or empty string if not available.
    """
    choices = result.get('choices', [])
    if not choices:
        return ''
    message = choices[0].get('message', {})
    return message.get('content', '')


def _parse_paddleocr_output(
    text: str,
    page_width: int,
    page_height: int,
    prompt: str,
) -> PageIR:
    """Parse PaddleOCR-VL output text into PageIR.

    The entire non-empty response becomes a single text_block element
    with no geometry, since PaddleOCR-VL does not provide coordinates.

    Args:
        text: Raw model output text.
        page_width: Image width in pixels.
        page_height: Image height in pixels.
        prompt: Prompt that was used for this request.

    Returns:
        PageIR with parsed elements.
    """
    meta: dict[str, Any] = {'prompt': prompt}
    elements: tuple[ElementIR, ...] = ()

    stripped = text.strip()
    if stripped:
        meta['fulltext'] = text
        elements = (
            ElementIR(
                id='e0',
                kind='text_block',
                text=text,
                reading_order=0,
            ),
        )

    return PageIR(
        page_id='unknown',
        width_px=page_width,
        height_px=page_height,
        elements=elements,
        meta=meta,
    )
