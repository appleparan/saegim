"""Export endpoints for OmniDocBench JSON generation."""

import uuid

from fastapi import APIRouter, HTTPException, status

from saegim.core.database import get_pool
from saegim.schemas.export import ExportResponse
from saegim.services import export_service

router = APIRouter()


@router.post('/projects/{project_id}/export', response_model=ExportResponse)
async def export_project(project_id: uuid.UUID) -> ExportResponse:
    """Export a project as OmniDocBench JSON.

    Args:
        project_id: Project UUID.

    Returns:
        ExportResponse: Export data with all page annotations.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    result = await export_service.export_project(pool, project_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return ExportResponse(**result)
