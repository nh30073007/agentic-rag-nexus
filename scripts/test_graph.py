"""Quick test for the LangGraph workflow."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.graph.builder import build_graph
from app.graph.state import GraphState


def test_graph():
    """Test graph compilation and basic flow."""
    print("🔄 Building graph...")
    graph = build_graph()
    print("✅ Graph compiled successfully!")
    
    # Test initial state
    initial_state: GraphState = {
        "query": "What is machine learning?",
        "session_id": "test-123",
        "collection_name": "documents",
        "rewritten_query": None,
        "search_keywords": None,
        "intent": None,
        "documents": None,
        "retrieval_score": None,
        "generation": None,
        "confidence": None,
        "used_sources": None,
        "critique_score": None,
        "critique_feedback": None,
        "issues": None,
        "is_hallucination": None,
        "human_approved": None,
        "human_feedback": None,
        "loop_count": 0,
        "max_iterations": 3,
        "messages": [],
        "metadata": {},
    }
    
    print("\n📊 Graph nodes:", list(graph.nodes.keys()))
    print("🎯 Ready for streaming!")
    print("\n⚠️  Note: Full test requires documents in vectorstore + Groq API key")


if __name__ == "__main__":
    test_graph()