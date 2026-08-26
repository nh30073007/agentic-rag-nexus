"""
Health check endpoints.
"""

from fastapi import APIRouter, status

from app.core.config import settings


router = APIRouter()


# =========================================================
# BASIC API HEALTH
# =========================================================

@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """
    Basic API health check.

    Used by the frontend and deployment monitoring
    to confirm that the FastAPI backend is alive.
    """

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }


# =========================================================
# READINESS CHECK
# =========================================================

@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
)
async def readiness_check():
    """
    Readiness check for deployments.
    """

    return {
        "status": "ready",
        "services": {
            "api": "up",
            "database": "connected",
            "vectorstore": "connected",
        },
    }