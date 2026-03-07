"""Admin-only endpoints for user and project management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from saegim.api.deps import require_admin
from saegim.core.database import get_pool
from saegim.repositories import project_repo, user_repo
from saegim.schemas.project import ProjectResponse
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
    """Update a user's role (admin only).

    Args:
        user_id: Target user UUID.
        body: Fields to update.
        _: Current admin user (injected by dependency).

    Returns:
        UserResponse: Updated user.

    Raises:
        HTTPException: 404 if user not found, 400 if no fields to update.
    """
    pool = get_pool()

    if body.role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No fields to update',
        )

    record = await user_repo.update_role(pool, user_id, str(body.role))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    return UserResponse.model_validate(dict(record))


@router.get('/admin/projects', response_model=list[ProjectResponse])
async def admin_list_projects(
    _: UserResponse = Depends(require_admin),  # noqa: B008
) -> list[ProjectResponse]:
    """List all projects (admin only).

    Args:
        _: Current admin user (injected by dependency).

    Returns:
        list[ProjectResponse]: All projects.
    """
    pool = get_pool()
    records = await project_repo.list_all(pool)
    return [ProjectResponse.model_validate(dict(r)) for r in records]
