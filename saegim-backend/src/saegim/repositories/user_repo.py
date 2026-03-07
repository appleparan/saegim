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


async def get_by_email(pool: asyncpg.Pool, email: str) -> asyncpg.Record | None:
    """Get a user by email address (includes password_hash).

    Args:
        pool: Database connection pool.
        email: User email address.

    Returns:
        asyncpg.Record or None: User record if found.
    """
    return await pool.fetchrow(
        'SELECT id, name, email, role, password_hash, created_at FROM users WHERE email = $1',
        email,
    )


async def create_with_password(
    pool: asyncpg.Pool,
    name: str,
    email: str,
    password_hash: str,
    role: str = 'annotator',
) -> asyncpg.Record:
    """Create a new user with password hash.

    Args:
        pool: Database connection pool.
        name: User name.
        email: User email (must be unique).
        password_hash: Bcrypt password hash.
        role: User role (admin, annotator, reviewer).

    Returns:
        asyncpg.Record: Created user record.
    """
    return await pool.fetchrow(
        """
        INSERT INTO users (name, email, password_hash, role)
        VALUES ($1, $2, $3, $4)
        RETURNING id, name, email, role, created_at
        """,
        name,
        email,
        password_hash,
        role,
    )


async def count_all(pool: asyncpg.Pool) -> int:
    """Count total number of users.

    Args:
        pool: Database connection pool.

    Returns:
        int: Total user count.
    """
    row = await pool.fetchrow('SELECT COUNT(*) AS cnt FROM users')
    return int(row['cnt'])


async def update_role(
    pool: asyncpg.Pool,
    user_id: uuid.UUID,
    role: str,
) -> asyncpg.Record | None:
    """Update a user's system role.

    Args:
        pool: Database connection pool.
        user_id: User UUID.
        role: New role value.

    Returns:
        asyncpg.Record or None: Updated user record, or None if not found.
    """
    return await pool.fetchrow(
        """
        UPDATE users SET role = $1
        WHERE id = $2
        RETURNING id, name, email, role, created_at
        """,
        role,
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
