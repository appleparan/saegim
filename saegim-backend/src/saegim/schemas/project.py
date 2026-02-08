"""Project schemas."""

import datetime
import uuid

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
