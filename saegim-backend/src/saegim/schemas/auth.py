"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field, model_validator


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


class LoginIdCheckResponse(BaseModel):
    """Schema for login ID availability checks."""

    login_id: str
    available: bool


class CredentialUpdateRequest(BaseModel):
    """Schema for updating login credentials."""

    current_password: str = Field(min_length=1, max_length=128)
    login_id: str | None = Field(default=None, min_length=3, max_length=64)
    email: EmailStr | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @model_validator(mode='after')
    def validate_has_update_target(self) -> 'CredentialUpdateRequest':
        """Ensure at least one credential field is provided."""
        if self.login_id is None and self.email is None and self.new_password is None:
            msg = 'At least one of login_id, email, or new_password must be provided'
            raise ValueError(msg)
        return self
