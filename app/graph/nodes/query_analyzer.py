"""Query Analyzer Node - understands and optimizes user queries."""

import json
from typing import Any, Dict

from langchain_core.messages import AIMessage

from app.core.config import settings
from app.graph.state import GraphState
from app.services.llm_service import llm_service


def _safe_json_parse(text: str, default: dict) -> dict:
    """Safely parse JSON, return default if invalid or not a dict."""
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
        if isinstance(result, (list, tuple)) and len(result) > 0 and isinstance(result[0], dict):
            return result[0]
    except Exception:
        pass
    return default


def _safe_state(state: Any) -> Dict[str, Any]:
    """Ensure state is dict."""
    if isinstance(state, dict):
        return state
    if isinstance(state, (list, tuple)) and len(state) > 0:
        if isinstance(state[0], dict):
            return state[0]
    return {}


def query_analyzer_node(state: GraphState) -> dict:
    """Analyze user query: rewrite, extract intent, identify keywords."""
    # ✅ DEFENSIVE: Ensure state is dict
    state = _safe_state(state)
    query = state.get("query", "")
    
    if not query:
        return {
            "rewritten_query": "",
            "intent": "factual",
            "search_keywords": [],
            "messages": [AIMessage(content="🔍 Empty query received")],
        }

    system_prompt = """You are a Query Intelligence Analyst. Your task:
1. Rewrite the query for better document retrieval
2. Identify the user's intent (factual, analytical, comparative, procedural)
3. Extract key search keywords
4. Flag if the query is unclear

Return ONLY a valid JSON object:
{
    "rewritten_query": "improved query text",
    "intent": "factual",
    "search_keywords": ["keyword1", "keyword2"],
    "needs_human_clarification": false
}"""

    try:
        response = llm_service.chat_sync(
            system_prompt=system_prompt,
            user_prompt=f"Original user query: {query}"
        )
        result = _safe_json_parse(response, {})
    except Exception:
        result = {}

    rewritten = result.get("rewritten_query", query) if isinstance(result, dict) else query
    intent = result.get("intent", "factual") if isinstance(result, dict) else "factual"
    keywords = result.get("search_keywords", []) if isinstance(result, dict) else []

    return {
        "rewritten_query": rewritten,
        "intent": intent,
        "search_keywords": keywords if isinstance(keywords, list) else [],
        "messages": [AIMessage(content=f"🔍 Query analyzed | Intent: {intent}")],
    }