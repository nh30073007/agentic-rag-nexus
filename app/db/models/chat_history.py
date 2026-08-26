"""Chat history model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.db.base import Base


class ChatHistoryModel(Base):
    """Stores persistent chat conversations and messages."""

    __tablename__ = "chat_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Each conversation has a unique session ID
    session_id = Column(
        String(100),
        index=True,
        nullable=False
    )

    # Conversation title
    # Usually generated from the first user query
    conversation_title = Column(
        String(255),
        nullable=True
    )

    # User message
    query = Column(
        Text,
        nullable=False
    )

    # Optional rewritten query from RAG pipeline
    rewritten_query = Column(
        Text,
        nullable=True
    )

    # AI response
    response = Column(
        Text,
        nullable=True
    )

    # Critic score
    critique_score = Column(
        Float,
        nullable=True
    )

    # Human approval status
    human_approved = Column(
        String(20),
        default="pending"
    )

    # Agent loop count
    loop_count = Column(
        Integer,
        default=0
    )

    # Creation time
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )