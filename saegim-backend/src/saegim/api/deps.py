"""FastAPI dependency injection for authentication and authorization."""

import datetime
import logging
import uuid

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from saegim.api.settings import Settings, get_settings
from saegim.core.database import get_pool
from saegim.repositories import user_repo
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
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User UUID string.
        role: User role string.
        settings: Application settings.

    Returns:
        str: Encoded JWT token.
    """
    expire = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        'sub': user_id,
        'role': role,
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
