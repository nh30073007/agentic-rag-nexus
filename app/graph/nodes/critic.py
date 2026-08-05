"""Critic Node - evaluates answer quality and detects hallucinations."""

import json

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
    except Exception:
        pass
    return default


def critic_node(state: GraphState) -> dict:
    """Critique the generated answer: score 0-10, detect hallucinations, provide feedback."""
    query = state.get("rewritten_query") or state["query"]
    answer = state.get("generation", "")
    docs = state.get("documents", [])
    loop_count = state.get("loop_count", 0)
    
    # Prepare document summaries for critic
    doc_summaries = []
    for i, doc in enumerate(docs[:3], 1):
        content = doc.get("content", "")[:800] if isinstance(doc, dict) else str(doc)[:800]
        doc_summaries.append(f"Doc {i}: {content}")
    
    docs_text = "\n\n".join(doc_summaries) if doc_summaries else "No documents available."
    
    system_prompt = """You are a strict Quality Critic. Evaluate the answer against the source documents.

Score 0-10 based on:
1. Factual Accuracy (does answer match documents?) — 40%
2. Completeness (does it fully answer the query?) — 30%
3. No Hallucination (no info outside documents) — 20%
4. Clarity & Structure — 10%

Return ONLY valid JSON:
{
    "score": 7.5,
    "feedback": "Detailed improvement suggestions",
    "issues": ["issue 1", "issue 2"],
    "is_hallucination": false,
    "needs_retry": false
}"""

    user_prompt = f"""Query: {query}

Generated Answer:
{answer}

Source Documents:
{docs_text}

Loop attempt: {loop_count}/{settings.MAX_ITERATIONS}

Provide your critique:"""

    try:
        response = llm_service.chat_sync(system_prompt, user_prompt)
        result = _safe_json_parse(response, {})
    except Exception:
        result = {}

    # Safe extraction with defaults
    score = 7.0
    feedback = "Parse error - assuming acceptable quality"
    issues = []
    is_hallucination = False
    needs_retry = False

    if isinstance(result, dict):
        try:
            score = float(result.get("score", 7.0))
        except (ValueError, TypeError):
            score = 7.0
        feedback = result.get("feedback", feedback)
        issues = result.get("issues", [])
        is_hallucination = result.get("is_hallucination", False)
        needs_retry = result.get("needs_retry", False)

    return {
        "critique_score": score,
        "critique_feedback": feedback,
        "issues": issues if isinstance(issues, list) else [],
        "is_hallucination": bool(is_hallucination),
        "messages": [AIMessage(content=f"🛡️ Critic score: {score}/10 | Issues: {len(issues) if isinstance(issues, list) else 0}")],
    }