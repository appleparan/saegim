"""User schemas."""

import datetime
import uuid
from enum import StrEnum

from pydantic import BaseModel


class UserRole(StrEnum):
    """User role enum."""

    ADMIN = 'admin'
    ANNOTATOR = 'annotator'
    REVIEWER = 'reviewer'


class UserUpdate(BaseModel):
    """Schema for admin user update (role change and activation toggle)."""

    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: uuid.UUID
    name: str
    login_id: str
    email: str
    role: UserRole
    must_change_password: bool = False
    is_active: bool = True
    created_at: datetime.datetime
