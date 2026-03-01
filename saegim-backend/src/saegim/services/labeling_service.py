"""Labeling service for annotation data management."""

import json
import uuid
from typing import Any

import asyncpg

from saegim.repositories import page_repo


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

    annotation_data = record['annotation_data']
    if isinstance(annotation_data, str):
        annotation_data = json.loads(annotation_data)

    auto_extracted = record['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': annotation_data or {},
        'auto_extracted_data': auto_extracted,
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
        'project_id': record['project_id'],
        'project_name': record['project_name'],
        'document_filename': record['document_filename'],
        'pdf_path': record['pdf_path'],
    }


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

    result_annotation = record['annotation_data']
    if isinstance(result_annotation, str):
        result_annotation = json.loads(result_annotation)

    auto_extracted = record['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': auto_extracted,
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
    }


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

    result_annotation = record['annotation_data']
    if isinstance(result_annotation, str):
        result_annotation = json.loads(result_annotation)

    auto_extracted = record['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': auto_extracted,
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
    }


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

    result_annotation = record['annotation_data']
    if isinstance(result_annotation, str):
        result_annotation = json.loads(result_annotation)

    auto_extracted = record['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': auto_extracted,
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
    }


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

    result_annotation = record['annotation_data']
    if isinstance(result_annotation, str):
        result_annotation = json.loads(result_annotation)

    auto_extracted = record['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': auto_extracted,
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
    }


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

    result_annotation = record['annotation_data']
    if isinstance(result_annotation, str):
        result_annotation = json.loads(result_annotation)

    auto_extracted = record['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': auto_extracted,
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
    }


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

    result_annotation = record['annotation_data']
    if isinstance(result_annotation, str):
        result_annotation = json.loads(result_annotation)

    auto_extracted = record['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': auto_extracted,
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
    }


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

    result_annotation = result['annotation_data']
    if isinstance(result_annotation, str):
        result_annotation = json.loads(result_annotation)

    auto_extracted = result['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': result['id'],
        'document_id': result['document_id'],
        'page_no': result['page_no'],
        'width': result['width'],
        'height': result['height'],
        'image_path': result['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': auto_extracted,
        'status': result['status'],
        'assigned_to': result['assigned_to'],
        'updated_at': result['updated_at'],
    }


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

    result_annotation = record['annotation_data']
    if isinstance(result_annotation, str):
        result_annotation = json.loads(result_annotation)

    auto_extracted = record['auto_extracted_data']
    if isinstance(auto_extracted, str):
        auto_extracted = json.loads(auto_extracted)

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': auto_extracted,
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
    }
