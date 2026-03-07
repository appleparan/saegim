"""Admin dashboard repository with aggregate queries."""

import asyncpg


async def get_system_stats(pool: asyncpg.Pool) -> asyncpg.Record:
    """Get system-wide statistics for admin dashboard.

    Args:
        pool: Database connection pool.

    Returns:
        asyncpg.Record: Row with total_users, active_users, total_projects,
            total_pages, completed_pages, submitted_pages.
    """
    return await pool.fetchrow(
        """
        SELECT
            (SELECT COUNT(*) FROM users) AS total_users,
            (SELECT COUNT(*) FROM users WHERE is_active = TRUE) AS active_users,
            (SELECT COUNT(*) FROM projects) AS total_projects,
            (SELECT COUNT(*) FROM pages) AS total_pages,
            (SELECT COUNT(*) FROM pages WHERE status = 'reviewed') AS completed_pages,
            (SELECT COUNT(*) FROM pages WHERE status = 'submitted') AS submitted_pages
        """,
    )


async def list_projects_with_stats(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """List all projects with member count and page statistics.

    Args:
        pool: Database connection pool.

    Returns:
        list[asyncpg.Record]: Projects with member_count, total_pages,
            completed_pages, submitted_pages.
    """
    return await pool.fetch(
        """
        SELECT
            p.id,
            p.name,
            p.description,
            p.created_at,
            COALESCE(pm_counts.member_count, 0) AS member_count,
            COALESCE(page_stats.total_pages, 0) AS total_pages,
            COALESCE(page_stats.completed_pages, 0) AS completed_pages,
            COALESCE(page_stats.submitted_pages, 0) AS submitted_pages
        FROM projects p
        LEFT JOIN (
            SELECT project_id, COUNT(*) AS member_count
            FROM project_members
            GROUP BY project_id
        ) pm_counts ON pm_counts.project_id = p.id
        LEFT JOIN (
            SELECT d.project_id,
                   COUNT(*) AS total_pages,
                   COUNT(*) FILTER (WHERE pg.status = 'reviewed') AS completed_pages,
                   COUNT(*) FILTER (WHERE pg.status = 'submitted') AS submitted_pages
            FROM pages pg
            JOIN documents d ON pg.document_id = d.id
            GROUP BY d.project_id
        ) page_stats ON page_stats.project_id = p.id
        ORDER BY p.created_at DESC
        """,
    )
