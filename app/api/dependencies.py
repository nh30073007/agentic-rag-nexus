"""FastAPI dependencies."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.db.session import SessionLocal
from app.services.llm_service import LLMService
from app.services.vectorstore_service import VectorStoreService
from app.services.document_service import DocumentService
from app.services.session_service import SessionService

security = HTTPBearer(auto_error=False)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return LLMService()


def get_vectorstore_service() -> VectorStoreService:
    """Get vector store service instance."""
    return VectorStoreService()


def get_document_service() -> DocumentService:
    """Get document service instance."""
    return DocumentService()


def get_session_service() -> SessionService:
    """Get session service instance."""
    return SessionService()