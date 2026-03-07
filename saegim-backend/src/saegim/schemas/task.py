"""Task workflow request and response schemas."""

import datetime
import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

from saegim.schemas.page import PageStatus


class ReviewAction(StrEnum):
    """Review decision action."""

    APPROVED = 'approved'
    REJECTED = 'rejected'


class AssignRequest(BaseModel):
    """Schema for assigning a page to a user."""

    user_id: uuid.UUID


class ReviewRequest(BaseModel):
    """Schema for reviewing a submitted page."""

    action: ReviewAction
    comment: str | None = Field(default=None, max_length=2000)


class TaskResponse(BaseModel):
    """Schema for a user's assigned task item."""

    page_id: uuid.UUID
    page_no: int
    document_id: uuid.UUID
    document_filename: str
    project_id: uuid.UUID
    project_name: str
    status: PageStatus
    assigned_at: datetime.datetime


class ReviewQueueItem(BaseModel):
    """Schema for a page in the review queue."""

    page_id: uuid.UUID
    page_no: int
    document_id: uuid.UUID
    document_filename: str
    assigned_to: uuid.UUID | None = None
    assigned_to_name: str | None = None
    submitted_at: datetime.datetime


class TaskHistoryEntry(BaseModel):
    """Schema for a single task history record."""

    id: uuid.UUID
    page_id: uuid.UUID
    user_id: uuid.UUID
    action: str
    snapshot: dict | None = None
    created_at: datetime.datetime
