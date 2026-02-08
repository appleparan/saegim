"""Page schemas."""

import datetime
import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


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
    annotation_data: dict[str, Any]
    auto_extracted_data: dict[str, Any] | None = None
    status: PageStatus
    assigned_to: uuid.UUID | None = None
    updated_at: datetime.datetime


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
