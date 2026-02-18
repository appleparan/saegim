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

OcrProvider = Literal['gemini', 'vllm', 'mineru', 'pymupdf']


class GeminiConfig(BaseModel):
    """Gemini API configuration."""

    api_key: str = Field(min_length=1, description='Google Gemini API key')
    model: str = Field(default='gemini-2.0-flash', description='Gemini model name')


class VllmConfig(BaseModel):
    """vLLM server configuration."""

    host: str = Field(default='localhost', description='vLLM server host')
    port: int = Field(default=8000, ge=1, le=65535, description='vLLM server port')
    model: str = Field(
        default='Qwen/Qwen2.5-VL-72B-Instruct',
        description='vLLM model name',
    )


class OcrConfigUpdate(BaseModel):
    """Schema for updating project OCR configuration."""

    provider: OcrProvider
    gemini: GeminiConfig | None = None
    vllm: VllmConfig | None = None


class OcrConfigResponse(BaseModel):
    """Schema for OCR configuration response."""

    provider: OcrProvider
    gemini: GeminiConfig | None = None
    vllm: VllmConfig | None = None
