"""Document management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from saegim.api.settings import Settings, get_settings
from saegim.core.database import get_pool
from saegim.repositories import document_repo, page_repo, project_repo
from saegim.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from saegim.schemas.page import PageListResponse

router = APIRouter()


@router.get(
    '/projects/{project_id}/documents',
    response_model=list[DocumentListResponse],
)
async def list_project_documents(project_id: uuid.UUID) -> list[DocumentListResponse]:
    """List all documents for a project.

    Args:
        project_id: Parent project UUID.

    Returns:
        list[DocumentListResponse]: Documents in the project.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    project = await project_repo.get_by_id(pool, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    records = await document_repo.list_by_project(pool, project_id)
    return [DocumentListResponse(**dict(r)) for r in records]


@router.post(
    '/projects/{project_id}/documents',
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> DocumentUploadResponse:
    """Upload a PDF document and convert to page images.

    Args:
        project_id: Parent project UUID.
        file: Uploaded PDF file.
        settings: Application settings.

    Returns:
        DocumentUploadResponse: Upload result with document info.

    Raises:
        HTTPException: If project not found or file is not PDF.
    """
    pool = get_pool()

    project = await project_repo.get_by_id(pool, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Only PDF files are accepted',
        )

    from saegim.services import document_service

    content = await file.read()
    result = await document_service.upload_and_convert(
        pool,
        project_id=project_id,
        filename=file.filename,
        file_content=content,
        storage_path=settings.storage_path,
    )

    return DocumentUploadResponse(
        id=result['id'],
        filename=result['filename'],
        total_pages=result['total_pages'],
        status=result['status'],
    )


@router.delete('/documents/{document_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: uuid.UUID) -> None:
    """Delete a document and its storage files.

    Args:
        document_id: Document UUID.

    Raises:
        HTTPException: If document not found.
    """
    from saegim.services import document_service

    pool = get_pool()
    deleted = await document_service.delete_with_files(pool, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Document not found')


@router.get('/documents/{document_id}', response_model=DocumentResponse)
async def get_document(document_id: uuid.UUID) -> DocumentResponse:
    """Get a document by ID.

    Args:
        document_id: Document UUID.

    Returns:
        DocumentResponse: Document data.

    Raises:
        HTTPException: If document not found.
    """
    pool = get_pool()
    record = await document_repo.get_by_id(pool, document_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Document not found')
    return DocumentResponse(**dict(record))


@router.get('/documents/{document_id}/status', response_model=DocumentStatusResponse)
async def get_document_status(document_id: uuid.UUID) -> DocumentStatusResponse:
    """Get document processing/extraction progress.

    Args:
        document_id: Document UUID.

    Returns:
        DocumentStatusResponse: Document status with processed page count.

    Raises:
        HTTPException: If document not found.
    """
    pool = get_pool()
    record = await document_repo.get_by_id(pool, document_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Document not found')

    total_pages = int(record['total_pages'] or 0)
    status_value = record['status']
    processed_pages = await page_repo.count_processed_by_document(pool, document_id)

    # For terminal states, expose full progress for stable UI behavior.
    if status_value in {'ready', 'error', 'extraction_failed'} and total_pages > 0:
        processed_pages = total_pages

    return DocumentStatusResponse(
        id=record['id'],
        status=status_value,
        total_pages=total_pages,
        processed_pages=min(processed_pages, total_pages) if total_pages > 0 else processed_pages,
    )


@router.get(
    '/documents/{document_id}/pages',
    response_model=list[PageListResponse],
)
async def list_document_pages(document_id: uuid.UUID) -> list[PageListResponse]:
    """List all pages for a document.

    Args:
        document_id: Document UUID.

    Returns:
        list[PageListResponse]: Pages in the document.

    Raises:
        HTTPException: If document not found.
    """
    pool = get_pool()
    doc = await document_repo.get_by_id(pool, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Document not found')

    pages = await page_repo.list_by_document(pool, document_id)
    return [PageListResponse(**dict(r)) for r in pages]
