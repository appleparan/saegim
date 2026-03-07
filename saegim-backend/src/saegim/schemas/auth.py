"""Authentication request and response schemas."""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    name: str = Field(min_length=1, max_length=255)
    login_id: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Schema for user login."""

    login_id: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = 'bearer'  # noqa: S105
    must_change_password: bool = False
