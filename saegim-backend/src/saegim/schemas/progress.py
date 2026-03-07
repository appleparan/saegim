"""Project progress board schemas."""

import uuid

from pydantic import BaseModel


class StatusBreakdown(BaseModel):
    """Count of pages per status."""

    pending: int
    in_progress: int
    submitted: int
    reviewed: int


class DocumentProgress(BaseModel):
    """Per-document progress within a project."""

    document_id: uuid.UUID
    filename: str
    total_pages: int
    status_counts: StatusBreakdown
    completion_rate: float


class MemberActivity(BaseModel):
    """Per-member activity within a project."""

    user_id: uuid.UUID
    user_name: str
    role: str
    assigned_pages: int
    in_progress_pages: int
    submitted_pages: int
    reviewed_pages: int


class ProjectProgressResponse(BaseModel):
    """Full project progress board response."""

    total_pages: int
    completion_rate: float
    status_breakdown: StatusBreakdown
    documents: list[DocumentProgress]
    members: list[MemberActivity]
