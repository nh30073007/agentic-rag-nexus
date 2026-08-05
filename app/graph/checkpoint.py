"""Checkpoint configuration for LangGraph state persistence."""

from langgraph.checkpoint.memory import MemorySaver


def get_checkpointer():
    """
    Get checkpointer for graph state persistence.
    Using in-memory for development (fast, no setup).
    For production: switch to SqliteSaver or PostgresSaver.
    """
    return MemorySaver()