"""Text extraction service for user-drawn regions.

Crops a region from a page image and sends it to the configured
text OCR provider (Gemini or vLLM) for text extraction.
"""

import io
import logging
import uuid
from pathlib import Path
from typing import Any

import asyncpg
from PIL import Image

from saegim.repositories import page_repo, project_repo
from saegim.services.gemini_ocr_service import GeminiTextOcrProvider
from saegim.services.ocr_pipeline import TextOcrProvider
from saegim.services.vllm_ocr_service import VllmTextOcrProvider

logger = logging.getLogger(__name__)


class TextExtractionError(Exception):
    """Raised when text extraction fails."""


class NoTextProviderError(Exception):
    """Raised when no text OCR provider is available for the project."""


def poly_to_bbox(poly: list[float]) -> tuple[float, float, float, float]:
    """Convert 8-point polygon to axis-aligned bounding box.

    Args:
        poly: 8-float polygon [x1,y1, x2,y1, x2,y2, x1,y2].

    Returns:
        Bounding box as (x1, y1, x2, y2).
    """
    xs = poly[0::2]
    ys = poly[1::2]
    return (min(xs), min(ys), max(xs), max(ys))


def crop_region(
    image: Image.Image,
    bbox: tuple[float, float, float, float],
) -> bytes:
    """Crop a region from an image and return as PNG bytes.

    Args:
        image: Full page PIL Image.
        bbox: Bounding box as (x1, y1, x2, y2) in pixels.

    Returns:
        Cropped image as PNG bytes.

    Raises:
        TextExtractionError: If the region has zero or negative area.
    """
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(x1, image.width))
    y1 = max(0, min(y1, image.height))
    x2 = max(0, min(x2, image.width))
    y2 = max(0, min(y2, image.height))

    ix1, iy1, ix2, iy2 = int(x1), int(y1), int(x2), int(y2)
    if ix2 <= ix1 or iy2 <= iy1:
        msg = f'Region has zero area: ({ix1}, {iy1}, {ix2}, {iy2})'
        raise TextExtractionError(msg)

    cropped = image.crop((ix1, iy1, ix2, iy2))
    buf = io.BytesIO()
    cropped.save(buf, format='PNG')
    return buf.getvalue()


def build_text_provider(ocr_config: dict[str, Any]) -> TextOcrProvider | None:
    """Build a text-only OCR provider from project OCR configuration.

    Args:
        ocr_config: Project OCR configuration dict with 'engine_type' key.

    Returns:
        TextOcrProvider instance, or None if the engine type does not support
        region-level text extraction.
    """
    engine_type = ocr_config.get('engine_type', '')

    if engine_type == 'split_pipeline':
        return _build_from_split_pipeline(ocr_config.get('split_pipeline', {}))

    if engine_type == 'commercial_api':
        return _build_from_commercial_api(ocr_config.get('commercial_api', {}))

    if engine_type == 'integrated_server':
        return _build_from_integrated_server(ocr_config.get('integrated_server', {}))

    # pdfminer and unknown engines have no text extraction capability
    return None


def extract_text_from_region(
    image_path: Path,
    poly: list[float],
    category_type: str,
    text_provider: TextOcrProvider,
) -> str:
    """Extract text from a region of a page image.

    Args:
        image_path: Path to the page image file.
        poly: 8-float polygon defining the region.
        category_type: OmniDocBench category type for prompt selection.
        text_provider: Text-only OCR provider.

    Returns:
        Extracted text string.

    Raises:
        TextExtractionError: If cropping or OCR fails.
    """
    bbox = poly_to_bbox(poly)

    try:
        image = Image.open(image_path)
    except (OSError, FileNotFoundError) as exc:
        msg = f'Failed to open image: {image_path}'
        raise TextExtractionError(msg) from exc

    try:
        cropped_bytes = crop_region(image, bbox)
    finally:
        image.close()

    try:
        return text_provider.extract_text(cropped_bytes, category_type)
    except RuntimeError as exc:
        msg = f'OCR provider failed: {exc}'
        raise TextExtractionError(msg) from exc


