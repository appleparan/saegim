"""Refresh token repository with raw SQL queries."""

import datetime
import uuid

import asyncpg


async def create(
    pool: asyncpg.Pool,
    user_id: uuid.UUID,
    token_hash: str,
    family_id: uuid.UUID,
    expires_at: datetime.datetime,
) -> asyncpg.Record:
    """Create a new refresh token record.

    Args:
        pool: Database connection pool.
        user_id: Owner user UUID.
        token_hash: SHA-256 hash of the raw token.
        family_id: Token family UUID for rotation tracking.
        expires_at: Token expiration timestamp.

    Returns:
        asyncpg.Record: Created refresh token record.
    """
    return await pool.fetchrow(
        """
        INSERT INTO refresh_tokens (user_id, token_hash, family_id, expires_at)
        VALUES ($1, $2, $3, $4)
        RETURNING id, user_id, token_hash, family_id, expires_at, revoked_at, created_at
        """,
        user_id,
        token_hash,
        family_id,
        expires_at,
    )


async def get_by_token_hash(
    pool: asyncpg.Pool,
    token_hash: str,
) -> asyncpg.Record | None:
    """Look up a refresh token by its hash.

    Args:
        pool: Database connection pool.
        token_hash: SHA-256 hash of the raw token.

    Returns:
        asyncpg.Record or None: Token record if found.
    """
    return await pool.fetchrow(
        """
        SELECT id, user_id, token_hash, family_id, expires_at, revoked_at, created_at
        FROM refresh_tokens
        WHERE token_hash = $1
        """,
        token_hash,
    )


async def revoke(pool: asyncpg.Pool, token_id: uuid.UUID) -> None:
    """Revoke a single refresh token.

    Args:
        pool: Database connection pool.
        token_id: Token UUID to revoke.
    """
    await pool.execute(
        'UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = $1',
        token_id,
    )


async def revoke_family(pool: asyncpg.Pool, family_id: uuid.UUID) -> None:
    """Revoke all refresh tokens in a family.

    Args:
        pool: Database connection pool.
        family_id: Family UUID whose tokens should be revoked.
    """
    await pool.execute(
        'UPDATE refresh_tokens SET revoked_at = NOW() WHERE family_id = $1 AND revoked_at IS NULL',
        family_id,
    )


async def revoke_all_for_user(pool: asyncpg.Pool, user_id: uuid.UUID) -> None:
    """Revoke all refresh tokens for a user.

    Args:
        pool: Database connection pool.
        user_id: User UUID whose tokens should be revoked.
    """
    await pool.execute(
        'UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id = $1 AND revoked_at IS NULL',
        user_id,
    )


async def delete_expired(pool: asyncpg.Pool) -> int:
    """Delete expired refresh tokens for cleanup.

    Args:
        pool: Database connection pool.

    Returns:
        int: Number of deleted rows.
    """
    result = await pool.execute(
        'DELETE FROM refresh_tokens WHERE expires_at < NOW()',
    )
    # asyncpg returns 'DELETE N' where N is the row count
    return int(result.split()[-1])
