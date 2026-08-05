"""Retriever Node - searches vector database for relevant documents."""

from langchain_core.messages import AIMessage

from app.graph.state import GraphState
from app.services.vectorstore_service import vectorstore_service


def retriever_node(state: GraphState) -> dict:
    """
    Retrieve relevant documents from ChromaDB using rewritten query.
    """
    rewritten_query = state.get("rewritten_query") or state["query"]
    collection = state.get("collection_name", "documents")
    keywords = state.get("search_keywords", [])
    
    # Combine rewritten query with keywords for better retrieval
    search_query = rewritten_query
    if keywords:
        search_query += " " + " ".join(keywords)
    
    results = vectorstore_service.search(
        query=search_query,
        top_k=5,
        collection_name=collection,
    )
    
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
    
    return {
        "documents": results,
        "retrieval_score": round(avg_score, 3),
        "messages": [AIMessage(content=f"📚 Retrieved {len(results)} documents (avg score: {avg_score:.3f})")],
    }