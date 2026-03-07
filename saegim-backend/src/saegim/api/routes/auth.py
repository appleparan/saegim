"""Authentication endpoints (register, login)."""

import logging

from fastapi import APIRouter, HTTPException, status

from saegim.api.deps import create_access_token, hash_password, verify_password
from saegim.api.settings import get_settings
from saegim.core.database import get_pool
from saegim.repositories import user_repo
from saegim.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/auth/register', response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest) -> TokenResponse:
    """Register a new user. First user automatically becomes admin.

    Args:
        body: Registration data (name, login_id, password).

    Returns:
        TokenResponse: JWT access token.

    Raises:
        HTTPException: 409 if login_id already taken.
    """
    pool = get_pool()
    settings = get_settings()

    count = await user_repo.count_all(pool)
    role = 'admin' if count == 0 else 'annotator'

    password_hashed = hash_password(body.password)

    try:
        record = await user_repo.create_with_password(
            pool,
            name=body.name,
            login_id=body.login_id,
            password_hash=password_hashed,
            role=role,
        )
    except Exception as e:
        if 'unique' in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='User with this login ID already exists',
            ) from e
        raise

    token = create_access_token(
        str(record['id']),
        role,
        settings,
        must_change_password=bool(record['must_change_password']),
    )
    return TokenResponse(
        access_token=token,
        must_change_password=bool(record['must_change_password']),
    )


@router.post('/auth/login', response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Login with login ID and password.

    Args:
        body: Login credentials.

    Returns:
        TokenResponse: JWT access token.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    pool = get_pool()
    settings = get_settings()

    record = await user_repo.get_by_login_id(pool, body.login_id)

    invalid_msg = 'Invalid ID or password'
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=invalid_msg)

    if record['password_hash'] is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=invalid_msg)

    if not verify_password(body.password, record['password_hash']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=invalid_msg)

    token = create_access_token(
        str(record['id']),
        record['role'],
        settings,
        must_change_password=bool(record['must_change_password']),
    )
    return TokenResponse(
        access_token=token,
        must_change_password=bool(record['must_change_password']),
    )
