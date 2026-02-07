"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    message: str
    version: str = '0.1.0'


@router.get('/health', response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Health status information.
    """
    return HealthResponse(
        status='healthy',
        message='saegim API is running',
    )


@router.get('/health/ready', response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness check endpoint.

    Returns:
        HealthResponse: Readiness status information.
    """
    # Add any readiness checks here (database, model loading, etc.)
    return HealthResponse(
        status='ready',
        message='saegim API is ready to serve requests',
    )
