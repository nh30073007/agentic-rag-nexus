"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import chat, health, session, upload

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(upload.router, prefix="/upload", tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(session.router, prefix="", tags=["Session"])