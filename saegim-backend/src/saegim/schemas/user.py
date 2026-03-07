"""User schemas."""

import datetime
import uuid
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class UserRole(StrEnum):
    """User role enum."""

    ADMIN = 'admin'
    ANNOTATOR = 'annotator'
    REVIEWER = 'reviewer'


class UserCreate(BaseModel):
    """Schema for creating a user."""

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    role: UserRole = Field(default=UserRole.ANNOTATOR)


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
