"""Project management endpoints.

LEGACY: This module's OCR config endpoints still use the old flat format.
They will be rewritten in Stage 3 to use the multi-instance format.
The normalize_ocr_config in project_repo now auto-converts old→new on read,
so these legacy endpoints reconstruct old-format responses for backward compat.
"""

import uuid

from fastapi import APIRouter, HTTPException, status

from saegim.core.database import get_pool
from saegim.repositories import document_repo, project_repo
from saegim.schemas.project import (
    LegacyAvailableEngine,
    LegacyAvailableEnginesResponse,
    LegacyOcrConfigResponse,
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
    return ProjectResponse.model_validate(dict(record))


@router.get('/projects', response_model=list[ProjectResponse])
async def list_projects() -> list[ProjectResponse]:
    """List all projects.

    Returns:
        list[ProjectResponse]: All projects.
    """
    pool = get_pool()
    records = await project_repo.list_all(pool)
    return [ProjectResponse.model_validate(dict(r)) for r in records]


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
    return ProjectResponse.model_validate(dict(record))


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


@router.get('/projects/{project_id}/ocr-config', response_model=LegacyOcrConfigResponse)
async def get_ocr_config(project_id: uuid.UUID) -> LegacyOcrConfigResponse:
    """Get a project's OCR configuration (LEGACY format).

    Args:
        project_id: Project UUID.

    Returns:
        LegacyOcrConfigResponse: Current OCR config in legacy format.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    config = await project_repo.get_ocr_config(pool, project_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

    from saegim.api.settings import get_settings

    env_key = get_settings().gemini_api_key

    # Config is now in new multi-instance format from normalize_ocr_config.
    # Convert back to legacy flat format for backward compat.
    return _to_legacy_response(config, env_key)


def _to_legacy_response(config: dict, env_key: str) -> LegacyOcrConfigResponse:
    """Convert multi-instance config to legacy flat response.

    Args:
        config: Multi-instance format config.
        env_key: Gemini API key from environment.

    Returns:
        LegacyOcrConfigResponse in old flat format.
    """
    engines = config.get('engines', {})
    default_id = config.get('default_engine_id')

    if not engines and not default_id:
        return LegacyOcrConfigResponse(engine_type='pdfminer', env_gemini_api_key=env_key)

    # Reconstruct old-format fields from engine instances
    engine_type = 'pdfminer'
    commercial_api = None
    vllm = None
    split_pipeline = None
    enabled_engines = []

    for entry in engines.values():
        et = entry.get('engine_type', '')
        cfg = entry.get('config', {})
        if et == 'commercial_api':
            commercial_api = cfg
        elif et == 'vllm':
            vllm = cfg
        elif et == 'split_pipeline':
            split_pipeline = cfg
        enabled_engines.append(et)

    if default_id and default_id in engines:
        engine_type = engines[default_id].get('engine_type', 'pdfminer')

    return LegacyOcrConfigResponse(
        engine_type=engine_type,
        commercial_api=commercial_api,
        vllm=vllm,
        split_pipeline=split_pipeline,
        enabled_engines=enabled_engines,
        env_gemini_api_key=env_key,
    )


@router.put('/projects/{project_id}/ocr-config', response_model=LegacyOcrConfigResponse)
async def update_ocr_config(
    project_id: uuid.UUID,
    body: OcrConfigUpdate,
) -> LegacyOcrConfigResponse:
    """Update a project's OCR configuration (LEGACY format).

    Args:
        project_id: Project UUID.
        body: New OCR configuration in legacy format.

    Returns:
        LegacyOcrConfigResponse: Updated OCR config.

    Raises:
        HTTPException: If project not found or validation fails.
    """
    _validate_ocr_config(body)

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
    return LegacyOcrConfigResponse(**config_dict)


def _validate_ocr_config(body: OcrConfigUpdate) -> None:
    """Validate engine_type-based OCR configuration (LEGACY).

    Validates the primary engine has its sub-config, and each engine
    in enabled_engines also has its required sub-config.

    Args:
        body: OCR config to validate.

    Raises:
        HTTPException: If required sub-config is missing.
    """
    _validate_engine_has_config(body.engine_type, body)

    for engine in body.enabled_engines:
        if engine != 'pdfminer':
            _validate_engine_has_config(engine, body)


def _validate_engine_has_config(engine_type: str, body: OcrConfigUpdate) -> None:
    """Validate that a specific engine type has its required sub-config.

    Args:
        engine_type: Engine type to validate.
        body: OCR config containing sub-configs.

    Raises:
        HTTPException: If required sub-config is missing.
    """
    if engine_type == 'commercial_api' and body.commercial_api is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='commercial_api config is required when engine_type is commercial_api',
        )
    if engine_type == 'vllm' and body.vllm is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='vllm config is required when engine_type is vllm',
        )
    if engine_type == 'split_pipeline' and body.split_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='split_pipeline config is required when engine_type is split_pipeline',
        )


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

    from saegim.services.engines.factory import build_engine

    config_dict = body.model_dump(exclude_none=True)
    try:
        engine = build_engine(config_dict)
        success, message = engine.test_connection()
    except ValueError as exc:
        success, message = False, str(exc)
    return OcrConnectionTestResponse(success=success, message=message)


ENGINE_LABELS: dict[str, str] = {
    'pdfminer': 'pdfminer',
    'commercial_api': 'Gemini API',
    'vllm': 'vLLM',
    'split_pipeline': 'Docling + OCR',
}


@router.get(
    '/projects/{project_id}/available-engines',
    response_model=LegacyAvailableEnginesResponse,
)
async def get_available_engines(project_id: uuid.UUID) -> LegacyAvailableEnginesResponse:
    """Get list of engines available for per-element text extraction (LEGACY).

    Returns engines from the config that support region-level text extraction.

    Args:
        project_id: Project UUID.

    Returns:
        AvailableEnginesResponse: Available engines with labels.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    config = await project_repo.get_ocr_config(pool, project_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

    # Config is now in multi-instance format. Extract engines from it.
    engines_dict = config.get('engines', {})
    if not engines_dict:
        return LegacyAvailableEnginesResponse(engines=[])

    engines: list[LegacyAvailableEngine] = []
    for engine_type_entry in engines_dict.values():
        et = engine_type_entry.get('engine_type', '')
        if et == 'pdfminer':
            continue
        engines.append(
            LegacyAvailableEngine(
                engine_type=et,
                label=ENGINE_LABELS.get(et, et),
            )
        )

    return LegacyAvailableEnginesResponse(engines=engines)
