"""PP-StructureV3 HTTP client for document layout detection.

Communicates with a PP-StructureV3 server to detect layout regions
(bounding boxes + categories) from document page images.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# PP-StructureV3 category → OmniDocBench category mapping
_PP_CATEGORY_MAP: dict[str, str] = {
    'title': 'title',
    'text': 'text_block',
    'figure': 'figure',
    'figure_caption': 'figure_caption',
    'table': 'table',
    'table_caption': 'table_caption',
    'header': 'header',
    'footer': 'footer',
    'reference': 'reference',
    'equation': 'equation_isolated',
    'seal': 'abandon',
    'formula': 'equation_isolated',
    'doc_title': 'title',
    'paragraph_title': 'title',
    'abstract': 'text_block',
    'content': 'text_block',
    'number': 'page_number',
    'code': 'code_txt',
}


@dataclass(frozen=True)
class LayoutRegion:
    """A detected layout region from PP-StructureV3.

    Attributes:
        bbox: Bounding box as (x1, y1, x2, y2) pixel coordinates.
        category: OmniDocBench category type.
        score: Detection confidence score.
        text: Recognized text (only present in PP-OCR mode).
    """

    bbox: tuple[float, float, float, float]
    category: str
    score: float
    text: str | None = None


def _map_category(pp_category: str) -> str:
    """Map PP-StructureV3 category to OmniDocBench category.

    Args:
        pp_category: Category string from PP-StructureV3.

    Returns:
        Corresponding OmniDocBench category type.
    """
    return _PP_CATEGORY_MAP.get(pp_category.lower(), 'text_block')


class PpstructureClient:
    """HTTP client for PP-StructureV3 server.

    Sends page images to the PP-StructureV3 API and returns
    detected layout regions.

    Args:
        host: PP-StructureV3 server host.
        port: PP-StructureV3 server port.
    """

    def __init__(self, host: str, port: int) -> None:
        """Initialize the PP-StructureV3 client."""
        self._base_url = f'http://{host}:{port}'
        self._timeout = httpx.Timeout(120.0, connect=10.0)

    def detect_layout(self, image_path: Path) -> list[LayoutRegion]:
        """Detect layout regions from a page image.

        Args:
            image_path: Path to the page image file.

        Returns:
            List of detected layout regions.

        Raises:
            httpx.HTTPStatusError: If the server returns an error.
            httpx.RequestError: If connection fails.
        """
        url = f'{self._base_url}/api/v1/predict'

        with httpx.Client(timeout=self._timeout) as client:
            with image_path.open('rb') as f:
                files = {'file': (image_path.name, f, 'image/png')}
                response = client.post(url, files=files)
            response.raise_for_status()
            data = response.json()

        return _parse_response(data)


def _parse_response(data: dict[str, Any]) -> list[LayoutRegion]:
    """Parse PP-StructureV3 API response into LayoutRegion list.

    Args:
        data: JSON response from the PP-StructureV3 API.

    Returns:
        List of LayoutRegion instances.
    """
    regions: list[LayoutRegion] = []

    results = data.get('results', data.get('result', []))
    if isinstance(results, dict):
        results = results.get('regions', [])

    for item in results:
        bbox_raw = item.get('bbox', item.get('box', [0, 0, 0, 0]))
        # Handle both [x1,y1,x2,y2] and [[x1,y1],[x2,y2]] formats
        if bbox_raw and isinstance(bbox_raw[0], list):
            x1, y1 = bbox_raw[0]
            x2, y2 = bbox_raw[2] if len(bbox_raw) > 2 else bbox_raw[1]
            bbox = (float(x1), float(y1), float(x2), float(y2))
        else:
            bbox = tuple(float(v) for v in bbox_raw[:4])

        category = _map_category(
            item.get('type', item.get('label', item.get('category', 'text'))),
        )
        score = float(item.get('score', item.get('confidence', 0.0)))
        text = item.get('text') or item.get('rec_text')

        regions.append(
            LayoutRegion(
                bbox=bbox,  # type: ignore[arg-type]
                category=category,
                score=score,
                text=text,
            )
        )

    return regions
