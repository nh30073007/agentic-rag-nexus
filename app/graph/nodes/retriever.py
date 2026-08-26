"""Retriever Node - searches vector database for relevant documents."""

from typing import Any, Dict

from langchain_core.messages import AIMessage

from app.graph.state import GraphState
from app.services.vectorstore_service import vectorstore_service


def _safe_state(state: Any) -> Dict[str, Any]:
    if isinstance(state, dict):
        return state
    if isinstance(state, (list, tuple)) and len(state) > 0:
        if isinstance(state[0], dict):
            return state[0]
    return {}


def retriever_node(state: GraphState) -> dict:
    """Retrieve relevant documents from ChromaDB with fallback."""
    state = _safe_state(state)
    
    rewritten_query = state.get("rewritten_query") or state.get("query", "")
    collection = state.get("collection_name", "documents")
    keywords = state.get("search_keywords", [])
    
    # Combine rewritten query with keywords
    search_query = rewritten_query
    if isinstance(keywords, list) and keywords:
        search_query += " " + " ".join(str(k) for k in keywords)
    
    # 1. Try semantic search first
    results = []
    try:
        results = vectorstore_service.search(
            query=search_query,
            top_k=5,
            collection_name=collection,
        )
    except Exception as e:
        print(f"⚠️ Semantic search error: {e}")
        results = []
    
    avg_score = sum(r.get("score", 0) for r in results) / len(results) if results else 0.0
    
    # ✅ FALLBACK: If no results or poor match, get all documents
    if not results or avg_score < 0.3:
        print(f"⚠️ Low semantic match (score={avg_score:.3f}), falling back to all docs...")
        fallback_results = vectorstore_service.get_all_documents(
            collection_name=collection,
            limit=10,
        )
        if fallback_results:
            results = fallback_results
            avg_score = 0.5  # Neutral score for fallback
    
    return {
        "documents": results if isinstance(results, list) else [],
        "retrieval_score": round(avg_score, 3),
        "messages": [AIMessage(content=f"📚 Retrieved {len(results)} documents (avg score: {avg_score:.3f})")],
    }