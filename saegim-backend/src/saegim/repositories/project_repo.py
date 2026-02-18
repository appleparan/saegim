"""Project repository with raw SQL queries."""

import json
import uuid
from typing import Any

import asyncpg


async def create(pool: asyncpg.Pool, name: str, description: str = '') -> asyncpg.Record:
    """Create a new project.

    Args:
        pool: Database connection pool.
        name: Project name.
        description: Project description.

    Returns:
        asyncpg.Record: Created project record.
    """
    return await pool.fetchrow(
        """
        INSERT INTO projects (name, description)
        VALUES ($1, $2)
        RETURNING id, name, description, created_at
        """,
        name,
        description,
    )


async def get_by_id(pool: asyncpg.Pool, project_id: uuid.UUID) -> asyncpg.Record | None:
    """Get a project by ID.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        asyncpg.Record or None: Project record if found.
    """
    return await pool.fetchrow(
        'SELECT id, name, description, created_at FROM projects WHERE id = $1',
        project_id,
    )


async def delete(pool: asyncpg.Pool, project_id: uuid.UUID) -> bool:
    """Delete a project by ID.

    Cascades to documents, pages, and task history.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        bool: True if project was deleted.
    """
    result = await pool.execute(
        'DELETE FROM projects WHERE id = $1',
        project_id,
    )
    return result == 'DELETE 1'


async def list_all(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """List all projects ordered by creation date.

    Args:
        pool: Database connection pool.

    Returns:
        list[asyncpg.Record]: List of project records.
    """
    return await pool.fetch(
        'SELECT id, name, description, created_at FROM projects ORDER BY created_at DESC',
    )


async def get_ocr_config(pool: asyncpg.Pool, project_id: uuid.UUID) -> dict[str, Any] | None:
    """Get a project's OCR configuration.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        OCR config dict, or None if project not found.
    """
    row = await pool.fetchrow(
        'SELECT ocr_config FROM projects WHERE id = $1',
        project_id,
    )
    if row is None:
        return None
    raw = row['ocr_config']
    if raw is None:
        return {}
    return json.loads(raw) if isinstance(raw, str) else dict(raw)


async def update_ocr_config(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    ocr_config: dict[str, Any],
) -> bool:
    """Update a project's OCR configuration.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.
        ocr_config: OCR config dict to store as JSONB.

    Returns:
        True if the project was found and updated.
    """
    result = await pool.execute(
        'UPDATE projects SET ocr_config = $1::jsonb WHERE id = $2',
        json.dumps(ocr_config),
        project_id,
    )
    return result == 'UPDATE 1'
