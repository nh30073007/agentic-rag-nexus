"""Pydantic schemas for session management."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionState(BaseModel):
    """Session state for tracking graph execution."""
    session_id: str
    status: str = Field(default="active")  # active, paused, completed, error
    current_node: Optional[str] = None
    query: Optional[str] = None
    rewritten_query: Optional[str] = None
    documents: List[Dict[str, Any]] = []
    generation: Optional[str] = None
    critique_score: Optional[float] = None
    critique_feedback: Optional[str] = None
    human_approved: Optional[bool] = None
    loop_count: int = 0
    max_iterations: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionCreateResponse(BaseModel):
    """Response for creating a new session."""
    session_id: str
    message: str
    created_at: datetime