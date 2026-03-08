"""User management endpoints."""

from fastapi import APIRouter, Depends

from saegim.api.deps import get_current_user
from saegim.core.database import get_pool
from saegim.repositories import user_repo
from saegim.schemas.user import UserResponse

router = APIRouter()


@router.get('/users', response_model=list[UserResponse])
async def list_users(
    _: UserResponse = Depends(get_current_user),  # noqa: B008
) -> list[UserResponse]:
    """List all users (requires authentication).

    Args:
        _: Current authenticated user (injected by dependency).

    Returns:
        list[UserResponse]: All users.
    """
    pool = get_pool()
    records = await user_repo.list_all(pool)
    return [UserResponse.model_validate(dict(r)) for r in records]
