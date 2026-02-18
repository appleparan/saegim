"""OCR provider factory and common interfaces.

Provides a unified interface for different OCR providers (Gemini, vLLM).
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
    """Protocol for OCR providers (full-page layout + text)."""

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


class TextOcrProvider(Protocol):
    """Protocol for text-only OCR providers (2-stage pipeline).

    Used with PP-StructureV3 layout detection: receives a cropped region
    image and returns extracted text.
    """

    def extract_text(self, image_bytes: bytes, category_hint: str = '') -> str:
        """Extract text from a cropped region image.

        Args:
            image_bytes: Raw image bytes of the cropped region.
            category_hint: OmniDocBench category hint (e.g. 'table', 'equation_isolated').

        Returns:
            Extracted text string.
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
    """Get an OCR provider instance based on 2-stage configuration.

    Args:
        ocr_config: OCR configuration dict with 'ocr_provider' key.

    Returns:
        OcrProvider instance for the specified provider.

    Raises:
        ValueError: If provider is unknown.
    """
    provider = ocr_config.get('ocr_provider', '')

    if provider == 'gemini':
        from saegim.services.gemini_ocr_service import GeminiOcrProvider

        gemini_config = ocr_config.get('gemini', {})
        return GeminiOcrProvider(
            api_key=gemini_config['api_key'],
            model=gemini_config.get('model', 'gemini-2.0-flash'),
        )

    if provider == 'olmocr':
        from saegim.services.vllm_ocr_service import VllmOcrProvider

        vllm_config = ocr_config.get('vllm', {})
        return VllmOcrProvider(
            host=vllm_config.get('host', 'localhost'),
            port=vllm_config.get('port', 8000),
            model=vllm_config.get('model', 'allenai/olmOCR-2-7B-1025'),
        )

    msg = f"Unknown OCR provider: '{provider}'. Use 'gemini' or 'olmocr'."
    raise ValueError(msg)


# --- Text-only OCR for 2-stage pipeline ---

# Category-specific prompts for text-only extraction
_TEXT_PROMPT_DEFAULT = (
    'Read all text in this image and return it exactly as written. '
    'Preserve line breaks and paragraph structure. '
    'Return only the extracted text, nothing else.'
)

_TEXT_PROMPT_TABLE = (
    'This image contains a table. '
    'Extract the table content as a markdown table. '
    'Use | for column separators and --- for header rows. '
    'Return only the markdown table, nothing else.'
)

_TEXT_PROMPT_EQUATION = (
    'This image contains a mathematical equation. '
    'Convert it to LaTeX notation. '
    'Return only the LaTeX expression (no $$ delimiters), nothing else.'
)

_TEXT_PROMPT_CODE = (
    'This image contains source code. '
    'Extract the code exactly as written, preserving indentation. '
    'Return only the code, nothing else.'
)

_CATEGORY_PROMPT_MAP: dict[str, str] = {
    'table': _TEXT_PROMPT_TABLE,
    'equation_isolated': _TEXT_PROMPT_EQUATION,
    'code_txt': _TEXT_PROMPT_CODE,
}


def get_text_prompt(category_hint: str = '') -> str:
    """Get the appropriate text extraction prompt for a category.

    Args:
        category_hint: OmniDocBench category type.

    Returns:
        Prompt string for text extraction.
    """
    return _CATEGORY_PROMPT_MAP.get(category_hint, _TEXT_PROMPT_DEFAULT)


def get_text_ocr_provider(ocr_config: dict[str, Any]) -> TextOcrProvider:
    """Get a text-only OCR provider instance for the 2-stage pipeline.

    Args:
        ocr_config: OCR configuration dict with 'ocr_provider' key.

    Returns:
        TextOcrProvider instance.

    Raises:
        ValueError: If provider is unknown or unsupported for text extraction.
    """
    provider = ocr_config.get('ocr_provider', '')

    if provider == 'gemini':
        from saegim.services.gemini_ocr_service import GeminiTextOcrProvider

        gemini_config = ocr_config.get('gemini', {})
        return GeminiTextOcrProvider(
            api_key=gemini_config['api_key'],
            model=gemini_config.get('model', 'gemini-2.0-flash'),
        )

    if provider == 'olmocr':
        from saegim.services.vllm_ocr_service import VllmTextOcrProvider

        vllm_config = ocr_config.get('vllm', {})
        return VllmTextOcrProvider(
            host=vllm_config.get('host', 'localhost'),
            port=vllm_config.get('port', 8000),
            model=vllm_config.get('model', 'allenai/olmOCR-2-7B-1025'),
        )

    msg = f"Unknown text OCR provider: '{provider}'. Use 'gemini' or 'olmocr'."
    raise ValueError(msg)
