"""User management endpoints."""

from fastapi import APIRouter, HTTPException, status

from saegim.core.database import get_pool
from saegim.repositories import user_repo
from saegim.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post('/users', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate) -> UserResponse:
    """Create a new user.

    Args:
        body: User creation data.

    Returns:
        UserResponse: Created user.

    Raises:
        HTTPException: If email already exists.
    """
    pool = get_pool()
    try:
        record = await user_repo.create(pool, name=body.name, email=body.email, role=body.role)
    except Exception as e:
        if 'unique' in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='User with this email already exists',
            ) from e
        raise
    return UserResponse(**dict(record))


@router.get('/users', response_model=list[UserResponse])
async def list_users() -> list[UserResponse]:
    """List all users.

    Returns:
        list[UserResponse]: All users.
    """
    pool = get_pool()
    records = await user_repo.list_all(pool)
    return [UserResponse(**dict(r)) for r in records]
