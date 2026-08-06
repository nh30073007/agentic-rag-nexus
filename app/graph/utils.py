"""Defensive utilities for LangGraph nodes."""

from typing import Any, Dict


def safe_state(state: Any) -> Dict[str, Any]:
    """
    Ensure state is always a dict.
    LangGraph sometimes passes tuple/list instead of dict.
    """
    if isinstance(state, dict):
        return state
    elif isinstance(state, (list, tuple)) and len(state) > 0:
        if isinstance(state[0], dict):
            return state[0]
        else:
            return {"_raw_tuple": state}
    else:
        return {}


def safe_get(state: Any, key: str, default: Any = None) -> Any:
    """Safely get from state, handles any type gracefully."""
    s = safe_state(state)
    return s.get(key, default)