"""Export service for OmniDocBench JSON generation."""

import json
import uuid
from typing import Any

import asyncpg

from saegim.repositories import page_repo, project_repo


async def export_project(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Export a project as OmniDocBench JSON format.

    Combines all page annotation_data with page_info to produce
    the final benchmark dataset format.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        dict or None: Export data with project name, total pages, and data array.
    """
    project = await project_repo.get_by_id(pool, project_id)
    if project is None:
        return None

    pages = await page_repo.get_all_by_project(pool, project_id)

    result: list[dict[str, Any]] = []
    for page in pages:
        annotation = page['annotation_data']
        if isinstance(annotation, str):
            annotation = json.loads(annotation)
        annotation = annotation or {}

        page_attribute = annotation.pop('page_attribute', {})

        entry = {
            **annotation,
            'page_info': {
                'page_no': page['page_no'],
                'height': page['height'],
                'width': page['width'],
                'image_path': page['image_path'],
                'page_attribute': page_attribute,
            },
        }
        result.append(entry)

    return {
        'project_name': project['name'],
        'total_pages': len(result),
        'data': result,
    }
