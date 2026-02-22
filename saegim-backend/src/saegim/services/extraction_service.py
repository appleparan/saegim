"""Extraction service for extracting text blocks and images from PDF pages.

Uses pdfminer.six for structured layout extraction with bounding boxes.
Coordinates are converted from pdfminer's bottom-left origin to top-left
origin, then scaled to match rendered image pixels.
"""

import logging
from pathlib import Path
from typing import Any

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTFigure, LTImage, LTTextBox

logger = logging.getLogger(__name__)

# Scale factor matching the image rendering in document_service (2x)
DEFAULT_SCALE = 2.0


def _flip_bbox(
    bbox: tuple[float, float, float, float],
    page_height: float,
) -> tuple[float, float, float, float]:
    """Convert pdfminer bottom-left origin bbox to top-left origin.

    Args:
        bbox: (x0, y0, x1, y1) in bottom-left origin.
        page_height: Height of the page in PDF units.

    Returns:
        (x0, y0, x1, y1) in top-left origin.
    """
    x0, y0_bl, x1, y1_bl = bbox
    new_y0 = page_height - y1_bl
    new_y1 = page_height - y0_bl
    return (x0, new_y0, x1, new_y1)


def bbox_to_poly(bbox: tuple[float, ...], scale: float) -> list[float]:
    """Convert a bounding box to a 4-corner polygon with coordinate scaling.

    Args:
        bbox: Bounding box as (x0, y0, x1, y1) in top-left origin coordinates.
        scale: Scale factor to convert PDF coords to image pixel coords.

    Returns:
        Polygon as [x1,y1, x2,y2, x3,y3, x4,y4] in image pixel coordinates.
    """
    x0, y0, x1, y1 = (v * scale for v in bbox[:4])
    return [x0, y0, x1, y0, x1, y1, x0, y1]


def extract_page_elements(
    pdf_path: Path,
    page_no: int,
    scale: float = DEFAULT_SCALE,
) -> dict[str, Any]:
    """Extract text blocks and images from a PDF page as OmniDocBench format.

    Uses pdfminer.six's extract_pages() for structured layout extraction.
    Coordinates are converted from pdfminer's bottom-left origin to
    top-left origin, then scaled to match rendered image pixels.

    Args:
        pdf_path: Path to the PDF file.
        page_no: Zero-based page index.
        scale: Scale factor for coordinate conversion (default 2.0).

    Returns:
        OmniDocBench-compatible annotation data dict with layout_dets,
        page_attribute, and extra fields.
    """
    laparams = LAParams()
    layout_dets: list[dict[str, Any]] = []
    anno_id = 0

    for lt_page in extract_pages(str(pdf_path), page_numbers=[page_no], laparams=laparams):
        page_height = lt_page.height

        for element in lt_page:
            if isinstance(element, LTTextBox):
                text = element.get_text().strip()
                if not text:
                    continue

                bbox = _flip_bbox(element.bbox, page_height)
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

            elif isinstance(element, (LTFigure, LTImage)):
                bbox = _flip_bbox(element.bbox, page_height)
                poly = bbox_to_poly(bbox, scale)

                # Skip zero-area figures
                if _is_zero_area(poly):
                    continue

                # Skip if overlaps with an existing figure
                existing_figure_polys = [
                    el['poly'] for el in layout_dets if el['category_type'] == 'figure'
                ]
                if _overlaps_existing(poly, existing_figure_polys):
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
                anno_id += 1

    return {
        'layout_dets': layout_dets,
        'page_attribute': {},
        'extra': {'relation': []},
    }


def _is_zero_area(poly: list[float]) -> bool:
    """Check if a polygon has zero area.

    Args:
        poly: Polygon [x1,y1, x2,y2, x3,y3, x4,y4].

    Returns:
        True if area is zero.
    """
    x0, y0 = poly[0], poly[1]
    x1, y1 = poly[4], poly[5]
    area = max(0, x1 - x0) * max(0, y1 - y0)
    return area == 0


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
