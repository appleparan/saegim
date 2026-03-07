"""Project member schemas."""

import datetime
import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


class ProjectMemberRole(StrEnum):
    """Project-level member role."""

    OWNER = 'owner'
    ANNOTATOR = 'annotator'
    REVIEWER = 'reviewer'


class ProjectMemberCreate(BaseModel):
    """Schema for adding a member to a project."""

    user_id: uuid.UUID
    role: ProjectMemberRole = Field(default=ProjectMemberRole.ANNOTATOR)


class ProjectMemberRoleUpdate(BaseModel):
    """Schema for updating a member's role."""

    role: ProjectMemberRole


class ProjectMemberResponse(BaseModel):
    """Schema for project member response."""

    user_id: uuid.UUID
    user_name: str
    user_email: str
    role: ProjectMemberRole
    joined_at: datetime.datetime
