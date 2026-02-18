"""OCR provider factory and common interfaces.

Provides a unified interface for different OCR providers (Gemini, vLLM, MinerU, PyMuPDF).
Each provider extracts structured layout elements from page images and returns
OmniDocBench-compatible dicts.
"""

import logging
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# Structured output prompt for VLM-based OCR providers (Gemini, vLLM)
STRUCTURED_OCR_PROMPT = (
    'You are a document layout analysis expert. '
    'Analyze this document page image and extract all layout elements.\n\n'
    'For each element, provide:\n'
    '1. category_type: One of: title, text_block, figure, figure_caption, '
    'figure_footnote, table, table_caption, table_footnote, '
    'equation_isolated, equation_caption, header, footer, page_number, '
    'page_footnote, abandon, code_txt, reference\n'
    '2. bbox: Bounding box as [x1, y1, x2, y2] in pixel coordinates\n'
    '3. text: The text content (empty string for figures)\n'
    '4. order: Reading order (0-based)\n\n'
    'Respond ONLY with a valid JSON array. Example:\n'
    '[{{"category_type": "title", "bbox": [x1, y1, x2, y2], '
    '"text": "extracted text", "order": 0}}]\n\n'
    'Important:\n'
    '- Coordinates: pixel values for image '
    '(width: {width}, height: {height})\n'
    '- Extract ALL visible elements\n'
    '- For tables, set category_type to "table"\n'
    '- For equations, use "equation_isolated" with LaTeX if possible\n'
    '- Maintain correct reading order\n'
    '- Return [] if no elements are found'
)


class OcrProvider(Protocol):
    """Protocol for OCR providers."""

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Extract structured layout elements from a page image.

        Args:
            image_path: Path to the page image file.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            OmniDocBench-compatible dict with layout_dets, page_attribute, extra.
        """
        ...


def bbox_to_poly(bbox: list[float]) -> list[float]:
    """Convert [x1, y1, x2, y2] bbox to 8-float polygon.

    Args:
        bbox: Bounding box [x1, y1, x2, y2].

    Returns:
        8-float polygon [x1,y1, x2,y1, x2,y2, x1,y2].
    """
    x1, y1, x2, y2 = bbox
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def build_omnidocbench_page(
    elements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build an OmniDocBench page dict from extracted elements.

    Args:
        elements: List of extracted element dicts with category_type, bbox, text, order.

    Returns:
        OmniDocBench-compatible page dict.
    """
    layout_dets = []
    for i, elem in enumerate(elements):
        bbox = elem.get('bbox', [0, 0, 0, 0])
        poly = bbox_to_poly(bbox)
        det: dict[str, Any] = {
            'category_type': elem.get('category_type', 'text_block'),
            'poly': poly,
            'ignore': False,
            'order': elem.get('order', i),
            'anno_id': i,
        }
        text = elem.get('text')
        if text:
            det['text'] = text
        latex = elem.get('latex')
        if latex:
            det['latex'] = latex
        html = elem.get('html')
        if html:
            det['html'] = html
        layout_dets.append(det)

    return {
        'layout_dets': layout_dets,
        'page_attribute': {},
        'extra': {'relation': []},
    }


def get_ocr_provider(ocr_config: dict[str, Any]) -> OcrProvider:
    """Get an OCR provider instance based on configuration.

    Args:
        ocr_config: OCR configuration dict with 'provider' key.

    Returns:
        OcrProvider instance for the specified provider.

    Raises:
        ValueError: If provider is unknown.
    """
    provider = ocr_config.get('provider', 'mineru')

    if provider == 'gemini':
        from saegim.services.gemini_ocr_service import GeminiOcrProvider

        gemini_config = ocr_config.get('gemini', {})
        return GeminiOcrProvider(
            api_key=gemini_config['api_key'],
            model=gemini_config.get('model', 'gemini-2.0-flash'),
        )

    if provider == 'vllm':
        from saegim.services.vllm_ocr_service import VllmOcrProvider

        vllm_config = ocr_config.get('vllm', {})
        return VllmOcrProvider(
            host=vllm_config.get('host', 'localhost'),
            port=vllm_config.get('port', 8000),
            model=vllm_config.get('model', 'Qwen/Qwen2.5-VL-72B-Instruct'),
        )

    msg = f"Unknown OCR provider: '{provider}'. Use 'gemini' or 'vllm'."
    raise ValueError(msg)
