"""Project schemas."""

import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, Field


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

EngineType = Literal['commercial_api', 'integrated_server', 'split_pipeline', 'pymupdf']
CommercialApiProvider = Literal['gemini', 'vllm']
SplitPipelineOcrProvider = Literal['gemini', 'vllm']


class CommercialApiConfig(BaseModel):
    """Commercial VLM API configuration (Type 1)."""

    provider: CommercialApiProvider = Field(description='VLM provider type')
    api_key: str = Field(default='', description='API key (for Gemini)')
    host: str = Field(default='localhost', description='Server host (for vLLM)')
    port: int = Field(default=8000, ge=1, le=65535, description='Server port (for vLLM)')
    model: str = Field(default='gemini-2.0-flash', description='Model name')


class IntegratedServerConfig(BaseModel):
    """Integrated pipeline server configuration (Type 2)."""

    url: str = Field(
        default='http://localhost:18811',
        description='Server URL (e.g., http://localhost:18811)',
    )


class SplitPipelineConfig(BaseModel):
    """Split pipeline configuration (Type 3)."""

    layout_server_url: str = Field(
        default='http://localhost:18811',
        description='Layout detection server URL',
    )
    ocr_provider: SplitPipelineOcrProvider = Field(description='OCR text provider')
    ocr_api_key: str = Field(default='', description='OCR API key (for Gemini)')
    ocr_host: str = Field(default='localhost', description='OCR server host (for vLLM)')
    ocr_port: int = Field(
        default=8000, ge=1, le=65535, description='OCR server port (for vLLM)'
    )
    ocr_model: str = Field(default='gemini-2.0-flash', description='OCR model name')


class OcrConfigUpdate(BaseModel):
    """Schema for updating project OCR configuration.

    Single engine_type selector with type-specific sub-config.
    """

    engine_type: EngineType
    commercial_api: CommercialApiConfig | None = None
    integrated_server: IntegratedServerConfig | None = None
    split_pipeline: SplitPipelineConfig | None = None


class OcrConfigResponse(BaseModel):
    """Schema for OCR configuration response."""

    engine_type: EngineType
    commercial_api: CommercialApiConfig | None = None
    integrated_server: IntegratedServerConfig | None = None
    split_pipeline: SplitPipelineConfig | None = None


class OcrConnectionTestResponse(BaseModel):
    """Schema for OCR connection test result."""

    success: bool
    message: str
