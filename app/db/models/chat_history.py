"""Chat history model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.db.base import Base


class ChatHistoryModel(Base):
    """Stores chat conversations."""

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    query = Column(Text, nullable=False)
    rewritten_query = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    critique_score = Column(Float, nullable=True)
    human_approved = Column(String(20), default="pending")  # pending, approved, rejected
    loop_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)