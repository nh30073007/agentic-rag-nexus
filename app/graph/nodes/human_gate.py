"""Human Gate Node - interrupts execution for human approval."""

from langchain_core.messages import AIMessage
from langgraph.types import interrupt

from app.graph.state import GraphState


def human_gate_node(state: GraphState) -> dict:
    """
    Interrupt the graph and wait for human approval/rejection.
    This pauses execution until resumed via Command(resume=...).
    """
    answer = state.get("generation", "")
    score = state.get("critique_score", 0)
    feedback = state.get("critique_feedback", "")
    
    # interrupt() sends this payload to the frontend and PAUSES execution
    # When human responds via Command(resume={...}), that dict is returned
    human_decision = interrupt({
        "type": "human_approval_required",
        "message": "Please review the generated answer before delivery.",
        "answer_preview": answer[:800] if answer else "",
        "critique_score": score,
        "critique_feedback": feedback,
        "loop_count": state.get("loop_count", 0),
    })
    
    # human_decision = {"decision": "approved"|"rejected", "feedback": "..."}
    decision = human_decision.get("decision", "rejected") if isinstance(human_decision, dict) else "rejected"
    human_feedback = human_decision.get("feedback", "") if isinstance(human_decision, dict) else ""
    
    is_approved = decision == "approved"
    
    return {
        "human_approved": is_approved,
        "human_feedback": human_feedback if not is_approved else "",
        "messages": [AIMessage(content=f"🛑 Human {decision.upper()} | Feedback: {human_feedback[:100] if human_feedback else 'None'}")],
    }