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

LayoutProvider = Literal['ppstructure', 'pymupdf']
OcrProvider = Literal['gemini', 'olmocr', 'ppocr']


class PpstructureConfig(BaseModel):
    """PP-StructureV3 server configuration."""

    host: str = Field(default='localhost', description='PP-StructureV3 server host')
    port: int = Field(
        default=18811,
        ge=1,
        le=65535,
        description='PP-StructureV3 server port',
    )


class GeminiConfig(BaseModel):
    """Gemini API configuration."""

    api_key: str = Field(min_length=1, description='Google Gemini API key')
    model: str = Field(default='gemini-2.0-flash', description='Gemini model name')


class VllmConfig(BaseModel):
    """vLLM server configuration (for OlmOCR)."""

    host: str = Field(default='localhost', description='vLLM server host')
    port: int = Field(default=8000, ge=1, le=65535, description='vLLM server port')
    model: str = Field(
        default='allenai/olmOCR-2-7B-1025',
        description='vLLM model name',
    )


class OcrConfigUpdate(BaseModel):
    """Schema for updating project OCR configuration.

    Two-stage pipeline: layout_provider (detection) + ocr_provider (text).
    - pymupdf layout: no extra config needed (fallback).
    - ppstructure layout: requires ppstructure config + ocr_provider.
    """

    layout_provider: LayoutProvider
    ocr_provider: OcrProvider | None = None
    ppstructure: PpstructureConfig | None = None
    gemini: GeminiConfig | None = None
    vllm: VllmConfig | None = None


class OcrConfigResponse(BaseModel):
    """Schema for OCR configuration response."""

    layout_provider: LayoutProvider
    ocr_provider: OcrProvider | None = None
    ppstructure: PpstructureConfig | None = None
    gemini: GeminiConfig | None = None
    vllm: VllmConfig | None = None


class OcrConnectionTestResponse(BaseModel):
    """Schema for OCR connection test result."""

    success: bool
    message: str
