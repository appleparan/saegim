"""MinerU-based PDF extraction service for structured layout detection.

Calls the saegim-mineru HTTP service to extract content_list, then converts
the result to OmniDocBench-compatible format for storage in pages.auto_extracted_data.

The actual MinerU code runs in a separate AGPL-licensed container; this module
only contains the HTTP client and the OmniDocBench conversion logic (Apache 2.0).
"""

import logging
from pathlib import Path
from typing import Any

import httpx

from saegim.api.settings import get_settings

logger = logging.getLogger(__name__)

# MinerU type → OmniDocBench category_type mapping
_CATEGORY_MAP: dict[str, str] = {
    'text': 'text_block',
    'image': 'figure',
    'table': 'table',
    'equation': 'equation_isolated',
    'code': 'code_txt',
    'list': 'text_block',
    'header': 'header',
    'footer': 'footer',
    'page_number': 'page_number',
    'aside_text': 'abandon',
    'page_footnote': 'page_footnote',
}


def _map_category_type(item: dict[str, Any]) -> str:
    """Map MinerU content type to OmniDocBench category_type.

    Args:
        item: A MinerU content_list entry with 'type' and optional 'text_level'.

    Returns:
        OmniDocBench category_type string.
    """
    mineru_type = item.get('type', 'text')
    text_level = item.get('text_level', 0)

    # text with text_level >= 1 is a title/heading
    if mineru_type == 'text' and text_level and text_level >= 1:
        return 'title'

    return _CATEGORY_MAP.get(mineru_type, 'text_block')


def _bbox_to_poly(bbox: list[float], width: int, height: int) -> list[float]:
    """Convert MinerU 0-1000 normalized bbox to pixel coordinate polygon.

    Args:
        bbox: Bounding box [x0, y0, x1, y1] normalized to 0-1000 range.
        width: Page image width in pixels (2x rendered).
        height: Page image height in pixels (2x rendered).

    Returns:
        8-float polygon [x0,y0, x1,y0, x1,y1, x0,y1] in pixel coordinates.
    """
    x0 = bbox[0] / 1000.0 * width
    y0 = bbox[1] / 1000.0 * height
    x1 = bbox[2] / 1000.0 * width
    y1 = bbox[3] / 1000.0 * height
    return [x0, y0, x1, y0, x1, y1, x0, y1]


def _build_element(
    category_type: str,
    poly: list[float],
    anno_id: int,
    *,
    text: str | None = None,
    latex: str | None = None,
    html: str | None = None,
) -> dict[str, Any]:
    """Build an OmniDocBench layout element dict.

    Args:
        category_type: Element category (e.g. 'text_block', 'figure').
        poly: 8-float polygon in pixel coordinates.
        anno_id: Sequential annotation ID.
        text: Optional text content.
        latex: Optional LaTeX content (for equations).
        html: Optional HTML content (for tables).

    Returns:
        OmniDocBench-compatible layout element dict.
    """
    element: dict[str, Any] = {
        'category_type': category_type,
        'poly': poly,
        'ignore': False,
        'order': anno_id,
        'anno_id': anno_id,
    }
    if text is not None:
        element['text'] = text
    if latex is not None:
        element['latex'] = latex
    if html is not None:
        element['html'] = html
    return element


def _extract_caption_elements(
    item: dict[str, Any],
    poly: list[float],
    anno_id: int,
    category_prefix: str,
) -> list[dict[str, Any]]:
    """Extract caption and footnote sub-elements from a content_list item.

    Args:
        item: MinerU content_list entry (image or table type).
        poly: Parent element's polygon (used as fallback for captions).
        anno_id: Starting annotation ID for generated elements.
        category_prefix: 'figure' or 'table' to form caption category names.

    Returns:
        List of caption/footnote OmniDocBench elements.
    """
    elements: list[dict[str, Any]] = []

    caption_key = f'{category_prefix}_caption' if category_prefix == 'table' else 'image_caption'
    footnote_key = f'{category_prefix}_footnote' if category_prefix == 'table' else None

    captions = item.get(caption_key, [])
    if captions:
        caption_text = '\n'.join(captions) if isinstance(captions, list) else str(captions)
        if caption_text.strip():
            elements.append(
                _build_element(
                    f'{category_prefix}_caption',
                    poly,
                    anno_id,
                    text=caption_text,
                )
            )
            anno_id += 1

    if footnote_key:
        footnotes = item.get(footnote_key, [])
        if footnotes:
            footnote_text = '\n'.join(footnotes) if isinstance(footnotes, list) else str(footnotes)
            if footnote_text.strip():
                elements.append(
                    _build_element(
                        f'{category_prefix}_footnote',
                        poly,
                        anno_id,
                        text=footnote_text,
                    )
                )

    return elements


