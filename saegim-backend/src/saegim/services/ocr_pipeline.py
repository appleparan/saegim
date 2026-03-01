"""2-stage OCR pipeline orchestrator.

Combines a pluggable layout detector with text-only OCR providers
(Gemini, vLLM, or built-in text) to produce OmniDocBench pages.
"""

import io
import logging
from pathlib import Path
from typing import Any, Protocol

from PIL import Image

from saegim.services.layout_types import LayoutDetector, LayoutRegion
from saegim.services.ocr_provider import bbox_to_poly

logger = logging.getLogger(__name__)


class TextOcrProvider(Protocol):
    """Protocol for text-only OCR providers (2-stage pipeline).

    Receives a cropped region image and returns extracted text.
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


class OcrPipeline:
    """2-stage OCR pipeline: layout detection + text extraction.

    Stage 1: Layout detector finds regions (bounding boxes + categories).
    Stage 2: Text OCR provider extracts text from each cropped region.
    """

    def __init__(
        self,
        layout_detector: LayoutDetector,
        text_provider: TextOcrProvider | None = None,
        *,
        use_builtin_ocr: bool = False,
    ) -> None:
        """Initialize the 2-stage OCR pipeline.

        Args:
            layout_detector: Layout detection backend (e.g. DoclingLayoutDetector).
            text_provider: Text-only OCR provider (Gemini or vLLM).
            use_builtin_ocr: If True, use built-in text from layout results.
        """
        self._layout_detector = layout_detector
        self._text_provider = text_provider
        self._use_builtin_ocr = use_builtin_ocr

    def extract_page(
        self,
        image_path: Path,
        _page_width: int,
        _page_height: int,
    ) -> dict[str, Any]:
        """Run the 2-stage pipeline on a page image.

        Args:
            image_path: Path to the page image file.
            _page_width: Image width in pixels (unused, kept for interface compat).
            _page_height: Image height in pixels (unused, kept for interface compat).

        Returns:
            OmniDocBench-compatible dict with layout_dets, page_attribute, extra.
        """
        regions = self._layout_detector.detect_layout(image_path)
        logger.info('Detected %d layout regions in %s', len(regions), image_path.name)

        if not regions:
            return {
                'layout_dets': [],
                'page_attribute': {},
                'extra': {'relation': []},
            }

        image = Image.open(image_path)

        layout_dets = []
        for i, region in enumerate(regions):
            text = self._extract_region_text(image, region)
            det = _build_layout_det(region, text, order=i)
            layout_dets.append(det)

        image.close()

        return {
            'layout_dets': layout_dets,
            'page_attribute': {},
            'extra': {'relation': []},
        }

    def _extract_region_text(
        self,
        image: Image.Image,
        region: LayoutRegion,
    ) -> str:
        """Extract text from a single layout region.

        Args:
            image: Full page PIL Image.
            region: Layout region with bounding box and category.

        Returns:
            Extracted text string.
        """
        if self._use_builtin_ocr:
            return region.text or ''

        if self._text_provider is None:
            return ''

        # Skip non-text regions (figures)
        if region.category == 'figure':
            return ''

        cropped_bytes = _crop_region(image, region.bbox)
        return self._text_provider.extract_text(cropped_bytes, region.category)


def _crop_region(
    image: Image.Image,
    bbox: tuple[float, float, float, float],
) -> bytes:
    """Crop a region from an image and return as PNG bytes.

    Args:
        image: Full page PIL Image.
        bbox: Bounding box as (x1, y1, x2, y2) in pixels.

    Returns:
        Cropped image as PNG bytes, empty bytes if region has zero area.
    """
    x1, y1, x2, y2 = bbox
    # Clamp to image bounds
    x1 = max(0, min(x1, image.width))
    y1 = max(0, min(y1, image.height))
    x2 = max(0, min(x2, image.width))
    y2 = max(0, min(y2, image.height))

    ix1, iy1, ix2, iy2 = int(x1), int(y1), int(x2), int(y2)
    if ix2 <= ix1 or iy2 <= iy1:
        return b''

    cropped = image.crop((ix1, iy1, ix2, iy2))
    buf = io.BytesIO()
    cropped.save(buf, format='PNG')
    return buf.getvalue()


def _build_layout_det(
    region: LayoutRegion,
    text: str,
    *,
    order: int,
) -> dict[str, Any]:
    """Build an OmniDocBench layout_det from a LayoutRegion.

    Args:
        region: Layout region with bounding box and category.
        text: Extracted text for this region.
        order: Reading order index.

    Returns:
        OmniDocBench-compatible layout_det dict.
    """
    poly = bbox_to_poly(list(region.bbox))
    det: dict[str, Any] = {
        'category_type': region.category,
        'poly': poly,
        'ignore': False,
        'order': order,
        'anno_id': order,
    }
    if text:
        if region.category == 'equation_isolated':
            det['latex'] = text
        elif region.category == 'table':
            det['html'] = text
        else:
            det['text'] = text
    return det
