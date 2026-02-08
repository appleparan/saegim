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


class UserResponse(BaseModel):
    """Schema for user response."""

    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    created_at: datetime.datetime
