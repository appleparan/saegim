"""Project schemas."""

import datetime
import re
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ProjectCreate(BaseModel):
    """Schema for creating a project."""

    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default='')


class ProjectResponse(BaseModel):
    """Schema for project response."""

    id: uuid.UUID
    name: str
    description: str
    created_at: datetime.datetime


# --- OCR Config schemas ---

EngineType = Literal['commercial_api', 'vllm', 'split_pipeline', 'pdfminer']
CommercialApiProvider = Literal['gemini', 'vllm']
GeminiModel = Literal[
    'gemini-3-flash-preview',
    'gemini-3.1-pro-preview',
]
SplitPipelineOcrProvider = Literal['gemini', 'vllm']


class CommercialApiConfig(BaseModel):
    """Commercial VLM API configuration."""

    provider: CommercialApiProvider = Field(description='VLM provider type')
    api_key: str = Field(default='', description='API key')
    model: str = Field(default='gemini-3-flash-preview', description='Model name')
    prompt: str = Field(
        default='',
        description='Custom OCR prompt. Empty = default structured prompt.',
    )


class VllmServerConfig(BaseModel):
    """vLLM server configuration."""

    host: str = Field(default='localhost', description='Server host')
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description='Server port',
    )
    model: str = Field(
        default='datalab-to/chandra',
        description='Model running on the server',
    )


class SplitPipelineConfig(BaseModel):
    """Split pipeline configuration (Docling layout + text OCR)."""

    docling_model_name: str = Field(
        default='ibm-granite/granite-docling-258M',
        description='Docling model for layout detection',
    )
    ocr_provider: SplitPipelineOcrProvider = Field(description='OCR text provider')
    ocr_api_key: str = Field(default='', description='OCR API key (for Gemini)')
    ocr_host: str = Field(default='localhost', description='OCR server host (for vLLM)')
    ocr_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description='OCR server port (for vLLM)',
    )
    ocr_model: str = Field(
        default='allenai/olmOCR-2-7B-1025-FP8',
        description='OCR model name',
    )


# --- Multi-instance engine registry schemas ---

# Valid engine types that can be registered as instances
RegisterableEngineType = Literal['commercial_api', 'vllm', 'split_pipeline']

# Mapping from engine_type to expected config class for validation
_ENGINE_CONFIG_CLASSES: dict[str, type[BaseModel]] = {
    'commercial_api': CommercialApiConfig,
    'vllm': VllmServerConfig,
    'split_pipeline': SplitPipelineConfig,
}


def slugify(name: str) -> str:
    """Convert a display name to a URL-safe slug.

    Args:
        name: Display name to slugify.

    Returns:
        Lowercase slug with only alphanumeric chars and hyphens.
    """
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    return slug or 'engine'


def generate_engine_id(name: str, existing_ids: set[str]) -> str:
    """Generate a unique engine_id from a display name.

    Args:
        name: Display name.
        existing_ids: Set of existing engine IDs to avoid collision.

    Returns:
        Unique slug-based engine ID.
    """
    base = slugify(name)
    if base not in existing_ids:
        return base
    counter = 2
    while f'{base}-{counter}' in existing_ids:
        counter += 1
    return f'{base}-{counter}'


class EngineInstance(BaseModel):
    """A registered OCR engine instance."""

    engine_type: RegisterableEngineType
    name: str = Field(min_length=1, max_length=100, description='Display name')
    config: dict[str, Any] = Field(description='Engine-type-specific configuration')

    @model_validator(mode='after')
    def validate_config_matches_type(self) -> 'EngineInstance':
        """Ensure config dict validates against the engine_type's config class."""
        config_cls = _ENGINE_CONFIG_CLASSES.get(self.engine_type)
        if config_cls is not None:
            config_cls.model_validate(self.config)
        return self


class EngineInstanceCreate(BaseModel):
    """Request to register a new engine instance."""

    engine_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        pattern=r'^[a-z0-9][a-z0-9-]*$',
        description='Optional custom ID (auto-generated from name if omitted)',
    )
    engine_type: RegisterableEngineType
    name: str = Field(min_length=1, max_length=100, description='Display name')
    config: dict[str, Any] = Field(description='Engine-type-specific configuration')

    @model_validator(mode='after')
    def validate_config_matches_type(self) -> 'EngineInstanceCreate':
        """Ensure config dict validates against the engine_type's config class."""
        config_cls = _ENGINE_CONFIG_CLASSES.get(self.engine_type)
        if config_cls is not None:
            config_cls.model_validate(self.config)
        return self


class EngineInstanceUpdate(BaseModel):
    """Request to update an engine instance."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    config: dict[str, Any] | None = None


class OcrConfigResponse(BaseModel):
    """Full OCR configuration response (multi-instance format)."""

    default_engine_id: str | None = None
    engines: dict[str, EngineInstance] = Field(default_factory=dict)
    env_gemini_api_key: str = Field(
        default='',
        description='Gemini API key from server environment (for UI pre-fill)',
    )


class DefaultEngineUpdate(BaseModel):
    """Request to set the default engine."""

    engine_id: str | None = Field(
        default=None,
        description='Engine ID to set as default. None = pdfminer fallback.',
    )


class OcrConnectionTestRequest(BaseModel):
    """Request to test a specific engine's connection."""

    engine_id: str = Field(description='Engine instance ID to test')


class AvailableEngine(BaseModel):
    """An engine available for per-element OCR."""

    engine_id: str
    engine_type: RegisterableEngineType
    name: str


class AvailableEnginesResponse(BaseModel):
    """List of engines available for per-element text extraction."""

    engines: list[AvailableEngine]


class OcrConnectionTestResponse(BaseModel):
    """Schema for OCR connection test result."""

    success: bool
    message: str
