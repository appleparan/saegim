"""Database connection pool management using asyncpg."""

import logging
from pathlib import Path

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def create_pool(database_url: str, min_size: int = 2, max_size: int = 10) -> asyncpg.Pool:
    """Create and return a connection pool.

    Args:
        database_url: PostgreSQL connection URL.
        min_size: Minimum number of connections in the pool.
        max_size: Maximum number of connections in the pool.

    Returns:
        asyncpg.Pool: Connection pool instance.
    """
    global _pool
    _pool = await asyncpg.create_pool(
        database_url,
        min_size=min_size,
        max_size=max_size,
    )
    logger.info('Database connection pool created')
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info('Database connection pool closed')


def get_pool() -> asyncpg.Pool:
    """Get the current connection pool.

    Returns:
        asyncpg.Pool: The active connection pool.

    Raises:
        RuntimeError: If the pool has not been created yet.
    """
    if _pool is None:
        msg = 'Database pool not initialized. Call create_pool() first.'
        raise RuntimeError(msg)
    return _pool


async def run_migrations(pool: asyncpg.Pool, migrations_dir: str = 'migrations') -> None:
    """Run SQL migration files in order.

    Args:
        pool: asyncpg connection pool.
        migrations_dir: Directory containing .sql migration files.
    """
    migrations_path = Path(migrations_dir)
    if not migrations_path.exists():
        logger.warning('Migrations directory not found: %s', migrations_dir)
        return

    sql_files = sorted(migrations_path.glob('*.sql'))
    async with pool.acquire() as conn:
        for sql_file in sql_files:
            logger.info('Running migration: %s', sql_file.name)
            sql = sql_file.read_text()
            await conn.execute(sql)
    logger.info('All migrations completed')
