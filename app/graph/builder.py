"""
LangGraph Builder - assembles the complete Agentic RAG workflow.
"""

from langgraph.graph import END, START, StateGraph

from app.graph.checkpoint import get_checkpointer
from app.graph.edges.conditional import critic_router, human_router
from app.graph.nodes.critic import critic_node
from app.graph.nodes.human_gate import human_gate_node
from app.graph.nodes.query_analyzer import query_analyzer_node
from app.graph.nodes.retriever import retriever_node
from app.graph.nodes.synthesizer import synthesizer_node
from app.graph.state import GraphState


def build_graph():
    """Build and compile the LangGraph state machine."""
    
    workflow = StateGraph(GraphState)
    
    # Register Nodes
    workflow.add_node("query_analyzer", query_analyzer_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("human_gate", human_gate_node)
    
    # Entry Point
    workflow.add_edge(START, "query_analyzer")
    
    # Sequential Flow
    workflow.add_edge("query_analyzer", "retriever")
    workflow.add_edge("retriever", "synthesizer")
    workflow.add_edge("synthesizer", "critic")
    
    # Critic Decision
    workflow.add_conditional_edges(
        "critic",
        critic_router,
        {
            "approved": "human_gate",
            "retry": "synthesizer",
            "max_retries": END,
        }
    )
    
    # Human Gate Decision
    workflow.add_conditional_edges(
        "human_gate",
        human_router,
        {
            "approved": END,
            "retry": "synthesizer",
        }
    )
    
    # Compile with Checkpointing
    checkpointer = get_checkpointer()
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],
    )
    
    return app