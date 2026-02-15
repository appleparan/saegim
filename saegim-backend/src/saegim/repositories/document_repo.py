"""Document repository with raw SQL queries."""

import uuid

import asyncpg


async def create(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    filename: str,
    pdf_path: str,
    total_pages: int = 0,
    status: str = 'uploading',
) -> asyncpg.Record:
    """Create a new document record.

    Args:
        pool: Database connection pool.
        project_id: Parent project UUID.
        filename: Original PDF filename.
        pdf_path: Path to stored PDF file.
        total_pages: Number of pages in the PDF.
        status: Initial document status.

    Returns:
        asyncpg.Record: Created document record.
    """
    return await pool.fetchrow(
        """
        INSERT INTO documents (project_id, filename, pdf_path, total_pages, status)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, project_id, filename, pdf_path, total_pages, status, created_at
        """,
        project_id,
        filename,
        pdf_path,
        total_pages,
        status,
    )


async def get_by_id(pool: asyncpg.Pool, document_id: uuid.UUID) -> asyncpg.Record | None:
    """Get a document by ID.

    Args:
        pool: Database connection pool.
        document_id: Document UUID.

    Returns:
        asyncpg.Record or None: Document record if found.
    """
    return await pool.fetchrow(
        """
        SELECT id, project_id, filename, pdf_path, total_pages, status, created_at
        FROM documents WHERE id = $1
        """,
        document_id,
    )


async def delete(pool: asyncpg.Pool, document_id: uuid.UUID) -> bool:
    """Delete a document by ID.

    Cascades to pages and task history.

    Args:
        pool: Database connection pool.
        document_id: Document UUID.

    Returns:
        bool: True if document was deleted.
    """
    result = await pool.execute(
        'DELETE FROM documents WHERE id = $1',
        document_id,
    )
    return result == 'DELETE 1'


async def list_by_project(pool: asyncpg.Pool, project_id: uuid.UUID) -> list[asyncpg.Record]:
    """List all documents for a project.

    Args:
        pool: Database connection pool.
        project_id: Parent project UUID.

    Returns:
        list[asyncpg.Record]: List of document records.
    """
    return await pool.fetch(
        """
        SELECT id, filename, total_pages, status, created_at
        FROM documents WHERE project_id = $1
        ORDER BY created_at DESC
        """,
        project_id,
    )


async def update_status(
    pool: asyncpg.Pool,
    document_id: uuid.UUID,
    status: str,
    total_pages: int | None = None,
) -> asyncpg.Record | None:
    """Update document status and optionally total_pages.

    Args:
        pool: Database connection pool.
        document_id: Document UUID.
        status: New status value.
        total_pages: Updated page count (optional).

    Returns:
        asyncpg.Record or None: Updated document record.
    """
    if total_pages is not None:
        return await pool.fetchrow(
            """
            UPDATE documents SET status = $1, total_pages = $2
            WHERE id = $3
            RETURNING id, project_id, filename, pdf_path, total_pages, status, created_at
            """,
            status,
            total_pages,
            document_id,
        )
    return await pool.fetchrow(
        """
        UPDATE documents SET status = $1
        WHERE id = $2
        RETURNING id, project_id, filename, pdf_path, total_pages, status, created_at
        """,
        status,
        document_id,
    )
