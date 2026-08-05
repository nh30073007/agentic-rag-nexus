"""Session management service."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.db.models.chat_history import ChatHistoryModel
from app.db.session import SessionLocal


class SessionService:
    """Service for managing chat sessions."""

    def __init__(self):
        pass

    def create_session(self) -> str:
        """Create a new session ID."""
        return str(uuid.uuid4())

    def save_chat_turn(
        self,
        session_id: str,
        query: str,
        rewritten_query: Optional[str] = None,
        response: Optional[str] = None,
        critique_score: Optional[float] = None,
        human_approved: Optional[str] = None,
        loop_count: int = 0,
    ) -> ChatHistoryModel:
        """Save a chat turn to database."""
        db = SessionLocal()
        try:
            chat = ChatHistoryModel(
                session_id=session_id,
                query=query,
                rewritten_query=rewritten_query,
                response=response,
                critique_score=critique_score,
                human_approved=human_approved or "pending",
                loop_count=loop_count,
            )
            db.add(chat)
            db.commit()
            db.refresh(chat)
            return chat
        finally:
            db.close()

    def update_response(
        self,
        session_id: str,
        response: str,
        critique_score: Optional[float] = None,
    ) -> None:
        """Update the response for the latest chat turn."""
        db = SessionLocal()
        try:
            chat = (
                db.query(ChatHistoryModel)
                .filter(ChatHistoryModel.session_id == session_id)
                .order_by(ChatHistoryModel.created_at.desc())
                .first()
            )
            if chat:
                chat.response = response
                if critique_score is not None:
                    chat.critique_score = critique_score
                db.commit()
        finally:
            db.close()

    def update_approval(self, session_id: str, decision: str) -> None:
        """Update human approval status."""
        db = SessionLocal()
        try:
            chat = (
                db.query(ChatHistoryModel)
                .filter(ChatHistoryModel.session_id == session_id)
                .order_by(ChatHistoryModel.created_at.desc())
                .first()
            )
            if chat:
                chat.human_approved = decision
                db.commit()
        finally:
            db.close()

    def get_session_history(self, session_id: str, limit: int = 10) -> list:
        """Get chat history for a session."""
        db = SessionLocal()
        try:
            chats = (
                db.query(ChatHistoryModel)
                .filter(ChatHistoryModel.session_id == session_id)
                .order_by(ChatHistoryModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return chats
        finally:
            db.close()


# Singleton instance
session_service = SessionService()




