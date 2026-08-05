"""Conditional edge routing functions for the agentic graph."""

from app.core.config import settings
from app.graph.state import GraphState


def critic_router(state: GraphState) -> str:
    """
    Decide where to go after critic node:
    - approved: score >= threshold → human gate
    - retry: score < threshold, loops remaining → back to synthesizer
    - max_retries: exhausted all loops → force end
    """
    score = state.get("critique_score", 0)
    loop_count = state.get("loop_count", 0)
    max_iter = state.get("max_iterations", settings.MAX_ITERATIONS)
    
    if loop_count >= max_iter:
        return "max_retries"
    if score >= settings.CRITIC_MIN_SCORE:
        return "approved"
    return "retry"


def human_router(state: GraphState) -> str:
    """
    Decide where to go after human gate:
    - approved: human said OK → END
    - retry: human rejected → back to synthesizer with feedback
    """
    approved = state.get("human_approved")
    
    if approved is True:
        return "approved"
    # Rejected → go back to synthesizer, which will use human_feedback
    return "retry"