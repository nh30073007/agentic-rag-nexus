"""Synthesizer Node - generates answer from retrieved documents."""

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
    """Generate a comprehensive answer using retrieved documents."""
    # ✅ DEFENSIVE
    state = _safe_state(state)
    
    query = state.get("rewritten_query") or state.get("query", "")
    docs = state.get("documents", [])
    critique_feedback = state.get("critique_feedback")
    human_feedback = state.get("human_feedback")
    
    # Ensure docs is list
    if not isinstance(docs, list):
        docs = []
    
    # Build context from retrieved documents
    context_parts = []
    sources = []
    for i, doc in enumerate(docs, 1):
        if isinstance(doc, dict):
            content = doc.get("content", "")[:1200]
            source = doc.get("metadata", {}).get("source", "unknown") if isinstance(doc.get("metadata"), dict) else "unknown"
        else:
            content = str(doc)[:1200]
            source = "unknown"
        context_parts.append(f"[Document {i} | Source: {source}]\n{content}")
        sources.append(source)
    
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No documents retrieved."
    
    # Determine which feedback to use
    feedback = human_feedback or critique_feedback
    
    system_prompt = """You are an expert Answer Synthesizer. Create a clear, accurate, well-structured answer.

RULES:
- Use ONLY the provided documents as source material
- Cite sources naturally (e.g., "According to Document 1...")
- If documents lack sufficient information, clearly state what is missing
- Be concise but complete (2-4 paragraphs)
- Do NOT make up information not present in the documents"""

    user_prompt = f"""User Query: {query}

Retrieved Documents:
{context}

{f'Feedback for improvement: {feedback}' if feedback else ''}

Generate the final answer:"""

    try:
        answer = llm_service.chat_sync(system_prompt, user_prompt)
        confidence = 0.85 if docs else 0.3
    except Exception:
        answer = "Error generating answer. Please try again."
        confidence = 0.0

    loop_count = state.get("loop_count", 0)
    if not isinstance(loop_count, int):
        try:
            loop_count = int(loop_count)
        except Exception:
            loop_count = 0

    return {
        "generation": answer,
        "confidence": confidence,
        "used_sources": list(set(sources)),
        "loop_count": loop_count + 1,
        "messages": [AIMessage(content=f"✍️ Answer synthesized (attempt #{loop_count + 1})")],
    }