"""Synthesizer Node - generates answer from retrieved documents."""

from langchain_core.messages import AIMessage

from app.graph.state import GraphState
from app.services.llm_service import llm_service


def synthesizer_node(state: GraphState) -> dict:
    """
    Generate a comprehensive answer using retrieved documents.
    Increments loop_count each time it runs (tracks retry attempts).
    """
    query = state.get("rewritten_query") or state["query"]
    docs = state.get("documents", [])
    critique_feedback = state.get("critique_feedback")
    human_feedback = state.get("human_feedback")
    
    # Build context from retrieved documents
    context_parts = []
    sources = []
    for i, doc in enumerate(docs, 1):
        content = doc.get("content", "")[:1200]  # Limit per doc
        source = doc.get("metadata", {}).get("source", "unknown")
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

    return {
        "generation": answer,
        "confidence": confidence,
        "used_sources": list(set(sources)),
        "loop_count": state.get("loop_count", 0) + 1,  # Track iteration
        "messages": [AIMessage(content=f"✍️ Answer synthesized (attempt #{state.get('loop_count', 0) + 1})")],
    }