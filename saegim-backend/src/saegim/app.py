"""FastAPI application factory and main app instance."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from saegim.api.routes import documents, export, health, pages, projects, users
from saegim.api.settings import Settings, get_settings
from saegim.core.database import close_pool, create_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan: DB pool creation and cleanup.

    Args:
        app: FastAPI application instance.
    """
    settings: Settings = app.state.settings
    await create_pool(
        settings.database_url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
    )
    logger.info('Application started')
    yield
    await close_pool()
    logger.info('Application stopped')


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings instance. If not provided, will use get_settings().

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title='saegim',
        description='(Backend) human-in-the-loop labeling platform for Korean document benchmarks',
        version='0.1.0',
        docs_url='/docs' if settings.debug else None,
        redoc_url='/redoc' if settings.debug else None,
        lifespan=lifespan,
    )

    app.state.settings = settings

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # Include routers
    app.include_router(health.router, prefix='/api/v1', tags=['health'])
    app.include_router(projects.router, prefix='/api/v1', tags=['projects'])
    app.include_router(documents.router, prefix='/api/v1', tags=['documents'])
    app.include_router(pages.router, prefix='/api/v1', tags=['pages'])
    app.include_router(users.router, prefix='/api/v1', tags=['users'])
    app.include_router(export.router, prefix='/api/v1', tags=['export'])

    # Mount static files for serving page images and PDF documents
    storage_path = Path(settings.storage_path)
    images_path = storage_path / 'images'
    images_path.mkdir(parents=True, exist_ok=True)
    app.mount('/storage/images', StaticFiles(directory=str(images_path)), name='images')

    pdfs_path = storage_path / 'pdfs'
    pdfs_path.mkdir(parents=True, exist_ok=True)
    app.mount('/storage/pdfs', StaticFiles(directory=str(pdfs_path)), name='pdfs')

    return app


# Create app instance
app = create_app()
