"""OmniDocBench exporter for DocIR.

Converts a PageIR intermediate representation into an OmniDocBench-compatible
dict with layout_dets, page_attribute, and extra fields.
"""

from typing import Any

from saegim.services.docir import ElementIR, Geometry, PageIR

# Element kinds that map text to the 'latex' field
_EQUATION_KINDS = frozenset(
    {
        'equation',
        'equation_isolated',
        'equation_caption',
    }
)


def bbox_to_poly(bbox: tuple[float, float, float, float]) -> list[float]:
    """Convert (x1, y1, x2, y2) bbox to 8-float polygon.

    Args:
        bbox: Bounding box as (x1, y1, x2, y2).

    Returns:
        Polygon as [x1,y1, x2,y1, x2,y2, x1,y2].
    """
    x1, y1, x2, y2 = bbox
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def _geometry_to_poly(geometry: Geometry | None) -> list[float]:
    """Convert Geometry to an 8-float polygon list.

    Args:
        geometry: Element geometry, or None.

    Returns:
        Polygon list. Zero polygon if geometry is None or has no spatial data.
    """
    if geometry is None:
        return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    if geometry.polygon is not None:
        # Flatten [(x,y), ...] → [x, y, ...]
        return [coord for point in geometry.polygon for coord in point]

    if geometry.bbox is not None:
        return bbox_to_poly(geometry.bbox)

    return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


def _element_to_det(element: ElementIR, index: int) -> dict[str, Any]:
    """Convert an ElementIR to an OmniDocBench layout_det entry.

    Args:
        element: DocIR element.
        index: Positional index for anno_id.

    Returns:
        OmniDocBench layout_det dict.
    """
    det: dict[str, Any] = {
        'category_type': element.kind,
        'poly': _geometry_to_poly(element.geometry),
        'ignore': False,
        'order': element.reading_order if element.reading_order is not None else index,
        'anno_id': index,
    }

    if element.text:
        if element.kind in _EQUATION_KINDS:
            det['latex'] = element.text
        elif element.kind == 'table':
            det['html'] = element.text
        else:
            det['text'] = element.text

    return det


def export_page(page: PageIR) -> dict[str, Any]:
    """Convert a PageIR to an OmniDocBench-compatible dict.

    Args:
        page: DocIR page intermediate representation.

    Returns:
        Dict with 'layout_dets', 'page_attribute', and 'extra' keys.
    """
    layout_dets = [_element_to_det(element, i) for i, element in enumerate(page.elements)]

    return {
        'layout_dets': layout_dets,
        'page_attribute': {},
        'extra': {'relation': []},
    }
