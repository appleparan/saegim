"""Authentication endpoints (register, login, refresh, logout)."""

import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status

from saegim.api.deps import (
    clear_refresh_cookie,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    rotate_refresh_token,
    set_refresh_cookie,
    validate_refresh_token,
    verify_password,
)
from saegim.api.settings import get_settings
from saegim.core.database import get_pool
from saegim.repositories import refresh_token_repo, user_repo
from saegim.schemas.auth import (
    CredentialUpdateRequest,
    LoginIdCheckResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from saegim.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/auth/check-login-id', response_model=LoginIdCheckResponse)
async def check_login_id(
    login_id: str = Query(min_length=3, max_length=64),
) -> LoginIdCheckResponse:
    """Check whether a login ID is available."""
    pool = get_pool()
    available = not await user_repo.is_login_id_taken(pool, login_id)
    return LoginIdCheckResponse(login_id=login_id, available=available)


@router.post('/auth/register', response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response) -> TokenResponse:
    """Register a new user. First user automatically becomes admin.

    Args:
        body: Registration data (name, login_id, password).
        response: FastAPI response for setting cookies.

    Returns:
        TokenResponse: JWT access token. Refresh token set as HttpOnly cookie.

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

    raw_refresh, _ref_record = await create_refresh_token(record['id'], settings, pool)
    set_refresh_cookie(response, raw_refresh, settings)

    return TokenResponse(
        access_token=token,
        must_change_password=bool(record['must_change_password']),
    )


@router.post('/auth/login', response_model=TokenResponse)
async def login(body: LoginRequest, response: Response) -> TokenResponse:
    """Login with login ID and password.

    Args:
        body: Login credentials.
        response: FastAPI response for setting cookies.

    Returns:
        TokenResponse: JWT access token. Refresh token set as HttpOnly cookie.

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

    raw_refresh, _ref_record = await create_refresh_token(record['id'], settings, pool)
    set_refresh_cookie(response, raw_refresh, settings)

    return TokenResponse(
        access_token=token,
        must_change_password=bool(record['must_change_password']),
    )


@router.post('/auth/refresh', response_model=TokenResponse)
async def refresh(
    response: Response,
    saegim_refresh_token: str | None = Cookie(default=None),
) -> TokenResponse:
    """Refresh access token using refresh token cookie.

    Implements token rotation with grace period for multi-tab support.

    Args:
        response: FastAPI response for setting new cookie.
        saegim_refresh_token: Refresh token from HttpOnly cookie.

    Returns:
        TokenResponse: New JWT access token. New refresh token set as cookie.

    Raises:
        HTTPException: 401 if refresh token is missing, invalid, or stolen.
    """
    if saegim_refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing refresh token',
        )

    pool = get_pool()
    settings = get_settings()

    user_id, family_id = await validate_refresh_token(saegim_refresh_token, pool, settings)

    new_raw, _new_record = await rotate_refresh_token(
        saegim_refresh_token, user_id, family_id, settings, pool
    )
    set_refresh_cookie(response, new_raw, settings)

    record = await user_repo.get_by_id(pool, user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found',
        )

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


@router.post('/auth/logout', status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    saegim_refresh_token: str | None = Cookie(default=None),
) -> None:
    """Logout by revoking the refresh token family and clearing the cookie.

    Args:
        response: FastAPI response for clearing cookie.
        saegim_refresh_token: Refresh token from HttpOnly cookie.
    """
    settings = get_settings()

    if saegim_refresh_token is not None:
        pool = get_pool()
        from saegim.api.deps import _hash_token

        token_hash = _hash_token(saegim_refresh_token)
        record = await refresh_token_repo.get_by_token_hash(pool, token_hash)
        if record is not None:
            await refresh_token_repo.revoke_family(pool, record['family_id'])

    clear_refresh_cookie(response, settings)


@router.patch('/auth/me/credentials', response_model=TokenResponse)
async def update_my_credentials(
    body: CredentialUpdateRequest,
    response: Response,
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> TokenResponse:
    """Update current user's login_id/email/password.

    Revokes all existing refresh tokens for the user and issues new ones.
    """
    pool = get_pool()
    settings = get_settings()

    record = await user_repo.get_with_password_by_id(pool, current_user.id)
    invalid_msg = 'Invalid current password'
    if record is None or record['password_hash'] is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=invalid_msg)
    if not verify_password(body.current_password, record['password_hash']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=invalid_msg)

    target_login_id = body.login_id if body.login_id is not None else record['login_id']
    target_email = str(body.email) if body.email is not None else record['email']

    if await user_repo.is_login_id_taken(pool, target_login_id, exclude_user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User with this login ID already exists',
        )
    if await user_repo.is_email_taken(pool, target_email, exclude_user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User with this email already exists',
        )

    password_hash = (
        hash_password(body.new_password)
        if body.new_password is not None
        else record['password_hash']
    )
    must_change_password = (
        False if body.new_password is not None else record['must_change_password']
    )

    updated = await user_repo.update_credentials(
        pool,
        current_user.id,
        login_id=target_login_id,
        email=target_email,
        password_hash=password_hash,
        must_change_password=must_change_password,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    # Revoke all existing refresh tokens and issue new one
    await refresh_token_repo.revoke_all_for_user(pool, current_user.id)
    raw_refresh, _ref_record = await create_refresh_token(current_user.id, settings, pool)
    set_refresh_cookie(response, raw_refresh, settings)

    token = create_access_token(
        str(updated['id']),
        updated['role'],
        settings,
        must_change_password=bool(updated['must_change_password']),
    )
    return TokenResponse(
        access_token=token,
        must_change_password=bool(updated['must_change_password']),
    )
