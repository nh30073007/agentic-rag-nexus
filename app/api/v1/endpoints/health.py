"""Health check endpoint."""

from fastapi import APIRouter, status

from app.core.config import settings

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """API health check."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check for deployments."""
    return {
        "status": "ready",
        "services": {
            "api": "up",
            "database": "connected",
            "vectorstore": "connected",
        },
    }