"""Project repository with raw SQL queries."""

import json
import logging
import uuid
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

# --- Old→New config format migration ---

_OLD_ENGINE_NAMES: dict[str, str] = {
    'commercial_api': 'Gemini API',
    'vllm': 'vLLM',
    'split_pipeline': 'Docling + OCR',
}


def normalize_ocr_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert old-format ocr_config to new multi-instance format.

    Old format has top-level 'engine_type', per-type sub-configs, and
    optional 'enabled_engines'.  New format has 'default_engine_id' and
    an 'engines' dict keyed by engine_id.

    If already in new format (has 'engines' key) or empty, returns as-is.

    Args:
        raw: Raw ocr_config dict from database.

    Returns:
        Normalized config in multi-instance format.
    """
    if not raw:
        return {'default_engine_id': None, 'engines': {}}

    # Already new format
    if 'engines' in raw:
        return raw

    # Not old format either (no engine_type key)
    if 'engine_type' not in raw:
        return {'default_engine_id': None, 'engines': {}}

    engines: dict[str, dict[str, Any]] = {}
    old_engine_type = raw.get('engine_type', 'pdfminer')

    # Migrate each sub-config that exists
    for sub_key in ('commercial_api', 'vllm', 'split_pipeline'):
        sub_config = raw.get(sub_key)
        if sub_config:
            engine_id = sub_key.replace('_', '-')
            engines[engine_id] = {
                'engine_type': sub_key,
                'name': _OLD_ENGINE_NAMES.get(sub_key, sub_key),
                'config': dict(sub_config),
            }

    # Determine default
    default_engine_id = None
    if old_engine_type != 'pdfminer':
        candidate = old_engine_type.replace('_', '-')
        if candidate in engines:
            default_engine_id = candidate

    logger.info(
        'Normalized old ocr_config (engine_type=%s) → %d engine(s)',
        old_engine_type,
        len(engines),
    )

    return {'default_engine_id': default_engine_id, 'engines': engines}


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
    """Get a project's OCR configuration (auto-normalized to multi-instance format).

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        OCR config dict in multi-instance format, or None if project not found.
    """
    row = await pool.fetchrow(
        'SELECT ocr_config FROM projects WHERE id = $1',
        project_id,
    )
    if row is None:
        return None
    raw = row['ocr_config']
    if raw is None:
        return normalize_ocr_config({})
    parsed = json.loads(raw) if isinstance(raw, str) else dict(raw)
    return normalize_ocr_config(parsed)


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
