"""FastAPI dependency injection for authentication and authorization."""

import datetime
import hashlib
import logging
import secrets
import uuid

import asyncpg
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from saegim.api.settings import Settings, get_settings
from saegim.core.database import get_pool
from saegim.repositories import project_member_repo, refresh_token_repo, user_repo
from saegim.schemas.user import UserResponse

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer()


def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        plain: Plain-text password.

    Returns:
        str: Bcrypt hash string.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain.encode(), salt)
    return hashed.decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain: Plain-text password to verify.
        hashed: Stored bcrypt hash.

    Returns:
        bool: True if password matches.
    """
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    user_id: str,
    role: str,
    settings: Settings,
    must_change_password: bool = False,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User UUID string.
        role: User role string.
        settings: Application settings.
        must_change_password: Whether password change is required.

    Returns:
        str: Encoded JWT token.
    """
    expire = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        'sub': user_id,
        'role': role,
        'must_change_password': must_change_password,
        'exp': expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> UserResponse:
    """Decode JWT and return current authenticated user.

    Args:
        credentials: HTTP Bearer credentials from Authorization header.
        settings: Application settings.

    Returns:
        UserResponse: Authenticated user.

    Raises:
        HTTPException: 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token has expired',
            headers={'WWW-Authenticate': 'Bearer'},
        ) from e
    except jwt.InvalidTokenError as e:
        raise credentials_exception from e

    user_id: str | None = payload.get('sub')
    if user_id is None:
        raise credentials_exception

    pool = get_pool()
    record = await user_repo.get_by_id(pool, uuid.UUID(user_id))
    if record is None:
        raise credentials_exception

    return UserResponse.model_validate(dict(record))


async def require_admin(
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> UserResponse:
    """Require admin role for the current user.

    Args:
        current_user: Current authenticated user.

    Returns:
        UserResponse: Admin user.

    Raises:
        HTTPException: 403 if user is not admin.
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin access required',
        )
    return current_user


async def require_project_member(
    project_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> UserResponse:
    """Require the user to be a member of the project.

    Admin users bypass this check entirely.

    Args:
        project_id: Project UUID from path parameter.
        current_user: Current authenticated user.

    Returns:
        UserResponse: Authorized user.

    Raises:
        HTTPException: 403 if user is not a project member and not admin.
    """
    if current_user.role == 'admin':
        return current_user

    pool = get_pool()
    member_role = await project_member_repo.get_role(pool, project_id, current_user.id)
    if member_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not a project member',
        )
    return current_user


# ---------------------------------------------------------------------------
# Refresh Token helpers
# ---------------------------------------------------------------------------


def _hash_token(raw_token: str) -> str:
    """Hash a raw refresh token using SHA-256.

    Args:
        raw_token: Raw opaque token string.

    Returns:
        str: Hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def create_refresh_token(
    user_id: uuid.UUID,
    settings: Settings,
    pool: asyncpg.Pool,
    *,
    family_id: uuid.UUID | None = None,
) -> tuple[str, asyncpg.Record]:
    """Generate and store a new refresh token.

    Args:
        user_id: Owner user UUID.
        settings: Application settings.
        pool: Database connection pool.
        family_id: Existing family UUID for rotation. None creates a new family.

    Returns:
        tuple: (raw_token, db_record).
    """
    raw_token = secrets.token_hex(32)
    token_hash = _hash_token(raw_token)
    resolved_family_id = family_id or uuid.uuid4()
    expires_at = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(
        days=settings.refresh_token_expire_days,
    )
    record = await refresh_token_repo.create(
        pool, user_id, token_hash, resolved_family_id, expires_at
    )
    return raw_token, record


async def validate_refresh_token(
    raw_token: str,
    pool: asyncpg.Pool,
    settings: Settings,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Validate a refresh token and return user/family IDs.

    Implements grace period logic for token rotation:
    - Active token: valid
    - Revoked within grace period: valid (multi-tab support)
    - Revoked past grace period: theft detected, revoke family

    Args:
        raw_token: Raw opaque token string.
        pool: Database connection pool.
        settings: Application settings.

    Returns:
        tuple: (user_id, family_id).

    Raises:
        HTTPException: 401 if token is invalid, expired, or stolen.
    """
    token_hash = _hash_token(raw_token)
    record = await refresh_token_repo.get_by_token_hash(pool, token_hash)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid refresh token',
        )

    now = datetime.datetime.now(tz=datetime.UTC)

    if record['expires_at'] < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh token expired',
        )

    revoked_at = record['revoked_at']
    if revoked_at is not None:
        grace_deadline = revoked_at + datetime.timedelta(
            seconds=settings.refresh_grace_period_seconds,
        )
        if now > grace_deadline:
            logger.warning(
                'Refresh token reuse detected past grace period for user %s, revoking family %s',
                record['user_id'],
                record['family_id'],
            )
            await refresh_token_repo.revoke_family(pool, record['family_id'])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token reuse detected',
            )

    return record['user_id'], record['family_id']


async def rotate_refresh_token(
    raw_token: str,
    user_id: uuid.UUID,
    family_id: uuid.UUID,
    settings: Settings,
    pool: asyncpg.Pool,
) -> tuple[str, asyncpg.Record]:
    """Revoke old refresh token and issue a new one in the same family.

    Args:
        raw_token: Current raw token to revoke.
        user_id: Owner user UUID.
        family_id: Token family UUID.
        settings: Application settings.
        pool: Database connection pool.

    Returns:
        tuple: (new_raw_token, new_db_record).
    """
    old_hash = _hash_token(raw_token)
    old_record = await refresh_token_repo.get_by_token_hash(pool, old_hash)
    if old_record is not None and old_record['revoked_at'] is None:
        await refresh_token_repo.revoke(pool, old_record['id'])

    return await create_refresh_token(user_id, settings, pool, family_id=family_id)


def set_refresh_cookie(response: JSONResponse, raw_token: str, settings: Settings) -> None:
    """Set refresh token as HttpOnly cookie on the response.

    Args:
        response: FastAPI response object.
        raw_token: Raw refresh token string.
        settings: Application settings.
    """
    max_age = settings.refresh_token_expire_days * 86400
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        max_age=max_age,
        path='/api/v1/auth',
    )


def clear_refresh_cookie(response: JSONResponse, settings: Settings) -> None:
    """Remove refresh token cookie from the response.

    Args:
        response: FastAPI response object.
        settings: Application settings.
    """
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path='/api/v1/auth',
    )
