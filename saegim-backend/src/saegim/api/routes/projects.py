"""Project management and OCR engine configuration endpoints."""

import uuid
from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, status

from saegim.core.database import get_pool
from saegim.repositories import document_repo, project_repo
from saegim.schemas.project import (
    AvailableEngine,
    AvailableEnginesResponse,
    DefaultEngineUpdate,
    EngineInstance,
    EngineInstanceCreate,
    EngineInstanceUpdate,
    OcrConfigResponse,
    OcrConnectionTestRequest,
    OcrConnectionTestResponse,
    ProjectCreate,
    ProjectResponse,
    generate_engine_id,
)

router = APIRouter()


# --- Project CRUD ---


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

    Args:
        project_id: Project UUID.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    project = await project_repo.get_by_id(pool, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

    from saegim.services import document_service

    docs = await document_repo.list_by_project(pool, project_id)
    for doc in docs:
        await document_service.delete_with_files(pool, doc['id'])

    await project_repo.delete(pool, project_id)


# --- OCR Config ---


async def _get_config_or_404(pool: asyncpg.Pool, project_id: uuid.UUID) -> dict[str, Any]:
    """Get OCR config, raising 404 if project not found.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        OCR config dict in multi-instance format.

    Raises:
        HTTPException: If project not found.
    """
    config = await project_repo.get_ocr_config(pool, project_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return config


@router.get('/projects/{project_id}/ocr-config', response_model=OcrConfigResponse)
async def get_ocr_config(project_id: uuid.UUID) -> OcrConfigResponse:
    """Get a project's OCR configuration.

    Args:
        project_id: Project UUID.

    Returns:
        OcrConfigResponse: Current OCR config with all engine instances.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    config = await _get_config_or_404(pool, project_id)

    from saegim.api.settings import get_settings

    env_key = get_settings().gemini_api_key

    return OcrConfigResponse(
        default_engine_id=config.get('default_engine_id'),
        engines={eid: EngineInstance(**entry) for eid, entry in config.get('engines', {}).items()},
        env_gemini_api_key=env_key,
    )


# --- Engine Instance CRUD ---


@router.post(
    '/projects/{project_id}/ocr-config/engines',
    response_model=OcrConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_engine(
    project_id: uuid.UUID,
    body: EngineInstanceCreate,
) -> OcrConfigResponse:
    """Register a new engine instance.

    Args:
        project_id: Project UUID.
        body: Engine instance creation data.

    Returns:
        OcrConfigResponse: Updated OCR config.

    Raises:
        HTTPException: If project not found or engine_id collision.
    """
    pool = get_pool()
    config = await _get_config_or_404(pool, project_id)

    engines = dict(config.get('engines', {}))
    existing_ids = set(engines.keys())

    engine_id = body.engine_id or generate_engine_id(body.name, existing_ids)
    if engine_id in existing_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Engine ID '{engine_id}' already exists",
        )

    engines[engine_id] = {
        'engine_type': body.engine_type,
        'name': body.name,
        'config': body.config,
    }

    # If this is the first non-pdfminer engine, set as default
    default_id = config.get('default_engine_id')
    if default_id is None:
        default_id = engine_id

    new_config = {'default_engine_id': default_id, 'engines': engines}
    await project_repo.update_ocr_config(pool, project_id, new_config)

    from saegim.api.settings import get_settings

    return OcrConfigResponse(
        default_engine_id=default_id,
        engines={eid: EngineInstance(**entry) for eid, entry in engines.items()},
        env_gemini_api_key=get_settings().gemini_api_key,
    )


@router.put(
    '/projects/{project_id}/ocr-config/engines/{engine_id}',
    response_model=OcrConfigResponse,
)
async def update_engine(
    project_id: uuid.UUID,
    engine_id: str,
    body: EngineInstanceUpdate,
) -> OcrConfigResponse:
    """Update an existing engine instance.

    Args:
        project_id: Project UUID.
        engine_id: Engine instance ID.
        body: Fields to update (name and/or config).

    Returns:
        OcrConfigResponse: Updated OCR config.

    Raises:
        HTTPException: If project or engine not found.
    """
    pool = get_pool()
    config = await _get_config_or_404(pool, project_id)

    engines = dict(config.get('engines', {}))
    if engine_id not in engines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Engine '{engine_id}' not found",
        )

    entry = dict(engines[engine_id])
    if body.name is not None:
        entry['name'] = body.name
    if body.config is not None:
        # Validate new config against the engine type
        EngineInstance(
            engine_type=entry['engine_type'],
            name=entry['name'],
            config=body.config,
        )
        entry['config'] = body.config

    engines[engine_id] = entry
    new_config = {'default_engine_id': config.get('default_engine_id'), 'engines': engines}
    await project_repo.update_ocr_config(pool, project_id, new_config)

    from saegim.api.settings import get_settings

    return OcrConfigResponse(
        default_engine_id=new_config['default_engine_id'],
        engines={eid: EngineInstance(**e) for eid, e in engines.items()},
        env_gemini_api_key=get_settings().gemini_api_key,
    )


@router.delete(
    '/projects/{project_id}/ocr-config/engines/{engine_id}',
    response_model=OcrConfigResponse,
)
async def delete_engine(
    project_id: uuid.UUID,
    engine_id: str,
) -> OcrConfigResponse:
    """Delete an engine instance.

    If the deleted engine was the default, default_engine_id is cleared.

    Args:
        project_id: Project UUID.
        engine_id: Engine instance ID to delete.

    Returns:
        OcrConfigResponse: Updated OCR config.

    Raises:
        HTTPException: If project or engine not found.
    """
    pool = get_pool()
    config = await _get_config_or_404(pool, project_id)

    engines = dict(config.get('engines', {}))
    if engine_id not in engines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Engine '{engine_id}' not found",
        )

    del engines[engine_id]

    # Clear default if it was the deleted engine
    default_id = config.get('default_engine_id')
    if default_id == engine_id:
        default_id = None

    new_config = {'default_engine_id': default_id, 'engines': engines}
    await project_repo.update_ocr_config(pool, project_id, new_config)

    from saegim.api.settings import get_settings

    return OcrConfigResponse(
        default_engine_id=default_id,
        engines={eid: EngineInstance(**e) for eid, e in engines.items()},
        env_gemini_api_key=get_settings().gemini_api_key,
    )


# --- Default Engine ---


@router.put(
    '/projects/{project_id}/ocr-config/default-engine',
    response_model=OcrConfigResponse,
)
async def set_default_engine(
    project_id: uuid.UUID,
    body: DefaultEngineUpdate,
) -> OcrConfigResponse:
    """Set the default OCR engine for full-page extraction.

    Args:
        project_id: Project UUID.
        body: Engine ID to set as default (None = pdfminer fallback).

    Returns:
        OcrConfigResponse: Updated OCR config.

    Raises:
        HTTPException: If project or engine not found.
    """
    pool = get_pool()
    config = await _get_config_or_404(pool, project_id)

    engines = config.get('engines', {})
    if body.engine_id is not None and body.engine_id not in engines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Engine '{body.engine_id}' not found",
        )

    new_config = {'default_engine_id': body.engine_id, 'engines': engines}
    await project_repo.update_ocr_config(pool, project_id, new_config)

    from saegim.api.settings import get_settings

    return OcrConfigResponse(
        default_engine_id=body.engine_id,
        engines={eid: EngineInstance(**e) for eid, e in engines.items()},
        env_gemini_api_key=get_settings().gemini_api_key,
    )


# --- Connection Test ---


@router.post(
    '/projects/{project_id}/ocr-config/test',
    response_model=OcrConnectionTestResponse,
)
async def test_engine_connection(
    project_id: uuid.UUID,
    body: OcrConnectionTestRequest,
) -> OcrConnectionTestResponse:
    """Test a specific engine's connection.

    Args:
        project_id: Project UUID.
        body: Engine ID to test.

    Returns:
        OcrConnectionTestResponse: Test result.

    Raises:
        HTTPException: If project or engine not found.
    """
    pool = get_pool()
    config = await _get_config_or_404(pool, project_id)

    engines = config.get('engines', {})
    entry = engines.get(body.engine_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Engine '{body.engine_id}' not found",
        )

    from saegim.services.engines.factory import _build_engine_from_type

    try:
        engine = _build_engine_from_type(entry['engine_type'], entry.get('config', {}))
        success, message = engine.test_connection()
    except ValueError as exc:
        success, message = False, str(exc)

    return OcrConnectionTestResponse(success=success, message=message)


# --- Available Engines ---


@router.get(
    '/projects/{project_id}/available-engines',
    response_model=AvailableEnginesResponse,
)
async def get_available_engines(project_id: uuid.UUID) -> AvailableEnginesResponse:
    """Get list of engines available for per-element text extraction.

    Returns all registered engines (excluding pdfminer since it doesn't
    support region-level extraction).

    Args:
        project_id: Project UUID.

    Returns:
        AvailableEnginesResponse: Available engines with IDs and names.

    Raises:
        HTTPException: If project not found.
    """
    pool = get_pool()
    config = await _get_config_or_404(pool, project_id)

    engines_dict = config.get('engines', {})
    engines: list[AvailableEngine] = []
    for eid, entry in engines_dict.items():
        et = entry.get('engine_type', '')
        if et == 'pdfminer':
            continue
        engines.append(
            AvailableEngine(
                engine_id=eid,
                engine_type=et,
                name=entry.get('name', eid),
            )
        )

    return AvailableEnginesResponse(engines=engines)
