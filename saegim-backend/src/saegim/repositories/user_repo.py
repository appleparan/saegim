"""User repository with raw SQL queries."""

import uuid

import asyncpg


async def create(
    pool: asyncpg.Pool,
    name: str,
    email: str,
    role: str = 'annotator',
) -> asyncpg.Record:
    """Create a new user.

    Args:
        pool: Database connection pool.
        name: User name.
        email: User email (must be unique).
        role: User role (admin, annotator, reviewer).

    Returns:
        asyncpg.Record: Created user record.
    """
    return await pool.fetchrow(
        """
        INSERT INTO users (name, email, role)
        VALUES ($1, $2, $3)
        RETURNING id, name, email, role, created_at
        """,
        name,
        email,
        role,
    )


async def get_by_id(pool: asyncpg.Pool, user_id: uuid.UUID) -> asyncpg.Record | None:
    """Get a user by ID.

    Args:
        pool: Database connection pool.
        user_id: User UUID.

    Returns:
        asyncpg.Record or None: User record if found.
    """
    return await pool.fetchrow(
        'SELECT id, name, email, role, created_at FROM users WHERE id = $1',
        user_id,
    )


async def list_all(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """List all users.

    Args:
        pool: Database connection pool.

    Returns:
        list[asyncpg.Record]: List of user records.
    """
    return await pool.fetch(
        'SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC',
    )
