"""Synthesizer Node — generates answer with fallback on error."""

from typing import Any, Dict

from langchain_core.messages import AIMessage

from app.graph.state import GraphState
from app.services.llm_service import llm_service


def _safe_state(state: Any) -> Dict[str, Any]:
    if isinstance(state, dict):
        return state
    if isinstance(state, (list, tuple)) and len(state) > 0:
        if isinstance(state[0], dict):
            return state[0]
    return {}


def synthesizer_node(state: GraphState) -> dict:
    """Generate answer — with fallback if full prompt fails."""
    state = _safe_state(state)
    
    query = state.get("rewritten_query") or state.get("query", "")
    docs = state.get("documents", [])
    critique_feedback = state.get("critique_feedback")
    human_feedback = state.get("human_feedback")
    
    if not isinstance(docs, list):
        docs = []
    
    # Build context
    context_parts = []
    sources = []
    for i, doc in enumerate(docs, 1):
        if isinstance(doc, dict):
            content = doc.get("content", "")[:800]  # Shorter limit for safety
            meta = doc.get("metadata", {}) if isinstance(doc.get("metadata"), dict) else {}
            source = meta.get("source", "unknown")
        else:
            content = str(doc)[:800]
            source = "unknown"
        context_parts.append(f"[Doc{i}:{source}]\n{content}")
        sources.append(source)
    
    context = "\n\n".join(context_parts) if context_parts else "No documents."
    feedback = human_feedback or critique_feedback or ""
    
    system_prompt = """You are an expert Answer Synthesizer. Use ONLY the provided documents.
Rules:
- Cite sources naturally
- State if information is missing
- Be concise (2-4 paragraphs)
- NO made-up information"""

    # ==========================================
    # ATTEMPT 1: Full prompt with documents
    # ==========================================
    user_prompt_full = f"""Query: {query}

Documents:
{context}

{f'Feedback: {feedback}' if feedback else ''}

Answer:"""

    answer = None
    error_msg = None
    
    try:
        answer = llm_service.chat_sync(system_prompt, user_prompt_full)
        if answer and len(answer) > 20:
            # Success!
            pass
    except Exception as e:
        error_msg = str(e)
        answer = None

    # ==========================================
    # ATTEMPT 2: Shorter prompt (if first fails)
    # ==========================================
    if not answer:
        try:
            short_context = "\n".join(context_parts[:2]) if len(context_parts) > 2 else "\n".join(context_parts)
            user_prompt_short = f"""Query: {query}

Docs:
{short_context}

Answer:"""
            answer = llm_service.chat_sync(system_prompt, user_prompt_short)
        except Exception as e:
            error_msg = f"{error_msg}; Short fallback: {str(e)}"
            answer = None

    # ==========================================
    # ATTEMPT 3: Query-only fallback (no docs)
    # ==========================================
    if not answer:
        try:
            user_prompt_minimal = f"""Based on general knowledge, answer briefly:

Query: {query}

Answer:"""
            answer = llm_service.chat_sync(system_prompt, user_prompt_minimal)
        except Exception as e:
            error_msg = f"{error_msg}; Minimal fallback: {str(e)}"
            answer = f"Sorry, I couldn't generate an answer. Error: {error_msg[:200]}"

    # Ensure answer is valid string
    if not answer or len(answer.strip()) < 10:
        answer = "I apologize, but I couldn't synthesize a proper answer from the available documents. Please try rephrasing your question or uploading more relevant documents."

    loop_count = state.get("loop_count", 0)
    if not isinstance(loop_count, int):
        try:
            loop_count = int(loop_count)
        except Exception:
            loop_count = 0

    return {
        "generation": answer,
        "confidence": 0.85 if docs and "Error" not in answer else 0.3,
        "used_sources": list(set(sources)),
        "loop_count": loop_count + 1,
        "messages": [AIMessage(content=f"✍️ Answer synthesized ({len(answer)} chars)")],
    }