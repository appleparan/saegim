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
    record = await page_repo.get_by_id(pool, page_id)
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

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': record['auto_extracted_data'],
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

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': record['auto_extracted_data'],
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

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': record['auto_extracted_data'],
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
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

    return {
        'id': record['id'],
        'document_id': record['document_id'],
        'page_no': record['page_no'],
        'width': record['width'],
        'height': record['height'],
        'image_path': record['image_path'],
        'annotation_data': result_annotation or {},
        'auto_extracted_data': record['auto_extracted_data'],
        'status': record['status'],
        'assigned_to': record['assigned_to'],
        'updated_at': record['updated_at'],
    }
