"""Pydantic schemas for agent outputs."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryAnalysisOutput(BaseModel):
    """Output from Query Analyst agent."""
    rewritten_query: str = Field(..., description="Optimized query for retrieval")
    intent: str = Field(..., description="Detected intent: factual, analytical, comparative, etc.")
    search_keywords: List[str] = Field(default=[], description="Keywords for vector search")
    needs_human_clarification: bool = Field(default=False)


class RetrievalOutput(BaseModel):
    """Output from Retriever agent."""
    documents: List[Dict[str, Any]] = Field(default=[], description="Retrieved documents")
    retrieval_score: Optional[float] = None
    source_count: int = 0


class SynthesisOutput(BaseModel):
    """Output from Synthesizer agent."""
    answer: str = Field(..., description="Generated answer")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    used_sources: List[str] = Field(default=[])


class CriticOutput(BaseModel):
    """Output from Critic agent."""
    score: float = Field(..., ge=0.0, le=10.0, description="Quality score 0-10")
    feedback: str = Field(..., description="Detailed feedback")
    issues: List[str] = Field(default=[], description="List of issues found")
    is_hallucination: bool = Field(default=False)
    needs_retry: bool = Field(default=False)


class AgentProgress(BaseModel):
    """Real-time progress of agent execution."""
    agent_name: str
    status: str = Field(..., pattern="^(running|completed|failed|waiting)$")
    timestamp: str
    message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None