"""Pydantic schemas for document operations."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload."""
    collection_name: Optional[str] = Field(default="default", description="Vector collection name")


class DocumentResponse(BaseModel):
    """Response schema for uploaded document."""
    id: int
    filename: str
    file_type: str
    file_size: int
    collection_name: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response schema for listing documents."""
    documents: List[DocumentResponse]
    total: int