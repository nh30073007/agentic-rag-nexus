"""Human approval log model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.db.base import Base


class HumanApprovalModel(Base):
    """Logs human approval/rejection decisions."""

    __tablename__ = "human_approvals"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    query = Column(Text, nullable=False)
    proposed_answer = Column(Text, nullable=False)
    critique_score = Column(Float, nullable=False)
    critique_feedback = Column(Text, nullable=True)
    decision = Column(String(20), nullable=False)  # approved, rejected
    feedback = Column(Text, nullable=True)  # optional human feedback
    response_time_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)