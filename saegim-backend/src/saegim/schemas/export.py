"""Export schemas."""

from typing import Any

from pydantic import BaseModel


class ExportResponse(BaseModel):
    """Schema for export response."""

    project_name: str
    total_pages: int
    data: list[dict[str, Any]]