def content_list_to_omnidocbench(
    content_list: list[dict[str, Any]],
    page_dimensions: dict[int, tuple[int, int]],
) -> dict[int, dict[str, Any]]:
    """Convert MinerU content_list to per-page OmniDocBench format.

    Args:
        content_list: MinerU content_list.json output (reading-order sorted).
        page_dimensions: Mapping of page_idx (0-based) to (width, height) in pixels.

    Returns:
        Mapping of page_idx to OmniDocBench dict with layout_dets, page_attribute, extra.
    """
    # Initialize result for all known pages
    result: dict[int, dict[str, Any]] = {}
    for page_idx in page_dimensions:
        result[page_idx] = {
            'layout_dets': [],
            'page_attribute': {},
            'extra': {'relation': []},
        }

    # Track per-page anno_id counters
    anno_counters: dict[int, int] = dict.fromkeys(page_dimensions, 0)

    for item in content_list:
        page_idx = item.get('page_idx', 0)
        if page_idx not in page_dimensions:
            logger.warning('Skipping item with unknown page_idx=%d', page_idx)
            continue

        width, height = page_dimensions[page_idx]
        bbox = item.get('bbox', [0, 0, 0, 0])
        poly = _bbox_to_poly(bbox, width, height)
        category_type = _map_category_type(item)
        anno_id = anno_counters[page_idx]

        # Build the main element
        text = item.get('text')
        latex = None
        html = None

        if category_type == 'equation_isolated' and item.get('text_format') == 'latex':
            latex = text
            text = None

        if category_type == 'table':
            html = item.get('table_body')

        element = _build_element(category_type, poly, anno_id, text=text, latex=latex, html=html)
        result[page_idx]['layout_dets'].append(element)
        anno_counters[page_idx] += 1

        # Extract caption/footnote sub-elements for images and tables
        if category_type == 'figure':
            captions = _extract_caption_elements(item, poly, anno_counters[page_idx], 'figure')
            for cap in captions:
                result[page_idx]['layout_dets'].append(cap)
                anno_counters[page_idx] += 1

        elif category_type == 'table':
            captions = _extract_caption_elements(item, poly, anno_counters[page_idx], 'table')
            for cap in captions:
                result[page_idx]['layout_dets'].append(cap)
                anno_counters[page_idx] += 1

    return result


def _call_mineru_api(
    pdf_path: Path,
    language: str,
    backend: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Call the saegim-mineru HTTP service to extract content_list.

    Args:
        pdf_path: Path to the PDF file (accessible via shared volume).
        language: OCR language setting.
        backend: MinerU parsing backend name.
        output_dir: Directory for MinerU output files (shared volume).

    Returns:
        content_list entries from the MinerU service.

    Raises:
        RuntimeError: If the HTTP request fails.
    """
    settings = get_settings()
    url = f'{settings.mineru_api_url}/api/v1/extract'

    try:
        with httpx.Client(timeout=httpx.Timeout(1800.0)) as client:
            response = client.post(
                url,
                json={
                    'pdf_path': str(pdf_path),
                    'language': language,
                    'backend': backend,
                    'output_dir': str(output_dir),
                },
            )
            response.raise_for_status()
            return response.json()['content_list']
    except httpx.HTTPStatusError as exc:
        msg = f'MinerU API returned {exc.response.status_code}: {exc.response.text}'
        raise RuntimeError(msg) from exc
    except httpx.RequestError as exc:
        msg = f'MinerU API request failed: {exc}'
        raise RuntimeError(msg) from exc


def extract_document(
    pdf_path: Path,
    language: str = 'korean',
    backend: str = 'pipeline',
    output_dir: Path | None = None,
    page_dimensions: dict[int, tuple[int, int]] | None = None,
) -> dict[int, dict[str, Any]]:
    """Extract structured layout elements from a PDF using MinerU.

    Calls the saegim-mineru HTTP service and converts the results to
    per-page OmniDocBench format.

    Args:
        pdf_path: Path to the PDF file.
        language: OCR language setting (default 'korean').
        backend: MinerU parsing backend ('pipeline', 'hybrid-auto-engine', etc.).
        output_dir: Directory for MinerU output files (images, etc.).
        page_dimensions: Mapping of page_idx (0-based) to (width, height) in pixels.
            Required for coordinate conversion.

    Returns:
        Mapping of page_idx (0-based) to OmniDocBench dict.

    Raises:
        RuntimeError: If MinerU extraction fails.
    """
    if output_dir is None:
        output_dir = pdf_path.parent / f'{pdf_path.stem}_mineru_output'
    output_dir.mkdir(parents=True, exist_ok=True)

    if page_dimensions is None:
        page_dimensions = {}

    try:
        content_list = _call_mineru_api(pdf_path, language, backend, output_dir)
    except Exception as exc:
        msg = f'MinerU extraction failed for {pdf_path}: {exc}'
        logger.exception(msg)
        raise RuntimeError(msg) from exc

    # If no page dimensions provided, infer from content_list
    if not page_dimensions:
        page_indices = {item.get('page_idx', 0) for item in content_list}
        # Use default dimensions (will be overridden by caller in production)
        page_dimensions = dict.fromkeys(page_indices, (1, 1))
        logger.warning('No page_dimensions provided; coordinates will not be properly scaled')

    return content_list_to_omnidocbench(content_list, page_dimensions)
