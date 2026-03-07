"""User repository with raw SQL queries."""

import uuid

import asyncpg


async def create(
    pool: asyncpg.Pool,
    name: str,
    email: str,
    role: str = 'annotator',
    login_id: str | None = None,
) -> asyncpg.Record:
    """Create a new user.

    Args:
        pool: Database connection pool.
        name: User name.
        email: User email (must be unique).
        role: User role (admin, annotator, reviewer).
        login_id: Login ID. Defaults to email for backward compatibility.

    Returns:
        asyncpg.Record: Created user record.
    """
    resolved_login_id = login_id or email
    return await pool.fetchrow(
        """
        INSERT INTO users (name, login_id, email, role)
        VALUES ($1, $2, $3, $4)
        RETURNING id, name, login_id, email, role, must_change_password, created_at
        """,
        name,
        resolved_login_id,
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
        """
        SELECT id, name, login_id, email, role, must_change_password, created_at
        FROM users
        WHERE id = $1
        """,
        user_id,
    )


async def get_with_password_by_id(pool: asyncpg.Pool, user_id: uuid.UUID) -> asyncpg.Record | None:
    """Get a user by ID including password hash.

    Args:
        pool: Database connection pool.
        user_id: User UUID.

    Returns:
        asyncpg.Record or None: User record if found.
    """
    return await pool.fetchrow(
        """
        SELECT id, name, login_id, email, role, password_hash, must_change_password, created_at
        FROM users
        WHERE id = $1
        """,
        user_id,
    )


async def get_by_login_id(pool: asyncpg.Pool, login_id: str) -> asyncpg.Record | None:
    """Get a user by login ID (includes password_hash).

    Args:
        pool: Database connection pool.
        login_id: User login ID.

    Returns:
        asyncpg.Record or None: User record if found.
    """
    return await pool.fetchrow(
        """
        SELECT id, name, login_id, email, role, password_hash, must_change_password, created_at
        FROM users
        WHERE login_id = $1
        """,
        login_id,
    )


async def is_login_id_taken(
    pool: asyncpg.Pool,
    login_id: str,
    *,
    exclude_user_id: uuid.UUID | None = None,
) -> bool:
    """Check whether login_id is already used by another user.

    Args:
        pool: Database connection pool.
        login_id: Login ID to check.
        exclude_user_id: Optional user ID to ignore (for self-update).

    Returns:
        bool: True when the login ID is already taken.
    """
    if exclude_user_id is None:
        row = await pool.fetchrow('SELECT 1 FROM users WHERE login_id = $1 LIMIT 1', login_id)
    else:
        row = await pool.fetchrow(
            'SELECT 1 FROM users WHERE login_id = $1 AND id != $2 LIMIT 1',
            login_id,
            exclude_user_id,
        )
    return row is not None


async def get_by_email(pool: asyncpg.Pool, email: str) -> asyncpg.Record | None:
    """Get a user by email address (includes password_hash)."""
    return await pool.fetchrow(
        """
        SELECT id, name, login_id, email, role, password_hash, must_change_password, created_at
        FROM users
        WHERE email = $1
        """,
        email,
    )


async def is_email_taken(
    pool: asyncpg.Pool,
    email: str,
    *,
    exclude_user_id: uuid.UUID | None = None,
) -> bool:
    """Check whether email is already used by another user.

    Args:
        pool: Database connection pool.
        email: Email to check.
        exclude_user_id: Optional user ID to ignore (for self-update).

    Returns:
        bool: True when the email is already taken.
    """
    if exclude_user_id is None:
        row = await pool.fetchrow('SELECT 1 FROM users WHERE email = $1 LIMIT 1', email)
    else:
        row = await pool.fetchrow(
            'SELECT 1 FROM users WHERE email = $1 AND id != $2 LIMIT 1',
            email,
            exclude_user_id,
        )
    return row is not None


async def create_with_password(
    pool: asyncpg.Pool,
    name: str,
    login_id: str,
    password_hash: str,
    role: str = 'annotator',
    *,
    email: str | None = None,
    must_change_password: bool = False,
) -> asyncpg.Record:
    """Create a new user with password hash.

    Args:
        pool: Database connection pool.
        name: User name.
        login_id: Login ID (must be unique).
        password_hash: Bcrypt password hash.
        role: User role (admin, annotator, reviewer).
        email: Email value. Defaults to login_id.
        must_change_password: Whether user must change password on first login.

    Returns:
        asyncpg.Record: Created user record.
    """
    resolved_email = email or login_id
    return await pool.fetchrow(
        """
        INSERT INTO users (name, login_id, email, password_hash, must_change_password, role)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, name, login_id, email, role, must_change_password, created_at
        """,
        name,
        login_id,
        resolved_email,
        password_hash,
        must_change_password,
        role,
    )


async def update_credentials(
    pool: asyncpg.Pool,
    user_id: uuid.UUID,
    *,
    login_id: str,
    email: str,
    password_hash: str,
    must_change_password: bool,
) -> asyncpg.Record | None:
    """Update a user's credentials.

    Args:
        pool: Database connection pool.
        user_id: User UUID.
        login_id: New login ID.
        email: New email value.
        password_hash: New or existing password hash.
        must_change_password: New must_change_password flag.

    Returns:
        asyncpg.Record or None: Updated user record, or None if not found.
    """
    return await pool.fetchrow(
        """
        UPDATE users
        SET login_id = $1,
            email = $2,
            password_hash = $3,
            must_change_password = $4
        WHERE id = $5
        RETURNING id, name, login_id, email, role, must_change_password, created_at
        """,
        login_id,
        email,
        password_hash,
        must_change_password,
        user_id,
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
        RETURNING id, name, login_id, email, role, must_change_password, created_at
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
        """
        SELECT id, name, login_id, email, role, must_change_password, created_at
        FROM users
        ORDER BY created_at DESC
        """,
    )
