"""Admin-only endpoints for user and project management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from saegim.api.deps import require_admin
from saegim.core.database import get_pool
from saegim.repositories import admin_repo, user_repo
from saegim.schemas.admin import AdminProjectResponse, AdminStatsResponse
from saegim.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get('/admin/users', response_model=list[UserResponse])
async def admin_list_users(
    _: UserResponse = Depends(require_admin),  # noqa: B008
) -> list[UserResponse]:
    """List all users (admin only).

    Args:
        _: Current admin user (injected by dependency).

    Returns:
        list[UserResponse]: All users.
    """
    pool = get_pool()
    records = await user_repo.list_all(pool)
    return [UserResponse.model_validate(dict(r)) for r in records]


@router.patch('/admin/users/{user_id}', response_model=UserResponse)
async def admin_update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    _: UserResponse = Depends(require_admin),  # noqa: B008
) -> UserResponse:
    """Update a user's role and/or active status (admin only).

    Args:
        user_id: Target user UUID.
        body: Fields to update (role and/or is_active).
        _: Current admin user (injected by dependency).

    Returns:
        UserResponse: Updated user.

    Raises:
        HTTPException: 404 if user not found, 400 if no fields to update.
    """
    pool = get_pool()

    if body.role is None and body.is_active is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No fields to update',
        )

    record = await user_repo.update_user(
        pool,
        user_id,
        role=str(body.role) if body.role is not None else None,
        is_active=body.is_active,
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    return UserResponse.model_validate(dict(record))


@router.get('/admin/projects', response_model=list[AdminProjectResponse])
async def admin_list_projects(
    _: UserResponse = Depends(require_admin),  # noqa: B008
) -> list[AdminProjectResponse]:
    """List all projects with stats (admin only).

    Args:
        _: Current admin user (injected by dependency).

    Returns:
        list[AdminProjectResponse]: All projects with member/page stats.
    """
    pool = get_pool()
    records = await admin_repo.list_projects_with_stats(pool)
    return [AdminProjectResponse.model_validate(dict(r)) for r in records]


@router.get('/admin/stats', response_model=AdminStatsResponse)
async def admin_get_stats(
    _: UserResponse = Depends(require_admin),  # noqa: B008
) -> AdminStatsResponse:
    """Get system-wide statistics (admin only).

    Args:
        _: Current admin user (injected by dependency).

    Returns:
        AdminStatsResponse: System statistics.
    """
    pool = get_pool()
    record = await admin_repo.get_system_stats(pool)
    row = dict(record)

    total = row['total_pages']
    completed = row['completed_pages']
    completion_rate = (completed / total * 100) if total > 0 else 0.0

    return AdminStatsResponse(
        total_users=row['total_users'],
        active_users=row['active_users'],
        total_projects=row['total_projects'],
        total_pages=total,
        completed_pages=completed,
        submitted_pages=row['submitted_pages'],
        completion_rate=round(completion_rate, 1),
    )
