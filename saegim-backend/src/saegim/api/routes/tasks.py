"""Task management endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends

from saegim.api.deps import get_current_user
from saegim.core.database import get_pool
from saegim.repositories import task_repo
from saegim.schemas.task import ReviewQueueItem, TaskResponse
from saegim.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/users/me/tasks', response_model=list[TaskResponse])
async def get_my_tasks(
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> list[TaskResponse]:
    """Get the current user's assigned tasks.

    Args:
        current_user: Authenticated user.

    Returns:
        List of assigned task items.
    """
    pool = get_pool()
    records = await task_repo.get_user_tasks(pool, current_user.id)
    return [TaskResponse(**dict(r)) for r in records]


@router.get('/projects/{project_id}/review-queue', response_model=list[ReviewQueueItem])
async def get_review_queue(
    project_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),  # noqa: ARG001, B008
) -> list[ReviewQueueItem]:
    """Get the review queue for a project (submitted pages).

    Args:
        project_id: Project UUID.
        current_user: Authenticated user (required for auth).

    Returns:
        List of review queue items.
    """
    pool = get_pool()
    records = await task_repo.get_review_queue(pool, project_id)
    return [ReviewQueueItem(**dict(r)) for r in records]
