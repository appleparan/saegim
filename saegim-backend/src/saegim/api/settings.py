"""Application settings using Pydantic Settings."""

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # API Settings
    api_host: str = Field(default='0.0.0.0', description='API host')  # noqa: S104
    api_port: int = Field(default=5000, description='API port')
    debug: bool = Field(default=False, description='Debug mode')
    log_level: str = Field(default='INFO', description='Log level')

    # CORS Settings
    cors_origins: list[str] = Field(
        default=['http://localhost:3000', 'http://localhost:5173'],
        description='Allowed CORS origins',
    )

    # Database Settings
    database_url: str = Field(
        default='postgresql://labeling:labeling@localhost:5432/labeling',
        description='PostgreSQL connection URL',
    )
    db_pool_min_size: int = Field(default=2, description='Minimum DB pool connections')
    db_pool_max_size: int = Field(default=10, description='Maximum DB pool connections')

    # Storage Settings
    storage_path: str = Field(default='./storage', description='File storage base path')

    # Server Settings
    max_workers: int = Field(default=1, description='Maximum number of workers')

    # JWT Settings
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description='Secret key for JWT signing',
    )
    jwt_algorithm: str = Field(default='HS256', description='JWT signing algorithm')
    access_token_expire_minutes: int = Field(
        default=15, description='Access token expiry in minutes'
    )

    # Refresh Token Settings
    refresh_token_expire_days: int = Field(default=7, description='Refresh token expiry in days')
    refresh_cookie_name: str = Field(
        default='saegim_refresh_token', description='Refresh token cookie name'
    )
    refresh_cookie_secure: bool = Field(
        default=True, description='Set Secure flag on refresh cookie (disable for HTTP dev)'
    )
    refresh_cookie_samesite: Literal['lax', 'strict', 'none'] = Field(
        default='lax', description='SameSite attribute for refresh cookie'
    )
    refresh_grace_period_seconds: int = Field(
        default=30, description='Grace period for revoked refresh tokens (multi-tab support)'
    )

    # OCR API Keys (optional, pre-filled in UI when available)
    gemini_api_key: str = Field(default='', description='Gemini API key from environment')


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
