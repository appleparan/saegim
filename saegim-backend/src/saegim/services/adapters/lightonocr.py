"""LightOnOCR adapter for prompt-free VLM OCR models.

Works with: lightonai/LightOnOCR-2-1B-bbox-soup and similar models that
accept only an image (no prompt) and return plain text with embedded
``![image](image_N.png)x1,y1,x2,y2`` markers for figure regions.

Coordinates in the model output are normalised to 0-1000 range and must
be converted to pixel space before constructing Geometry objects.
"""

import logging
import re
from typing import Any

from saegim.services.docir import ElementIR, Geometry, PageIR

logger = logging.getLogger(__name__)

_IMAGE_PATTERN = re.compile(r'!\[image\]\(image_\d+\.png\)(\d+),(\d+),(\d+),(\d+)')


class LightOnOcrAdapter:
    """Adapter for LightOnOCR and prompt-free VLM models."""

    def build_messages(
        self,
        image_b64: str,
        mime_type: str,
        page_width: int,  # noqa: ARG002
        page_height: int,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Build API messages with image only (no prompt).

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
        """Parse LightOnOCR response into PageIR.

        Args:
            result: Raw API response dict.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            Parsed PageIR.
        """
        text = _extract_content(result)
        return _parse_lighton_output(text, page_width, page_height)


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


def _normalize_to_pixel(
    x: float,
    y: float,
    page_width: int,
    page_height: int,
) -> tuple[float, float]:
    """Convert 0-1000 normalised coordinates to pixel space.

    Args:
        x: Normalised x coordinate (0-1000).
        y: Normalised y coordinate (0-1000).
        page_width: Image width in pixels.
        page_height: Image height in pixels.

    Returns:
        Tuple of (x_px, y_px) in pixel space.
    """
    return (x * page_width / 1000.0, y * page_height / 1000.0)


def _parse_lighton_output(
    text: str,
    page_width: int,
    page_height: int,
) -> PageIR:
    """Parse LightOnOCR output text into PageIR.

    Processes the output line-by-line:
    - ``![image](image_N.png)x1,y1,x2,y2`` lines become figure elements.
    - Consecutive non-image lines are merged into a single text_block element.
    - The full raw text is stored in ``meta['fulltext']``.

    Args:
        text: Raw model output text.
        page_width: Image width in pixels.
        page_height: Image height in pixels.

    Returns:
        PageIR with parsed elements.
    """
    meta: dict[str, Any] = {}
    if text.strip():
        meta['fulltext'] = text

    elements: list[ElementIR] = []
    pending_text_lines: list[str] = []
    order = 0

    def _flush_text() -> None:
        nonlocal order
        if pending_text_lines:
            elements.append(
                ElementIR(
                    id=f'e{order}',
                    kind='text_block',
                    text='\n'.join(pending_text_lines),
                    reading_order=order,
                )
            )
            order += 1
            pending_text_lines.clear()

    for line in text.split('\n'):
        match = _IMAGE_PATTERN.match(line)
        if match:
            _flush_text()
            x1, y1, x2, y2 = (float(match.group(i)) for i in range(1, 5))
            px1, py1 = _normalize_to_pixel(x1, y1, page_width, page_height)
            px2, py2 = _normalize_to_pixel(x2, y2, page_width, page_height)
            elements.append(
                ElementIR(
                    id=f'e{order}',
                    kind='figure',
                    geometry=Geometry(bbox=(px1, py1, px2, py2)),
                    reading_order=order,
                )
            )
            order += 1
        elif line.strip():
            pending_text_lines.append(line)

    _flush_text()

    return PageIR(
        page_id='unknown',
        width_px=page_width,
        height_px=page_height,
        elements=tuple(elements),
        meta=meta,
    )
