"""Labeling service for annotation data management."""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any

import asyncpg

from saegim.repositories import page_repo
from saegim.services import attribute_classifier, extraction_service
from saegim.services.document_service import _resolve_engine_type, _resolve_ocr_config
from saegim.services.engines import build_engine_by_id

logger = logging.getLogger(__name__)

_STANDARD_FIELDS = (
    'id',
    'document_id',
    'page_no',
    'width',
    'height',
    'image_path',
    'status',
    'assigned_to',
    'updated_at',
)


def _parse_json_field(value: str | dict | list | None) -> dict | list | None:
    """Parse a JSON string field if needed."""
    if isinstance(value, str):
        return json.loads(value)
    return value


def _record_to_page_dict(
    record: asyncpg.Record,
    *,
    extra_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Convert a database record to a page response dict.

    Args:
        record: Database record with page fields.
        extra_fields: Additional field names to include from the record.

    Returns:
        Page data dictionary with parsed JSON fields.
    """
    result: dict[str, Any] = {field: record[field] for field in _STANDARD_FIELDS}
    result['annotation_data'] = _parse_json_field(record['annotation_data']) or {}
    result['auto_extracted_data'] = _parse_json_field(record['auto_extracted_data'])
    for field in extra_fields:
        result[field] = record[field]
    return result


async def get_page_data(pool: asyncpg.Pool, page_id: uuid.UUID) -> dict[str, Any] | None:
    """Get page data including annotation for the labeling UI.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        dict or None: Page data with annotation if found.
    """
    record = await page_repo.get_by_id_with_context(pool, page_id)
    if record is None:
        return None

    return _record_to_page_dict(
        record,
        extra_fields=('project_id', 'project_name', 'document_filename', 'pdf_path'),
    )


async def save_annotation(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    annotation_data: dict[str, Any],
) -> dict[str, Any] | None:
    """Save annotation data for a page.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        annotation_data: OmniDocBench annotation JSON.

    Returns:
        dict or None: Updated page data if found.
    """
    record = await page_repo.update_annotation(pool, page_id, annotation_data)
    if record is None:
        return None

    return _record_to_page_dict(record)


async def save_page_attribute(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    page_attribute: dict[str, Any],
) -> dict[str, Any] | None:
    """Save page attribute within annotation data.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        page_attribute: Page attribute dictionary.

    Returns:
        dict or None: Updated page data if found.
    """
    record = await page_repo.update_page_attribute(pool, page_id, page_attribute)
    if record is None:
        return None

    return _record_to_page_dict(record)


async def add_element(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    element: dict[str, Any],
) -> dict[str, Any] | None:
    """Add a new layout element to the page.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        element: Layout element dictionary.

    Returns:
        dict or None: Updated page data if found.
    """
    page = await page_repo.get_by_id(pool, page_id)
    if page is None:
        return None

    annotation = page['annotation_data']
    if isinstance(annotation, str):
        annotation = json.loads(annotation)
    annotation = annotation or {}

    layout_dets = annotation.get('layout_dets', [])
    max_anno_id = max((e.get('anno_id', -1) for e in layout_dets), default=-1)
    element['anno_id'] = max_anno_id + 1
    element['order'] = len(layout_dets)

    record = await page_repo.add_element(pool, page_id, element)
    if record is None:
        return None

    return _record_to_page_dict(record)


async def accept_auto_extraction(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Accept auto-extracted data as the initial annotation.

    Copies auto_extracted_data to annotation_data only when annotation is empty.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        dict or None: Updated page data, or None if page not found or
        preconditions not met (no auto data or annotation already exists).
    """
    record = await page_repo.accept_auto_extracted(pool, page_id)
    if record is None:
        return None

    return _record_to_page_dict(record)


async def force_accept_auto_extraction(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Force-accept auto-extracted data, overwriting existing annotation.

    Unlike ``accept_auto_extraction``, this replaces annotation_data
    even when it already contains elements.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        dict or None: Updated page data, or None if no auto data.
    """
    record = await page_repo.force_accept_auto_extracted(pool, page_id)
    if record is None:
        return None

    return _record_to_page_dict(record)


async def add_relation(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    relation: dict[str, Any],
) -> dict[str, Any] | None:
    """Add a relation between two elements.

    Validates that both anno_ids exist, prevents self-reference and duplicates.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        relation: Relation dict with source_anno_id, target_anno_id, relation_type.

    Returns:
        dict or None: Updated page data if found, None if page not found.

    Raises:
        ValueError: If validation fails (self-reference, missing elements, duplicate).
    """
    source_id = relation['source_anno_id']
    target_id = relation['target_anno_id']

    if source_id == target_id:
        msg = 'Self-referencing relation is not allowed'
        raise ValueError(msg)

    page = await page_repo.get_by_id(pool, page_id)
    if page is None:
        return None

    annotation = page['annotation_data']
    if isinstance(annotation, str):
        annotation = json.loads(annotation)
    annotation = annotation or {}

    layout_dets = annotation.get('layout_dets', [])
    anno_ids = {e.get('anno_id') for e in layout_dets}

    if source_id not in anno_ids:
        msg = f'Source element with anno_id {source_id} not found'
        raise ValueError(msg)
    if target_id not in anno_ids:
        msg = f'Target element with anno_id {target_id} not found'
        raise ValueError(msg)

    existing_relations = annotation.get('extra', {}).get('relation', [])
    for r in existing_relations:
        if r.get('source_anno_id') == source_id and r.get('target_anno_id') == target_id:
            msg = 'Duplicate relation already exists'
            raise ValueError(msg)

    record = await page_repo.add_relation(pool, page_id, relation)
    if record is None:
        return None

    return _record_to_page_dict(record)


async def delete_relation(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    source_anno_id: int,
    target_anno_id: int,
) -> dict[str, Any] | None:
    """Delete a relation between two elements.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        source_anno_id: Source annotation ID.
        target_anno_id: Target annotation ID.

    Returns:
        dict or None: Updated page data if found.
    """
    record = await page_repo.delete_relation(pool, page_id, source_anno_id, target_anno_id)
    if record is None:
        return None

    return _record_to_page_dict(record)


async def update_reading_order(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    order_map: dict[str, int],
) -> dict[str, Any] | None:
    """Update reading order for layout elements.

    Validates that all anno_ids in the map exist in the page's layout_dets,
    then updates each element's order field.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        order_map: Mapping of anno_id (as string) to new order (int).

    Returns:
        dict or None: Updated page data if found and valid.
    """
    parsed_map: dict[int, int] = {int(k): v for k, v in order_map.items()}

    record = await page_repo.get_by_id(pool, page_id)
    if record is None:
        return None

    annotation = record['annotation_data']
    if isinstance(annotation, str):
        annotation = json.loads(annotation)
    annotation = annotation or {}

    layout_dets = annotation.get('layout_dets', [])
    existing_ids = {el.get('anno_id') for el in layout_dets}

    for anno_id in parsed_map:
        if anno_id not in existing_ids:
            return None

    updated_dets = [
        {**el, 'order': parsed_map[el['anno_id']]} if el.get('anno_id') in parsed_map else el
        for el in layout_dets
    ]
    updated_annotation = {**annotation, 'layout_dets': updated_dets}

    result = await page_repo.update_annotation(pool, page_id, updated_annotation)
    if result is None:
        return None

    return _record_to_page_dict(result)


async def delete_element(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    anno_id: int,
) -> dict[str, Any] | None:
    """Delete a layout element by anno_id.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        anno_id: Annotation ID of the element.

    Returns:
        dict or None: Updated page data if found.
    """
    record = await page_repo.delete_element(pool, page_id, anno_id)
    if record is None:
        return None

    return _record_to_page_dict(record)


async def extract_page_on_demand(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Run on-demand OCR extraction for a single page.

    Resolves the OCR engine from the page's project config and extracts
    structured layout elements. For pdfminer, uses the PDF file directly.
    For other engines, uses the rendered page image.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        dict or None: Updated page data with auto_extracted_data populated,
        or None if page not found.

    Raises:
        LookupError: If project has no OCR config or engine not found.
    """
    record = await page_repo.get_by_id_with_context(pool, page_id)
    if record is None:
        return None

    project_id = record['project_id']
    image_path = record['image_path']
    pdf_path = record['pdf_path']
    page_no = record['page_no']
    width = record['width']
    height = record['height']

    ocr_config = await _resolve_ocr_config(pool, project_id)
    engine_type = _resolve_engine_type(ocr_config)

    if engine_type == 'pdfminer':
        if not pdf_path:
            msg = 'PDF file path not available for pdfminer extraction'
            raise LookupError(msg)
        extracted = await asyncio.to_thread(
            extraction_service.extract_page_elements,
            Path(pdf_path),
            page_no=page_no - 1,
            scale=2.0,
        )
    else:
        engine = build_engine_by_id(ocr_config)
        extracted = await asyncio.to_thread(
            engine.extract_page,
            Path(image_path),
            width,
            height,
        )

    extracted = attribute_classifier.classify_attributes(extracted)

    updated = await page_repo.update_auto_extracted_data(pool, page_id, extracted)
    if updated is None:
        return None

    return _record_to_page_dict(updated)
