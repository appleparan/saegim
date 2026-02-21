"""Page schemas."""

import datetime
import uuid
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, Field, model_validator


class PageStatus(StrEnum):
    """Page labeling status."""

    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    SUBMITTED = 'submitted'
    REVIEWED = 'reviewed'


class PageResponse(BaseModel):
    """Schema for page response with annotation data."""

    id: uuid.UUID
    document_id: uuid.UUID
    page_no: int
    width: int
    height: int
    image_path: str
    image_url: str = ''
    pdf_path: str | None = None
    pdf_url: str = ''
    annotation_data: dict[str, Any]
    auto_extracted_data: dict[str, Any] | None = None
    status: PageStatus
    assigned_to: uuid.UUID | None = None
    updated_at: datetime.datetime
    project_id: uuid.UUID | None = None
    project_name: str | None = None
    document_filename: str | None = None

    @model_validator(mode='after')
    def compute_urls(self) -> 'PageResponse':
        """Compute image_url and pdf_url from their respective paths."""
        if self.image_path and not self.image_url:
            filename = PurePosixPath(self.image_path).name
            object.__setattr__(self, 'image_url', f'/storage/images/{filename}')
        if self.pdf_path and not self.pdf_url:
            pdf_filename = PurePosixPath(self.pdf_path).name
            object.__setattr__(self, 'pdf_url', f'/storage/pdfs/{pdf_filename}')
        return self


class PageListResponse(BaseModel):
    """Schema for page list item."""

    id: uuid.UUID
    page_no: int
    width: int
    height: int
    status: PageStatus
    assigned_to: uuid.UUID | None = None
    updated_at: datetime.datetime


class PageAnnotationUpdate(BaseModel):
    """Schema for updating annotation data."""

    annotation_data: dict[str, Any]


class PageAttributeUpdate(BaseModel):
    """Schema for updating page attributes."""

    page_attribute: dict[str, Any]


class ElementCreate(BaseModel):
    """Schema for creating a new layout element."""

    category_type: str = Field(min_length=1)
    poly: list[float] = Field(min_length=8, max_length=8)
    text: str = Field(default='')
    latex: str = Field(default='')
    html: str = Field(default='')
    attribute: dict[str, Any] = Field(default_factory=dict)
    ignore: bool = Field(default=False)
