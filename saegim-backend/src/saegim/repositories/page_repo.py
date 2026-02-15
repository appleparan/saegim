"""Page repository with raw SQL queries for annotation data."""

import json
import uuid

import asyncpg


async def create(
    pool: asyncpg.Pool,
    document_id: uuid.UUID,
    page_no: int,
    width: int,
    height: int,
    image_path: str,
    auto_extracted_data: dict | None = None,
) -> asyncpg.Record:
    """Create a new page record.

    Args:
        pool: Database connection pool.
        document_id: Parent document UUID.
        page_no: Page number (1-based).
        width: Page image width in pixels.
        height: Page image height in pixels.
        image_path: Path to the page image file.
        auto_extracted_data: Auto-extracted annotation data from PDF parsing.

    Returns:
        asyncpg.Record: Created page record.
    """
    return await pool.fetchrow(
        """
        INSERT INTO pages (document_id, page_no, width, height, image_path, auto_extracted_data)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        RETURNING id, document_id, page_no, width, height, image_path,
                  annotation_data, auto_extracted_data, status, assigned_to,
                  locked_at, updated_at
        """,
        document_id,
        page_no,
        width,
        height,
        image_path,
        json.dumps(auto_extracted_data) if auto_extracted_data else None,
    )


async def get_by_id(pool: asyncpg.Pool, page_id: uuid.UUID) -> asyncpg.Record | None:
    """Get a page by ID with annotation data.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        asyncpg.Record or None: Page record if found.
    """
    return await pool.fetchrow(
        """
        SELECT id, document_id, page_no, width, height, image_path,
               annotation_data, auto_extracted_data, status, assigned_to,
               locked_at, updated_at
        FROM pages WHERE id = $1
        """,
        page_id,
    )


async def get_by_id_with_context(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
) -> asyncpg.Record | None:
    """Get a page by ID with document and project context for navigation.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        asyncpg.Record or None: Page record with project_id, project_name, document_filename.
    """
    return await pool.fetchrow(
        """
        SELECT p.id, p.document_id, p.page_no, p.width, p.height, p.image_path,
               p.annotation_data, p.auto_extracted_data, p.status, p.assigned_to,
               p.locked_at, p.updated_at,
               d.filename AS document_filename,
               d.project_id AS project_id,
               pr.name AS project_name
        FROM pages p
        JOIN documents d ON p.document_id = d.id
        JOIN projects pr ON d.project_id = pr.id
        WHERE p.id = $1
        """,
        page_id,
    )


async def list_by_document(pool: asyncpg.Pool, document_id: uuid.UUID) -> list[asyncpg.Record]:
    """List all pages for a document.

    Args:
        pool: Database connection pool.
        document_id: Parent document UUID.

    Returns:
        list[asyncpg.Record]: List of page records (without annotation_data for performance).
    """
    return await pool.fetch(
        """
        SELECT id, page_no, width, height, status, assigned_to, updated_at
        FROM pages WHERE document_id = $1
        ORDER BY page_no
        """,
        document_id,
    )


async def update_annotation(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    annotation_data: dict,
) -> asyncpg.Record | None:
    """Update annotation data for a page.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        annotation_data: OmniDocBench annotation JSON.

    Returns:
        asyncpg.Record or None: Updated page record.
    """
    return await pool.fetchrow(
        """
        UPDATE pages
        SET annotation_data = $1::jsonb, updated_at = NOW()
        WHERE id = $2
        RETURNING id, document_id, page_no, width, height, image_path,
                  annotation_data, auto_extracted_data, status, assigned_to,
                  locked_at, updated_at
        """,
        json.dumps(annotation_data),
        page_id,
    )


async def update_page_attribute(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    page_attribute: dict,
) -> asyncpg.Record | None:
    """Update page_attribute within annotation_data using jsonb_set.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        page_attribute: Page attribute dictionary.

    Returns:
        asyncpg.Record or None: Updated page record.
    """
    return await pool.fetchrow(
        """
        UPDATE pages
        SET annotation_data = jsonb_set(
            COALESCE(annotation_data, '{}'::jsonb),
            '{page_attribute}',
            $1::jsonb
        ),
        updated_at = NOW()
        WHERE id = $2
        RETURNING id, document_id, page_no, width, height, image_path,
                  annotation_data, auto_extracted_data, status, assigned_to,
                  locked_at, updated_at
        """,
        json.dumps(page_attribute),
        page_id,
    )


async def add_element(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    element: dict,
) -> asyncpg.Record | None:
    """Add a layout element to annotation_data.layout_dets.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        element: Layout element dictionary.

    Returns:
        asyncpg.Record or None: Updated page record.
    """
    return await pool.fetchrow(
        """
        UPDATE pages
        SET annotation_data = jsonb_set(
            COALESCE(annotation_data, '{"layout_dets": []}'::jsonb),
            '{layout_dets}',
            COALESCE(annotation_data->'layout_dets', '[]'::jsonb) || $1::jsonb
        ),
        updated_at = NOW()
        WHERE id = $2
        RETURNING id, document_id, page_no, width, height, image_path,
                  annotation_data, auto_extracted_data, status, assigned_to,
                  locked_at, updated_at
        """,
        json.dumps(element),
        page_id,
    )


async def delete_element(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    anno_id: int,
) -> asyncpg.Record | None:
    """Delete a layout element by anno_id from annotation_data.layout_dets.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        anno_id: Annotation ID of the element to remove.

    Returns:
        asyncpg.Record or None: Updated page record.
    """
    return await pool.fetchrow(
        """
        UPDATE pages
        SET annotation_data = jsonb_set(
            annotation_data,
            '{layout_dets}',
            (
                SELECT COALESCE(jsonb_agg(elem), '[]'::jsonb)
                FROM jsonb_array_elements(annotation_data->'layout_dets') AS elem
                WHERE (elem->>'anno_id')::int != $1
            )
        ),
        updated_at = NOW()
        WHERE id = $2
        RETURNING id, document_id, page_no, width, height, image_path,
                  annotation_data, auto_extracted_data, status, assigned_to,
                  locked_at, updated_at
        """,
        anno_id,
        page_id,
    )


async def accept_auto_extracted(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
) -> asyncpg.Record | None:
    """Copy auto_extracted_data to annotation_data if annotation is empty.

    Only updates when annotation_data has no layout_dets or is NULL/empty.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        asyncpg.Record or None: Updated page record, or None if preconditions not met.
    """
    return await pool.fetchrow(
        """
        UPDATE pages
        SET annotation_data = auto_extracted_data, updated_at = NOW()
        WHERE id = $1
          AND auto_extracted_data IS NOT NULL
          AND (
            annotation_data IS NULL
            OR annotation_data = '{}'::jsonb
            OR NOT (annotation_data ? 'layout_dets')
            OR jsonb_array_length(COALESCE(annotation_data->'layout_dets', '[]'::jsonb)) = 0
          )
        RETURNING id, document_id, page_no, width, height, image_path,
                  annotation_data, auto_extracted_data, status, assigned_to,
                  locked_at, updated_at
        """,
        page_id,
    )


async def get_all_by_project(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> list[asyncpg.Record]:
    """Get all pages for a project with annotation data (for export).

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        list[asyncpg.Record]: All pages with full annotation data.
    """
    return await pool.fetch(
        """
        SELECT p.id, p.page_no, p.width, p.height, p.image_path,
               p.annotation_data
        FROM pages p
        JOIN documents d ON p.document_id = d.id
        WHERE d.project_id = $1
        ORDER BY d.created_at, p.page_no
        """,
        project_id,
    )
