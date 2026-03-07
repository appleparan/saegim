"""Task workflow repository with raw SQL queries."""

import json
import uuid

import asyncpg

# Lock timeout in minutes
LOCK_TIMEOUT_MINUTES = 30


async def get_project_id_for_page(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
) -> uuid.UUID | None:
    """Get the project ID for a page via its document.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        Project UUID or None if page not found.
    """
    return await pool.fetchval(
        """
        SELECT d.project_id
        FROM pages p
        JOIN documents d ON p.document_id = d.id
        WHERE p.id = $1
        """,
        page_id,
    )


async def get_project_member_role(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> str | None:
    """Get a user's role in a project from project_members.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.
        user_id: User UUID.

    Returns:
        Role string ('owner', 'annotator', 'reviewer') or None if not a member.
    """
    return await pool.fetchval(
        """
        SELECT role FROM project_members
        WHERE project_id = $1 AND user_id = $2
        """,
        project_id,
        user_id,
    )


async def assign_page(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    user_id: uuid.UUID,
    assigned_by_id: uuid.UUID,
) -> asyncpg.Record | None:
    """Assign a page to a user, setting status to in_progress.

    Only works when the page status is 'pending' or 'in_progress' (reassignment).

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        user_id: User UUID to assign.
        assigned_by_id: User UUID performing the assignment.

    Returns:
        Updated page record, or None if page not found or invalid state.
    """
    async with pool.acquire() as conn, conn.transaction():
        record = await conn.fetchrow(
            """
            UPDATE pages
            SET assigned_to = $1, status = 'in_progress', updated_at = NOW()
            WHERE id = $2
              AND status IN ('pending', 'in_progress')
            RETURNING id, document_id, page_no, width, height, image_path,
                      annotation_data, auto_extracted_data, status, assigned_to,
                      locked_at, updated_at
            """,
            user_id,
            page_id,
        )
        if record is not None:
            await _record_history(conn, page_id, assigned_by_id, 'assigned')
        return record


async def submit_page(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    user_id: uuid.UUID,
) -> asyncpg.Record | None:
    """Submit a page for review, setting status to submitted.

    Only works when status is 'in_progress' and assigned_to matches user_id.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        user_id: User UUID submitting the page.

    Returns:
        Updated page record, or None if preconditions not met.
    """
    async with pool.acquire() as conn, conn.transaction():
        record = await conn.fetchrow(
            """
            UPDATE pages
            SET status = 'submitted', locked_at = NULL, updated_at = NOW()
            WHERE id = $1
              AND status = 'in_progress'
              AND assigned_to = $2
            RETURNING id, document_id, page_no, width, height, image_path,
                      annotation_data, auto_extracted_data, status, assigned_to,
                      locked_at, updated_at
            """,
            page_id,
            user_id,
        )
        if record is not None:
            await _record_history(conn, page_id, user_id, 'submitted')
        return record


async def review_page(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    action: str,
    comment: str | None = None,
) -> asyncpg.Record | None:
    """Review a submitted page (approve or reject).

    Approved → status='reviewed', Rejected → status='in_progress' (rework).

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        reviewer_id: Reviewer's user UUID.
        action: 'approved' or 'rejected'.
        comment: Optional review comment.

    Returns:
        Updated page record, or None if preconditions not met.
    """
    new_status = 'reviewed' if action == 'approved' else 'in_progress'
    history_action = 'approved' if action == 'approved' else 'rejected'

    async with pool.acquire() as conn, conn.transaction():
        record = await conn.fetchrow(
            """
            UPDATE pages
            SET status = $1, updated_at = NOW()
            WHERE id = $2
              AND status = 'submitted'
            RETURNING id, document_id, page_no, width, height, image_path,
                      annotation_data, auto_extracted_data, status, assigned_to,
                      locked_at, updated_at
            """,
            new_status,
            page_id,
        )
        if record is not None:
            snapshot = {'comment': comment} if comment else None
            await _record_history(conn, page_id, reviewer_id, history_action, snapshot=snapshot)
        return record


async def acquire_lock(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    user_id: uuid.UUID,
) -> asyncpg.Record | None:
    """Acquire an edit lock on a page.

    Succeeds if: no lock exists, lock belongs to same user, or lock timed out (>30 min).

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        user_id: User UUID requesting the lock.

    Returns:
        Updated page record, or None if locked by another user.
    """
    return await pool.fetchrow(
        f"""
        UPDATE pages
        SET locked_at = NOW(), updated_at = NOW()
        WHERE id = $1
          AND (
            locked_at IS NULL
            OR assigned_to = $2
            OR locked_at < NOW() - INTERVAL '{LOCK_TIMEOUT_MINUTES} minutes'
          )
        RETURNING id, document_id, page_no, width, height, image_path,
                  annotation_data, auto_extracted_data, status, assigned_to,
                  locked_at, updated_at
        """,  # noqa: S608
        page_id,
        user_id,
    )


async def release_lock(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
) -> asyncpg.Record | None:
    """Release the edit lock on a page.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.

    Returns:
        Updated page record, or None if page not found.
    """
    return await pool.fetchrow(
        """
        UPDATE pages
        SET locked_at = NULL, updated_at = NOW()
        WHERE id = $1
        RETURNING id, document_id, page_no, width, height, image_path,
                  annotation_data, auto_extracted_data, status, assigned_to,
                  locked_at, updated_at
        """,
        page_id,
    )


async def get_user_tasks(
    pool: asyncpg.Pool,
    user_id: uuid.UUID,
) -> list[asyncpg.Record]:
    """Get all pages assigned to a user with project/document context.

    Args:
        pool: Database connection pool.
        user_id: User UUID.

    Returns:
        List of task records.
    """
    return await pool.fetch(
        """
        SELECT p.id AS page_id, p.page_no, p.status,
               d.id AS document_id, d.filename AS document_filename,
               pr.id AS project_id, pr.name AS project_name,
               th.created_at AS assigned_at
        FROM pages p
        JOIN documents d ON p.document_id = d.id
        JOIN projects pr ON d.project_id = pr.id
        LEFT JOIN LATERAL (
            SELECT created_at FROM task_history
            WHERE page_id = p.id AND action = 'assigned'
            ORDER BY created_at DESC
            LIMIT 1
        ) th ON true
        WHERE p.assigned_to = $1
          AND p.status IN ('in_progress', 'submitted')
        ORDER BY th.created_at DESC NULLS LAST
        """,
        user_id,
    )


async def get_review_queue(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> list[asyncpg.Record]:
    """Get all submitted pages for a project (review queue).

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        List of review queue records.
    """
    return await pool.fetch(
        """
        SELECT p.id AS page_id, p.page_no,
               d.id AS document_id, d.filename AS document_filename,
               p.assigned_to,
               u.name AS assigned_to_name,
               th.created_at AS submitted_at
        FROM pages p
        JOIN documents d ON p.document_id = d.id
        LEFT JOIN users u ON p.assigned_to = u.id
        LEFT JOIN LATERAL (
            SELECT created_at FROM task_history
            WHERE page_id = p.id AND action = 'submitted'
            ORDER BY created_at DESC
            LIMIT 1
        ) th ON true
        WHERE d.project_id = $1
          AND p.status = 'submitted'
        ORDER BY th.created_at ASC NULLS LAST
        """,
        project_id,
    )


async def record_history(
    pool: asyncpg.Pool,
    page_id: uuid.UUID,
    user_id: uuid.UUID,
    action: str,
    snapshot: dict | None = None,
) -> asyncpg.Record:
    """Record a task history entry (public interface).

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        user_id: User UUID.
        action: Action string (assigned, started, saved, submitted, approved, rejected).
        snapshot: Optional JSON snapshot.

    Returns:
        Created task_history record.
    """
    return await pool.fetchrow(
        """
        INSERT INTO task_history (page_id, user_id, action, snapshot)
        VALUES ($1, $2, $3, $4::jsonb)
        RETURNING id, page_id, user_id, action, snapshot, created_at
        """,
        page_id,
        user_id,
        action,
        json.dumps(snapshot) if snapshot else None,
    )


async def _record_history(
    conn: asyncpg.Connection,
    page_id: uuid.UUID,
    user_id: uuid.UUID,
    action: str,
    snapshot: dict | None = None,
) -> asyncpg.Record:
    """Record a task history entry within a transaction.

    Args:
        conn: Database connection (within transaction).
        page_id: Page UUID.
        user_id: User UUID.
        action: Action string.
        snapshot: Optional JSON snapshot.

    Returns:
        Created task_history record.
    """
    return await conn.fetchrow(
        """
        INSERT INTO task_history (page_id, user_id, action, snapshot)
        VALUES ($1, $2, $3, $4::jsonb)
        RETURNING id, page_id, user_id, action, snapshot, created_at
        """,
        page_id,
        user_id,
        action,
        json.dumps(snapshot) if snapshot else None,
    )
