"""Page labeling endpoints."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from saegim.api.deps import get_current_user
from saegim.core.database import get_pool
from saegim.repositories import task_repo
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
from saegim.schemas.task import AssignRequest, ReviewRequest
from saegim.schemas.user import UserResponse
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


@router.post('/pages/{page_id}/force-accept-extraction', response_model=PageResponse)
async def force_accept_extraction(page_id: uuid.UUID) -> PageResponse:
    """Force-accept auto-extracted data, overwriting existing annotations.

    Unlike accept-extraction, this replaces annotation_data even when
    the page already has annotations.

    Args:
        page_id: Page UUID.

    Returns:
        PageResponse: Updated page data with accepted annotations.

    Raises:
        HTTPException: If page not found or no auto-extracted data.
    """
    pool = get_pool()
    result = await labeling_service.force_accept_auto_extraction(pool, page_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Cannot accept: no auto-extracted data available',
        )
    return PageResponse(**result)


@router.post('/pages/{page_id}/extract-text', response_model=ExtractTextResponse)
async def extract_text(page_id: uuid.UUID, body: ExtractTextRequest) -> ExtractTextResponse:
    """Extract text from a drawn region using OCR.

    Crops the specified polygon region from the page image and sends it
    to the project's configured text OCR provider for recognition.
    Optionally overrides the engine via body.engine_id.

    Args:
        page_id: Page UUID.
        body: Region polygon, category type, and optional engine ID override.

    Returns:
        ExtractTextResponse: Extracted text.

    Raises:
        HTTPException: 404 if page not found, 503 if no OCR provider,
            502 if OCR fails.
    """
    pool = get_pool()

    try:
        image_path, text_provider = await resolve_text_provider(
            pool, page_id, engine_id=body.engine_id
        )
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


# --- Task workflow endpoints ---


async def _check_page_project_role(
    pool: object,
    page_id: uuid.UUID,
    user: UserResponse,
    allowed_roles: frozenset[str],
) -> None:
    """Check that the user has an allowed project role for the page.

    Admin users bypass the check. Raises HTTPException on failure.

    Args:
        pool: Database connection pool.
        page_id: Page UUID.
        user: Current authenticated user.
        allowed_roles: Set of allowed project_members roles.

    Raises:
        HTTPException: 404 if page/project not found, 403 if insufficient permissions.
    """
    if user.role == 'admin':
        return

    project_id = await task_repo.get_project_id_for_page(pool, page_id)
    if project_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')

    member_role = await task_repo.get_project_member_role(pool, project_id, user.id)
    if member_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Insufficient permissions',
        )


@router.post('/pages/{page_id}/assign', response_model=PageResponse)
async def assign_page(
    page_id: uuid.UUID,
    body: AssignRequest,
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> PageResponse:
    """Assign a page to a user. Only project owner or admin can assign.

    Args:
        page_id: Page UUID.
        body: Assignment request with target user_id.
        current_user: Authenticated user.

    Returns:
        PageResponse: Updated page data.

    Raises:
        HTTPException: 403 if not owner/admin, 404 if not found, 409 if invalid state.
    """
    pool = get_pool()
    await _check_page_project_role(pool, page_id, current_user, frozenset({'owner'}))

    result = await task_repo.assign_page(pool, page_id, body.user_id, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Page not found or cannot be assigned in current state',
        )
    return PageResponse(**dict(result))


@router.post('/pages/{page_id}/submit', response_model=PageResponse)
async def submit_page(
    page_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> PageResponse:
    """Submit a page for review. Only the assigned user can submit.

    Args:
        page_id: Page UUID.
        current_user: Authenticated user.

    Returns:
        PageResponse: Updated page data.

    Raises:
        HTTPException: 409 if not assigned to user or invalid state.
    """
    pool = get_pool()
    result = await task_repo.submit_page(pool, page_id, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Page not found, not assigned to you, or not in progress',
        )
    return PageResponse(**dict(result))


@router.post('/pages/{page_id}/review', response_model=PageResponse)
async def review_page(
    page_id: uuid.UUID,
    body: ReviewRequest,
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> PageResponse:
    """Review a submitted page (approve or reject). Only reviewer or admin can review.

    Args:
        page_id: Page UUID.
        body: Review request with action and optional comment.
        current_user: Authenticated user.

    Returns:
        PageResponse: Updated page data.

    Raises:
        HTTPException: 403 if not reviewer/admin, 409 if invalid state.
    """
    pool = get_pool()
    await _check_page_project_role(pool, page_id, current_user, frozenset({'reviewer', 'owner'}))

    result = await task_repo.review_page(pool, page_id, current_user.id, body.action, body.comment)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Page not found or not in submitted state',
        )
    return PageResponse(**dict(result))
