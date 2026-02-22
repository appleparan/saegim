"""Document schemas."""

import datetime
import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentStatus(StrEnum):
    """Document processing status."""

    UPLOADING = 'uploading'
    PROCESSING = 'processing'
    EXTRACTING = 'extracting'
    READY = 'ready'
    ERROR = 'error'
    EXTRACTION_FAILED = 'extraction_failed'


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    pdf_path: str
    total_pages: int
    status: DocumentStatus
    created_at: datetime.datetime


class DocumentListResponse(BaseModel):
    """Schema for listing documents."""

    id: uuid.UUID
    filename: str
    total_pages: int
    status: DocumentStatus
    created_at: datetime.datetime


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    id: uuid.UUID
    filename: str
    total_pages: int
    status: DocumentStatus
    message: str = Field(default='Document uploaded successfully')


class DocumentStatusResponse(BaseModel):
    """Schema for document extraction/processing status."""

    id: uuid.UUID
    status: DocumentStatus
    total_pages: int
    processed_pages: int
