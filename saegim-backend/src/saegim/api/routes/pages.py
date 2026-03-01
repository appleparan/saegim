"""Page labeling endpoints."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException, status

from saegim.core.database import get_pool
from saegim.schemas.page import (
    ElementCreate,
    ExtractTextRequest,
    ExtractTextResponse,
    PageAnnotationUpdate,
    PageAttributeUpdate,
    PageResponse,
    ReadingOrderUpdate,
    RelationCreate,
    RelationDelete,
)
from saegim.services import labeling_service
from saegim.services.text_extraction_service import (
    NoTextProviderError,
    TextExtractionError,
    extract_text_from_region,
    resolve_text_provider,
)

logger = logging.getLogger(__name__)

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


@router.post('/pages/{page_id}/accept-extraction', response_model=PageResponse)
async def accept_extraction(page_id: uuid.UUID) -> PageResponse:
    """Accept auto-extracted data as the initial annotation.

    Copies auto_extracted_data to annotation_data. Only works when
    the page has auto_extracted_data and annotation_data is empty.

    Args:
        page_id: Page UUID.

    Returns:
        PageResponse: Updated page data with accepted annotations.

    Raises:
        HTTPException: If page not found or preconditions not met.
    """
    pool = get_pool()
    result = await labeling_service.accept_auto_extraction(pool, page_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Cannot accept: no auto-extracted data or annotation already exists',
        )
    return PageResponse(**result)


@router.post('/pages/{page_id}/extract-text', response_model=ExtractTextResponse)
async def extract_text(page_id: uuid.UUID, body: ExtractTextRequest) -> ExtractTextResponse:
    """Extract text from a drawn region using OCR.

    Crops the specified polygon region from the page image and sends it
    to the project's configured text OCR provider for recognition.

    Args:
        page_id: Page UUID.
        body: Region polygon and category type.

    Returns:
        ExtractTextResponse: Extracted text.

    Raises:
        HTTPException: 404 if page not found, 503 if no OCR provider,
            502 if OCR fails.
    """
    pool = get_pool()

    try:
        image_path, text_provider = await resolve_text_provider(pool, page_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Page not found',
        ) from exc
    except NoTextProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    try:
        text = await asyncio.to_thread(
            extract_text_from_region,
            image_path,
            body.poly,
            body.category_type,
            text_provider,
        )
    except TextExtractionError as exc:
        logger.warning('Text extraction failed for page %s: %s', page_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f'Text extraction failed: {exc}',
        ) from exc

    return ExtractTextResponse(text=text)


@router.post(
    '/pages/{page_id}/relations',
    response_model=PageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_relation(page_id: uuid.UUID, body: RelationCreate) -> PageResponse:
    """Add a relation between two elements on a page.

    Args:
        page_id: Page UUID.
        body: Relation creation data.

    Returns:
        PageResponse: Updated page data with new relation.

    Raises:
        HTTPException: If page not found or validation fails.
    """
    pool = get_pool()
    try:
        result = await labeling_service.add_relation(pool, page_id, body.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')
    return PageResponse(**result)


@router.delete('/pages/{page_id}/relations', response_model=PageResponse)
async def delete_relation(page_id: uuid.UUID, body: RelationDelete) -> PageResponse:
    """Delete a relation between two elements on a page.

    Args:
        page_id: Page UUID.
        body: Relation deletion data.

    Returns:
        PageResponse: Updated page data.

    Raises:
        HTTPException: If page not found.
    """
    pool = get_pool()
    result = await labeling_service.delete_relation(
        pool, page_id, body.source_anno_id, body.target_anno_id
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')
    return PageResponse(**result)


@router.put('/pages/{page_id}/reading-order', response_model=PageResponse)
async def update_reading_order(
    page_id: uuid.UUID,
    body: ReadingOrderUpdate,
) -> PageResponse:
    """Update reading order of layout elements.

    Args:
        page_id: Page UUID.
        body: Reading order update with anno_id-to-order mapping.

    Returns:
        PageResponse: Updated page data.

    Raises:
        HTTPException: If page not found or invalid annotation IDs.
    """
    pool = get_pool()
    result = await labeling_service.update_reading_order(pool, page_id, body.order_map)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Page not found or invalid annotation IDs',
        )
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
