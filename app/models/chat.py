"""Pydantic schemas for chat operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat query."""
    query: str = Field(..., min_length=1, max_length=5000, description="User query")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    collection_name: Optional[str] = Field(default="documents", description="Vector collection to search")


class ChatResponse(BaseModel):
    """Response schema for chat."""
    session_id: str
    query: str
    rewritten_query: Optional[str] = None
    answer: str
    sources: List[Dict[str, Any]] = []
    critique_score: Optional[float] = None
    critique_feedback: Optional[str] = None
    human_approved: Optional[bool] = None
    loop_count: int = 0
    processing_time_seconds: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HumanApprovalRequest(BaseModel):
    """Request schema for human approval."""
    session_id: str
    decision: str = Field(..., pattern="^(approved|rejected)$")
    feedback: Optional[str] = Field(default=None, max_length=1000)


class HumanApprovalResponse(BaseModel):
    """Response schema for human approval."""
    session_id: str
    decision: str
    final_answer: Optional[str] = None
    message: str