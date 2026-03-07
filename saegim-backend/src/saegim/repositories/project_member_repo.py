"""Project member repository with raw SQL queries."""

import logging
import uuid

import asyncpg

logger = logging.getLogger(__name__)


async def add(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str = 'annotator',
) -> asyncpg.Record:
    """Add a member to a project.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.
        user_id: User UUID.
        role: Member role (owner, annotator, reviewer).

    Returns:
        asyncpg.Record: Created member record with user info.

    Raises:
        asyncpg.UniqueViolationError: If user is already a member.
    """
    await pool.execute(
        """
        INSERT INTO project_members (project_id, user_id, role)
        VALUES ($1, $2, $3)
        """,
        project_id,
        user_id,
        role,
    )
    return await pool.fetchrow(
        """
        SELECT pm.user_id, u.name AS user_name, u.email AS user_email,
               pm.role, pm.joined_at
        FROM project_members pm
        JOIN users u ON u.id = pm.user_id
        WHERE pm.project_id = $1 AND pm.user_id = $2
        """,
        project_id,
        user_id,
    )


async def get_role(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> str | None:
    """Get a user's role in a project.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.
        user_id: User UUID.

    Returns:
        str or None: Role string if member, None otherwise.
    """
    row = await pool.fetchrow(
        'SELECT role FROM project_members WHERE project_id = $1 AND user_id = $2',
        project_id,
        user_id,
    )
    if row is None:
        return None
    return row['role']


async def list_by_project(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> list[asyncpg.Record]:
    """List all members of a project with user info.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        list[asyncpg.Record]: Member records with user name and email.
    """
    return await pool.fetch(
        """
        SELECT pm.user_id, u.name AS user_name, u.email AS user_email,
               pm.role, pm.joined_at
        FROM project_members pm
        JOIN users u ON u.id = pm.user_id
        WHERE pm.project_id = $1
        ORDER BY pm.joined_at ASC
        """,
        project_id,
    )


async def update_role(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
) -> asyncpg.Record | None:
    """Update a member's role in a project.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.
        user_id: User UUID.
        role: New role string.

    Returns:
        asyncpg.Record or None: Updated member record, or None if not found.
    """
    result = await pool.execute(
        """
        UPDATE project_members SET role = $3
        WHERE project_id = $1 AND user_id = $2
        """,
        project_id,
        user_id,
        role,
    )
    if result != 'UPDATE 1':
        return None
    return await pool.fetchrow(
        """
        SELECT pm.user_id, u.name AS user_name, u.email AS user_email,
               pm.role, pm.joined_at
        FROM project_members pm
        JOIN users u ON u.id = pm.user_id
        WHERE pm.project_id = $1 AND pm.user_id = $2
        """,
        project_id,
        user_id,
    )


async def remove(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Remove a member from a project.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.
        user_id: User UUID.

    Returns:
        bool: True if the member was removed.
    """
    result = await pool.execute(
        'DELETE FROM project_members WHERE project_id = $1 AND user_id = $2',
        project_id,
        user_id,
    )
    return result == 'DELETE 1'


async def list_projects_for_user(
    pool: asyncpg.Pool,
    user_id: uuid.UUID,
) -> list[asyncpg.Record]:
    """List all projects a user is a member of.

    Args:
        pool: Database connection pool.
        user_id: User UUID.

    Returns:
        list[asyncpg.Record]: Project records the user belongs to.
    """
    return await pool.fetch(
        """
        SELECT p.id, p.name, p.description, p.created_at
        FROM projects p
        JOIN project_members pm ON pm.project_id = p.id
        WHERE pm.user_id = $1
        ORDER BY p.created_at DESC
        """,
        user_id,
    )
