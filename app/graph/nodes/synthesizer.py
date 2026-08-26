"""Synthesizer Node — generates answer with fallback."""

import time
import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage

from app.graph.state import GraphState
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


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
    
    # ✅ Context per doc increased to 500 for better answers
    context_parts = []
    sources = []
    for i, doc in enumerate(docs, 1):
        if isinstance(doc, dict):
            content = doc.get("content", "")[:500]  # 300 → 500
            meta = doc.get("metadata", {}) if isinstance(doc.get("metadata"), dict) else {}
            source = meta.get("source", f"doc_{i}")
        else:
            content = str(doc)[:500]
            source = f"doc_{i}"
        context_parts.append(f"[{source}]\n{content}")
        sources.append(source)
    
    context = "\n\n".join(context_parts) if context_parts else "No documents."
    feedback = human_feedback or critique_feedback or ""
    
    system_prompt = """You are an expert Answer Synthesizer. Use ONLY the provided documents.
Rules:
- Cite sources naturally like [source_name]
- State if information is missing
- Be concise but complete (2-4 paragraphs)
- NO made-up information"""

    start_time = time.time()
    answer = None
    error_log = []

    # ATTEMPT 1: Full prompt
    user_prompt_full = f"""Query: {query}

Documents:
{context}

{f'Feedback: {feedback}' if feedback else ''}

Answer:"""

    try:
        logger.info(f"⚡ Synthesizing with {len(docs)} docs, {len(context)} chars...")
        answer = llm_service.chat_sync(system_prompt, user_prompt_full, max_retries=2)
        
        if answer and len(answer) > 15 and "⚠️ Ollama couldn't" not in answer:
            logger.info(f"✅ Full prompt success ({len(answer)} chars)")
        else:
            answer = None
            
    except Exception as e:
        error_log.append(f"Full: {str(e)[:100]}")
        answer = None

    # ATTEMPT 2: Shorter prompt
    if not answer and len(context_parts) > 1:
        try:
            logger.info("🔄 Trying shorter prompt...")
            short_context = "\n\n".join(context_parts[:2])
            user_prompt_short = f"""Query: {query}

Docs:
{short_context}

Answer:"""
            answer = llm_service.chat_sync(system_prompt, user_prompt_short, max_retries=1)
            if answer and len(answer) > 15 and "⚠️ Ollama couldn't" not in answer:
                logger.info(f"✅ Short prompt success ({len(answer)} chars)")
            else:
                answer = None
        except Exception as e:
            error_log.append(f"Short: {str(e)[:100]}")
            answer = None

    # ATTEMPT 3: Query-only fallback
    if not answer:
        try:
            logger.info("🔄 Trying general knowledge...")
            user_prompt_minimal = f"""Answer briefly based on your knowledge:

Query: {query}

Answer:"""
            answer = llm_service.chat_sync(system_prompt, user_prompt_minimal, max_retries=1)
            if answer and len(answer) > 15 and "⚠️ Ollama couldn't" not in answer:
                logger.info(f"✅ General knowledge success ({len(answer)} chars)")
            else:
                answer = None
        except Exception as e:
            error_log.append(f"Minimal: {str(e)[:100]}")
            answer = None

    # Final fallback
    if not answer or len(answer.strip()) < 10:
        answer = (
            "I apologize, but I couldn't generate an answer at this moment.\n"
            "Possible reasons:\n"
            "1. Ollama is not running or the model is not loaded\n"
            "2. The request timed out (local models can be slow)\n"
            "3. The documents don't contain relevant information\n\n"
            f"Details: {'; '.join(error_log) if error_log else 'Unknown error'}"
        )

    loop_count = state.get("loop_count", 0)
    if not isinstance(loop_count, int):
        try:
            loop_count = int(loop_count)
        except Exception:
            loop_count = 0

    elapsed = time.time() - start_time
    logger.info(f"⏱️ Synthesis done in {elapsed:.2f}s")

    return {
        "generation": answer,
        "confidence": 0.85 if (docs and "Ollama" not in answer and "apologize" not in answer) else 0.3,
        "used_sources": list(set(sources)),
        "loop_count": loop_count + 1,
        "messages": [AIMessage(content=f"✍️ Synthesized ({len(answer)} chars, {elapsed:.1f}s)")],
    }