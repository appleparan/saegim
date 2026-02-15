"""Project management endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from saegim.core.database import get_pool
from saegim.repositories import document_repo, project_repo
from saegim.schemas.project import ProjectCreate, ProjectResponse

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
