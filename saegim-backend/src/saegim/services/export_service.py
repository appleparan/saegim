"""Export service for OmniDocBench JSON generation."""

import io
import json
import re
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg

from saegim.repositories import document_repo, page_repo, project_repo


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename.

    Replaces whitespace with underscores, removes filesystem-unsafe characters,
    and strips leading/trailing underscores.

    Args:
        name: Raw filename string.

    Returns:
        Sanitized filename safe for all major filesystems.
    """
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    name = name.strip('._')
    return name or 'export'


def _document_dir_name(filename: str) -> str:
    """Derive a directory name from a document filename.

    Removes the file extension and sanitizes the result.

    Args:
        filename: Original document filename (e.g. "paper.pdf").

    Returns:
        Sanitized directory name (e.g. "paper").
    """
    stem = Path(filename).stem
    return sanitize_filename(stem)


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


async def export_project_zip(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> tuple[bytes, str] | None:
    """Export a project as an OmniDocBench-compatible ZIP archive.

    The ZIP contains:
    - annos.json: OmniDocBench labeling data with relative image_path
    - images/{document_name}/page_NNN.png: page images organised by document

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        Tuple of (zip_bytes, zip_filename) or None if project not found.
    """
    project = await project_repo.get_by_id(pool, project_id)
    if project is None:
        return None

    pages = await page_repo.get_all_by_project_with_document(pool, project_id)

    project_name = sanitize_filename(project['name'])
    timestamp = datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S')
    zip_filename = f'{project_name}_{timestamp}.zip'

    buf = io.BytesIO()
    annos_data: list[dict[str, Any]] = []

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for page in pages:
            annotation = page['annotation_data']
            if isinstance(annotation, str):
                annotation = json.loads(annotation)
            annotation = annotation or {}

            page_attribute = annotation.pop('page_attribute', {})

            doc_dir = _document_dir_name(page['document_filename'])
            image_name = f'page_{page["page_no"]:03d}.png'
            relative_image_path = f'images/{doc_dir}/{image_name}'

            # Add page image to ZIP
            source_path = Path(page['image_path'])
            if source_path.exists():
                zf.write(str(source_path), relative_image_path)

            entry = {
                **annotation,
                'page_info': {
                    'page_no': page['page_no'],
                    'height': page['height'],
                    'width': page['width'],
                    'image_path': relative_image_path,
                    'page_attribute': page_attribute,
                },
            }
            annos_data.append(entry)

        annos_json = json.dumps(
            {
                'project_name': project['name'],
                'total_pages': len(annos_data),
                'data': annos_data,
            },
            ensure_ascii=False,
            indent=2,
        )
        zf.writestr('annos.json', annos_json)

    return (buf.getvalue(), zip_filename)


async def export_document_zip(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    document_id: uuid.UUID,
) -> tuple[bytes, str] | None:
    """Export a single document as an OmniDocBench-compatible ZIP archive.

    Args:
        pool: Database connection pool.
        project_id: Parent project UUID (for validation).
        document_id: Document UUID.

    Returns:
        Tuple of (zip_bytes, zip_filename) or None if not found.
    """
    doc = await document_repo.get_by_id(pool, document_id)
    if doc is None or doc['project_id'] != project_id:
        return None

    pages = await page_repo.list_by_document_for_export(pool, document_id)

    doc_dir = _document_dir_name(doc['filename'])
    timestamp = datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S')
    zip_filename = f'{doc_dir}_{timestamp}.zip'

    buf = io.BytesIO()
    annos_data: list[dict[str, Any]] = []

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for page in pages:
            annotation = page['annotation_data']
            if isinstance(annotation, str):
                annotation = json.loads(annotation)
            annotation = annotation or {}

            page_attribute = annotation.pop('page_attribute', {})

            image_name = f'page_{page["page_no"]:03d}.png'
            relative_image_path = f'images/{doc_dir}/{image_name}'

            source_path = Path(page['image_path'])
            if source_path.exists():
                zf.write(str(source_path), relative_image_path)

            entry = {
                **annotation,
                'page_info': {
                    'page_no': page['page_no'],
                    'height': page['height'],
                    'width': page['width'],
                    'image_path': relative_image_path,
                    'page_attribute': page_attribute,
                },
            }
            annos_data.append(entry)

        annos_json = json.dumps(
            {
                'document_name': doc['filename'],
                'total_pages': len(annos_data),
                'data': annos_data,
            },
            ensure_ascii=False,
            indent=2,
        )
        zf.writestr('annos.json', annos_json)

    return (buf.getvalue(), zip_filename)
