"""Page labeling endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from saegim.core.database import get_pool
from saegim.schemas.page import (
    ElementCreate,
    PageAnnotationUpdate,
    PageAttributeUpdate,
    PageResponse,
)
from saegim.services import labeling_service

router = APIRouter()


@router.get('/pages/{page_id}', response_model=PageResponse)
async def get_page(page_id: uuid.UUID) -> PageResponse:
    """Get a page with annotation data for labeling.

    Args:
        page_id: Page UUID.

    Returns:
        PageResponse: Page data with annotations.

    Raises:
        HTTPException: If page not found.
    """
    pool = get_pool()
    result = await labeling_service.get_page_data(pool, page_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')
    return PageResponse(**result)


@router.put('/pages/{page_id}', response_model=PageResponse)
async def update_annotation(page_id: uuid.UUID, body: PageAnnotationUpdate) -> PageResponse:
    """Save annotation data for a page.

    Args:
        page_id: Page UUID.
        body: Annotation data to save.

    Returns:
        PageResponse: Updated page data.

    Raises:
        HTTPException: If page not found.
    """
    pool = get_pool()
    result = await labeling_service.save_annotation(pool, page_id, body.annotation_data)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')
    return PageResponse(**result)


@router.put('/pages/{page_id}/attributes', response_model=PageResponse)
async def update_page_attributes(page_id: uuid.UUID, body: PageAttributeUpdate) -> PageResponse:
    """Save page-level attributes.

    Args:
        page_id: Page UUID.
        body: Page attribute data.

    Returns:
        PageResponse: Updated page data.

    Raises:
        HTTPException: If page not found.
    """
    pool = get_pool()
    result = await labeling_service.save_page_attribute(pool, page_id, body.page_attribute)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')
    return PageResponse(**result)


@router.post(
    '/pages/{page_id}/elements',
    response_model=PageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_element(page_id: uuid.UUID, body: ElementCreate) -> PageResponse:
    """Add a new layout element to the page.

    Args:
        page_id: Page UUID.
        body: Element creation data.

    Returns:
        PageResponse: Updated page data with new element.

    Raises:
        HTTPException: If page not found.
    """
    pool = get_pool()
    element = body.model_dump()
    result = await labeling_service.add_element(pool, page_id, element)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')
    return PageResponse(**result)


@router.delete('/pages/{page_id}/elements/{anno_id}', response_model=PageResponse)
async def delete_element(page_id: uuid.UUID, anno_id: int) -> PageResponse:
    """Delete a layout element by annotation ID.

    Args:
        page_id: Page UUID.
        anno_id: Annotation ID of the element to delete.

    Returns:
        PageResponse: Updated page data.

    Raises:
        HTTPException: If page not found.
    """
    pool = get_pool()
    result = await labeling_service.delete_element(pool, page_id, anno_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')
    return PageResponse(**result)
