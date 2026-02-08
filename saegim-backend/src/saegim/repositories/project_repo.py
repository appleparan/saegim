"""Project repository with raw SQL queries."""

import uuid

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
