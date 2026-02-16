"""Application settings using Pydantic Settings."""

from functools import lru_cache

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

    # Extraction Settings
    extraction_backend: str = Field(
        default='mineru',
        description="PDF extraction backend: 'mineru' or 'pymupdf'",
    )
    mineru_api_url: str = Field(
        default='http://localhost:18000',
        description='MinerU extraction service URL (saegim-mineru)',
    )
    mineru_backend: str = Field(
        default='pipeline',
        description="MinerU parsing backend: 'pipeline', 'hybrid-auto-engine', 'vlm-auto-engine'",
    )
    mineru_language: str = Field(
        default='korean',
        description='MinerU OCR language setting',
    )

    # Celery Settings
    celery_broker_url: str = Field(
        default='redis://localhost:6379/0',
        description='Celery broker URL (Redis)',
    )
    celery_result_backend: str = Field(
        default='redis://localhost:6379/1',
        description='Celery result backend URL (Redis)',
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
