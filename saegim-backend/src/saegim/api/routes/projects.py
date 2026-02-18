"""Project management endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from saegim.core.database import get_pool
from saegim.repositories import document_repo, project_repo
from saegim.schemas.project import (
    OcrConfigResponse,
    OcrConfigUpdate,
    OcrConnectionTestResponse,
    ProjectCreate,
    ProjectResponse,
)

router = APIRouter()


@router.post('/projects', response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate) -> ProjectResponse:
    """Create a new project.

    Args:
        body: Project creation data.

    Returns:
        ProjectResponse: Created project.
    """
    pool = get_pool()
    record = await project_repo.create(pool, name=body.name, description=body.description)
    return ProjectResponse(**dict(record))


@router.get('/projects', response_model=list[ProjectResponse])
async def list_projects() -> list[ProjectResponse]:
    """List all projects.

    Returns:
        list[ProjectResponse]: All projects.
    """
    pool = get_pool()
    records = await project_repo.list_all(pool)
    return [ProjectResponse(**dict(r)) for r in records]


@router.get('/projects/{project_id}', response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID) -> ProjectResponse:
    """Get a project by ID.

    Args:
        project_id: Project UUID.

    Returns:
        ProjectResponse: Project data.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    record = await project_repo.get_by_id(pool, project_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return ProjectResponse(**dict(record))


@router.delete('/projects/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID) -> None:
    """Delete a project and all associated data.

    Deletes storage files (PDFs, images) then cascades DB delete
    to documents, pages, and task history.

    Args:
        project_id: Project UUID.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    project = await project_repo.get_by_id(pool, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

    # Delete storage files for each document first
    from saegim.services import document_service

    docs = await document_repo.list_by_project(pool, project_id)
    for doc in docs:
        await document_service.delete_with_files(pool, doc['id'])

    # Delete project (cascades remaining DB records)
    await project_repo.delete(pool, project_id)


@router.get('/projects/{project_id}/ocr-config', response_model=OcrConfigResponse)
async def get_ocr_config(project_id: uuid.UUID) -> OcrConfigResponse:
    """Get a project's OCR configuration.

    Args:
        project_id: Project UUID.

    Returns:
        OcrConfigResponse: Current OCR config.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    config = await project_repo.get_ocr_config(pool, project_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if not config:
        # No OCR config set yet — return default (pymupdf)
        return OcrConfigResponse(provider='pymupdf')
    return OcrConfigResponse(**config)


@router.put('/projects/{project_id}/ocr-config', response_model=OcrConfigResponse)
async def update_ocr_config(
    project_id: uuid.UUID,
    body: OcrConfigUpdate,
) -> OcrConfigResponse:
    """Update a project's OCR configuration.

    Args:
        project_id: Project UUID.
        body: New OCR configuration.

    Returns:
        OcrConfigResponse: Updated OCR config.

    Raises:
        HTTPException: If project not found or validation fails.
    """
    # Validate provider-specific config is provided
    if body.provider == 'gemini' and body.gemini is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='gemini config is required when provider is gemini',
        )
    if body.provider == 'vllm' and body.vllm is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='vllm config is required when provider is vllm',
        )

    pool = get_pool()
    project = await project_repo.get_by_id(pool, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

    config_dict = body.model_dump(exclude_none=True)
    updated = await project_repo.update_ocr_config(pool, project_id, config_dict)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update OCR config',
        )
    return OcrConfigResponse(**config_dict)


@router.post(
    '/projects/{project_id}/ocr-config/test',
    response_model=OcrConnectionTestResponse,
)
async def test_ocr_config(
    project_id: uuid.UUID,
    body: OcrConfigUpdate,
) -> OcrConnectionTestResponse:
    """Test OCR provider connection with the given configuration.

    Args:
        project_id: Project UUID (validates project exists).
        body: OCR configuration to test.

    Returns:
        OcrConnectionTestResponse: Test result.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    project = await project_repo.get_by_id(pool, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project not found',
        )

    from saegim.services.ocr_connection_test import check_ocr_connection

    config_dict = body.model_dump(exclude_none=True)
    success, message = check_ocr_connection(config_dict)
    return OcrConnectionTestResponse(success=success, message=message)
