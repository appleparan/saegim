"""Extraction service for extracting text blocks and images from PDF pages."""

import logging
from typing import Any

import fitz

logger = logging.getLogger(__name__)

# Scale factor matching the image rendering in document_service (2x)
DEFAULT_SCALE = 2.0


def bbox_to_poly(bbox: tuple[float, ...], scale: float) -> list[float]:
    """Convert a bounding box to a 4-corner polygon with coordinate scaling.

    Args:
        bbox: Bounding box as (x0, y0, x1, y1) in PDF coordinates.
        scale: Scale factor to convert PDF coords to image pixel coords.

    Returns:
        Polygon as [x1,y1, x2,y2, x3,y3, x4,y4] in image pixel coordinates.
    """
    x0, y0, x1, y1 = (v * scale for v in bbox[:4])
    return [x0, y0, x1, y0, x1, y1, x0, y1]


def _collect_block_text(block: dict[str, Any]) -> str:
    """Collect all text from a text block's lines and spans.

    Args:
        block: A PyMuPDF text block dict with 'lines' containing 'spans'.

    Returns:
        Concatenated text from all spans, joined by newlines per line.
    """
    lines: list[str] = []
    for line in block.get('lines', []):
        spans_text = ''.join(span.get('text', '') for span in line.get('spans', []))
        if spans_text.strip():
            lines.append(spans_text)
    return '\n'.join(lines)


def extract_page_elements(page: fitz.Page, scale: float = DEFAULT_SCALE) -> dict[str, Any]:
    """Extract text blocks and images from a PDF page as OmniDocBench format.

    Uses PyMuPDF's get_text("dict") for structured block extraction.
    Coordinates are scaled by the given factor to match rendered image pixels.

    Args:
        page: A PyMuPDF Page object.
        scale: Scale factor for coordinate conversion (default 2.0).

    Returns:
        OmniDocBench-compatible annotation data dict with layout_dets,
        page_attribute, and extra fields.
    """
    text_dict = page.get_text('dict')
    blocks = text_dict.get('blocks', [])

    layout_dets: list[dict[str, Any]] = []
    anno_id = 0

    for block in blocks:
        block_type = block.get('type', 0)
        bbox = (block['bbox'][0], block['bbox'][1], block['bbox'][2], block['bbox'][3])

        if block_type == 0:
            # Text block
            text = _collect_block_text(block)
            if not text.strip():
                continue

            layout_dets.append(
                {
                    'category_type': 'text_block',
                    'poly': bbox_to_poly(bbox, scale),
                    'ignore': False,
                    'order': anno_id,
                    'anno_id': anno_id,
                    'text': text,
                }
            )
            anno_id += 1

        elif block_type == 1:
            # Image block
            layout_dets.append(
                {
                    'category_type': 'figure',
                    'poly': bbox_to_poly(bbox, scale),
                    'ignore': False,
                    'order': anno_id,
                    'anno_id': anno_id,
                }
            )
            anno_id += 1

    # Also extract embedded images via get_images for images not in text dict
    _extract_embedded_images(page, scale, layout_dets, anno_id)

    return {
        'layout_dets': layout_dets,
        'page_attribute': {},
        'extra': {'relation': []},
    }


def _extract_embedded_images(
    page: fitz.Page,
    scale: float,
    layout_dets: list[dict[str, Any]],
    start_anno_id: int,
) -> None:
    """Extract embedded images not captured by get_text("dict").

    Adds figure elements to layout_dets for any image whose bbox doesn't
    overlap significantly with existing figure elements.

    Args:
        page: A PyMuPDF Page object.
        scale: Scale factor for coordinate conversion.
        layout_dets: Existing layout elements list (modified in-place).
        start_anno_id: Starting anno_id for new elements.
    """
    existing_figure_bboxes = [el['poly'] for el in layout_dets if el['category_type'] == 'figure']

    anno_id = start_anno_id
    try:
        images = page.get_images(full=True)
    except (ValueError, RuntimeError):
        logger.debug('Could not extract embedded images from page')
        return

    for img in images:
        xref = img[0]
        try:
            img_rects = page.get_image_rects(xref)
        except (ValueError, RuntimeError):
            logger.debug('Could not get rects for image xref=%d', xref)
            continue

        for rect in img_rects:
            if rect.is_empty or rect.is_infinite:
                continue

            bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
            poly = bbox_to_poly(bbox, scale)

            # Skip if this overlaps significantly with an already-found figure
            if _overlaps_existing(poly, existing_figure_bboxes):
                continue

            layout_dets.append(
                {
                    'category_type': 'figure',
                    'poly': poly,
                    'ignore': False,
                    'order': anno_id,
                    'anno_id': anno_id,
                }
            )
            existing_figure_bboxes.append(poly)
            anno_id += 1


def _overlaps_existing(
    poly: list[float],
    existing_polys: list[list[float]],
    threshold: float = 0.5,
) -> bool:
    """Check if a polygon overlaps significantly with any existing polygon.

    Args:
        poly: New polygon [x1,y1, x2,y2, x3,y3, x4,y4].
        existing_polys: List of existing polygons.
        threshold: IoU threshold above which overlap is considered significant.

    Returns:
        True if significant overlap exists.
    """
    x0, y0 = poly[0], poly[1]
    x1, y1 = poly[4], poly[5]
    area = max(0, x1 - x0) * max(0, y1 - y0)
    if area == 0:
        return True  # Zero-area → skip

    for existing in existing_polys:
        ex0, ey0 = existing[0], existing[1]
        ex1, ey1 = existing[4], existing[5]

        ix0 = max(x0, ex0)
        iy0 = max(y0, ey0)
        ix1 = min(x1, ex1)
        iy1 = min(y1, ey1)

        intersection = max(0, ix1 - ix0) * max(0, iy1 - iy0)
        if intersection / area > threshold:
            return True

    return False
