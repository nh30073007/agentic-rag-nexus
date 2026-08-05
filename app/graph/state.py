"""
LangGraph State Definition.
This is the central state that flows through the graph nodes.
"""

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """
    TypedDict representing the state of our agentic RAG graph.
    This state is passed between nodes and updated at each step.
    """
    
    # --- Input ---
    query: str
    """Original user query."""
    
    session_id: str
    """Unique session identifier."""
    
    collection_name: str
    """ChromaDB collection to search."""
    
    # --- Query Analysis Node ---
    rewritten_query: Optional[str]
    """Optimized query after analysis."""
    
    search_keywords: Optional[List[str]]
    """Extracted keywords for retrieval."""
    
    intent: Optional[str]
    """Detected query intent."""
    
    # --- Retriever Node ---
    documents: Optional[List[Dict[str, Any]]]
    """Retrieved documents from vector store."""
    
    retrieval_score: Optional[float]
    """Retrieval quality score."""
    
    # --- Synthesizer Node ---
    generation: Optional[str]
    """Generated answer."""
    
    confidence: Optional[float]
    """Confidence score of generation."""
    
    used_sources: Optional[List[str]]
    """Sources used in generation."""
    
    # --- Critic Node ---
    critique_score: Optional[float]
    """Quality score from critic (0-10)."""
    
    critique_feedback: Optional[str]
    """Detailed feedback from critic."""
    
    issues: Optional[List[str]]
    """List of issues found."""
    
    is_hallucination: Optional[bool]
    """Whether hallucination was detected."""
    
    # --- Human-in-the-Loop ---
    human_approved: Optional[bool]
    """Human approval status: True=approved, False=rejected, None=pending."""
    
    human_feedback: Optional[str]
    """Optional feedback from human."""
    
    # --- Loop Control ---
    loop_count: int
    """Number of retry loops performed."""
    
    max_iterations: int
    """Maximum allowed iterations."""
    
    # --- Messages (for LangGraph checkpointing) ---
    messages: Annotated[list, add_messages]
    """Conversation messages for LangGraph."""
    
    # --- Metadata ---
    metadata: Optional[Dict[str, Any]]
    """Additional metadata (timestamps, tokens, etc.)."""