async def resolve_text_provider(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
) -> tuple[Path, TextOcrProvider]:
    """Resolve the text OCR provider and image path for a page.

    Looks up the page's project OCR config and builds the appropriate
    text provider.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        Tuple of (image_path, text_provider).

    Raises:
        LookupError: If the page is not found.
        NoTextProviderError: If no text provider is available.
    """
    page = await page_repo.get_by_id_with_context(pool, page_id)
    if page is None:
        msg = f'Page not found: {page_id}'
        raise LookupError(msg)

    image_path = Path(page['image_path'])
    project_id = page['project_id']

    ocr_config = await project_repo.get_ocr_config(pool, project_id)
    if not ocr_config or not ocr_config.get('engine_type'):
        ocr_config = {'engine_type': 'pdfminer'}

    text_provider = build_text_provider(ocr_config)
    if text_provider is None:
        engine_type = ocr_config.get('engine_type', 'unknown')
        msg = (
            f"Engine type '{engine_type}' does not support region text extraction. "
            f'Configure a split_pipeline, commercial_api, or integrated_server engine.'
        )
        raise NoTextProviderError(msg)

    return (image_path, text_provider)


def _build_from_split_pipeline(
    config: dict[str, Any],
) -> GeminiTextOcrProvider | VllmTextOcrProvider | None:
    """Build text provider from split_pipeline config.

    Args:
        config: split_pipeline configuration dict.

    Returns:
        Text OCR provider, or None if config is invalid.
    """
    ocr_provider = config.get('ocr_provider', '')
    ocr_config = {
        k.removeprefix('ocr_'): v
        for k, v in config.items()
        if k.startswith('ocr_') and k != 'ocr_provider'
    }
    return _create_text_provider(ocr_provider, ocr_config)


def _build_from_commercial_api(
    config: dict[str, Any],
) -> GeminiTextOcrProvider | VllmTextOcrProvider | None:
    """Build text provider from commercial_api config.

    Args:
        config: commercial_api configuration dict.

    Returns:
        Text OCR provider, or None if config is invalid.
    """
    provider = config.get('provider', '')
    return _create_text_provider(provider, config)


def _build_from_integrated_server(
    config: dict[str, Any],
) -> VllmTextOcrProvider | None:
    """Build text provider from integrated_server config.

    PP-StructureV3 models (PP-* prefix) do not support standalone text extraction.

    Args:
        config: integrated_server configuration dict.

    Returns:
        VllmTextOcrProvider or None for PP-StructureV3 models.
    """
    model = config.get('model', '')
    if model.startswith('PP-'):
        return None

    return VllmTextOcrProvider(
        host=config.get('host', 'localhost'),
        port=config.get('port', 8000),
        model=model,
    )


def _create_text_provider(
    provider: str,
    config: dict[str, Any],
) -> GeminiTextOcrProvider | VllmTextOcrProvider | None:
    """Create a text-only OCR provider by provider type.

    Args:
        provider: Provider type ('gemini' or 'vllm').
        config: Provider configuration dict.

    Returns:
        Text OCR provider, or None if provider is unknown.
    """
    if provider == 'gemini':
        api_key = config.get('api_key', '')
        if not api_key:
            logger.warning('Gemini API key not configured')
            return None
        return GeminiTextOcrProvider(
            api_key=api_key,
            model=config.get('model', 'gemini-3-flash-preview'),
        )

    if provider == 'vllm':
        return VllmTextOcrProvider(
            host=config.get('host', 'localhost'),
            port=config.get('port', 8000),
            model=config.get('model', 'allenai/olmOCR-2-7B-1025-FP8'),
        )

    logger.warning("Unknown text provider: '%s'", provider)
    return None
