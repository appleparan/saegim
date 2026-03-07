"""Project progress board repository with aggregate queries."""

import uuid

import asyncpg


async def get_project_status_summary(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> asyncpg.Record:
    """Get overall page status counts for a project.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        asyncpg.Record: Row with total_pages, pending, in_progress,
            submitted, reviewed counts.
    """
    return await pool.fetchrow(
        """
        SELECT
            COUNT(*) AS total_pages,
            COUNT(*) FILTER (WHERE pg.status = 'pending') AS pending,
            COUNT(*) FILTER (WHERE pg.status = 'in_progress') AS in_progress,
            COUNT(*) FILTER (WHERE pg.status = 'submitted') AS submitted,
            COUNT(*) FILTER (WHERE pg.status = 'reviewed') AS reviewed
        FROM pages pg
        JOIN documents d ON pg.document_id = d.id
        WHERE d.project_id = $1
        """,
        project_id,
    )


async def get_document_progress(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> list[asyncpg.Record]:
    """Get per-document page status counts for a project.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        list[asyncpg.Record]: Documents with total_pages and status counts.
    """
    return await pool.fetch(
        """
        SELECT
            d.id AS document_id,
            d.filename,
            COUNT(pg.id) AS total_pages,
            COUNT(pg.id) FILTER (WHERE pg.status = 'pending') AS pending,
            COUNT(pg.id) FILTER (WHERE pg.status = 'in_progress') AS in_progress,
            COUNT(pg.id) FILTER (WHERE pg.status = 'submitted') AS submitted,
            COUNT(pg.id) FILTER (WHERE pg.status = 'reviewed') AS reviewed
        FROM documents d
        LEFT JOIN pages pg ON pg.document_id = d.id
        WHERE d.project_id = $1
        GROUP BY d.id, d.filename
        ORDER BY d.filename ASC
        """,
        project_id,
    )


async def get_member_activity(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> list[asyncpg.Record]:
    """Get per-member page activity for a project.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        list[asyncpg.Record]: Members with assigned/in_progress/submitted/reviewed counts.
    """
    return await pool.fetch(
        """
        SELECT
            pm.user_id,
            u.name AS user_name,
            pm.role,
            COALESCE(stats.assigned_pages, 0) AS assigned_pages,
            COALESCE(stats.in_progress_pages, 0) AS in_progress_pages,
            COALESCE(stats.submitted_pages, 0) AS submitted_pages,
            COALESCE(stats.reviewed_pages, 0) AS reviewed_pages
        FROM project_members pm
        JOIN users u ON u.id = pm.user_id
        LEFT JOIN (
            SELECT
                pg.assigned_to AS user_id,
                COUNT(*) AS assigned_pages,
                COUNT(*) FILTER (WHERE pg.status = 'in_progress') AS in_progress_pages,
                COUNT(*) FILTER (WHERE pg.status = 'submitted') AS submitted_pages,
                COUNT(*) FILTER (WHERE pg.status = 'reviewed') AS reviewed_pages
            FROM pages pg
            JOIN documents d ON pg.document_id = d.id
            WHERE d.project_id = $1
              AND pg.assigned_to IS NOT NULL
            GROUP BY pg.assigned_to
        ) stats ON stats.user_id = pm.user_id
        WHERE pm.project_id = $1
        ORDER BY u.name ASC
        """,
        project_id,
    )
