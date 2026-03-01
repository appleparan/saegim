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

EngineType = Literal['commercial_api', 'vllm', 'split_pipeline', 'pdfminer']
CommercialApiProvider = Literal['gemini', 'vllm']
GeminiModel = Literal[
    'gemini-3.1-pro-preview',
    'gemini-3-pro-preview',
    'gemini-3-flash-preview',
]
SplitPipelineOcrProvider = Literal['gemini', 'vllm']


class CommercialApiConfig(BaseModel):
    """Commercial VLM API configuration."""

    provider: CommercialApiProvider = Field(description='VLM provider type')
    api_key: str = Field(default='', description='API key')
    model: str = Field(default='gemini-3-flash-preview', description='Model name')


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


class OcrConfigUpdate(BaseModel):
    """Schema for updating project OCR configuration.

    Single engine_type selector with type-specific sub-config.
    """

    engine_type: EngineType
    commercial_api: CommercialApiConfig | None = None
    vllm: VllmServerConfig | None = None
    split_pipeline: SplitPipelineConfig | None = None


class OcrConfigResponse(BaseModel):
    """Schema for OCR configuration response."""

    engine_type: EngineType
    commercial_api: CommercialApiConfig | None = None
    vllm: VllmServerConfig | None = None
    split_pipeline: SplitPipelineConfig | None = None
    env_gemini_api_key: str = Field(
        default='',
        description='Gemini API key from server environment (for UI pre-fill)',
    )


class OcrConnectionTestResponse(BaseModel):
    """Schema for OCR connection test result."""

    success: bool
    message: str
