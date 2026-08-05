"""Session management endpoints."""

from fastapi import APIRouter
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/session/create")
async def create_session():
    """Create a new chat session."""
    service = SessionService()
    session_id = service.create_session()
    return {
        "session_id": session_id,
        "message": "Session created successfully",
    }


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 10):
    """Get chat history for a session."""
    service = SessionService()
    history = service.get_session_history(session_id, limit)
    
    return {
        "session_id": session_id,
        "history": [
            {
                "query": h.query,
                "response": h.response,
                "critique_score": h.critique_score,
                "human_approved": h.human_approved,
                "created_at": h.created_at,
            }
            for h in history
        ],
    }