"""Admin dashboard schemas."""

import datetime
import uuid

from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    """System-wide statistics for admin dashboard."""

    total_users: int
    active_users: int
    total_projects: int
    total_pages: int
    completed_pages: int
    submitted_pages: int
    completion_rate: float


class AdminProjectResponse(BaseModel):
    """Enriched project response for admin dashboard."""

    id: uuid.UUID
    name: str
    description: str
    member_count: int
    total_pages: int
    completed_pages: int
    submitted_pages: int
    created_at: datetime.datetime
