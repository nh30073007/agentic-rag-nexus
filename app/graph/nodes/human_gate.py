"""Human Gate Node - interrupts execution for human approval."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langgraph.types import interrupt

from app.graph.state import GraphState


def _safe_state(state: Any) -> Dict[str, Any]:
    if isinstance(state, dict):
        return state
    if isinstance(state, (list, tuple)) and len(state) > 0:
        if isinstance(state[0], dict):
            return state[0]
    return {}


def human_gate_node(state: GraphState) -> dict:
    """Interrupt the graph and wait for human approval/rejection."""
    # ✅ DEFENSIVE
    state = _safe_state(state)
    
    answer = state.get("generation", "")
    score = state.get("critique_score", 0)
    feedback = state.get("critique_feedback", "")
    loop_count = state.get("loop_count", 0)
    
    # Ensure proper types
    if not isinstance(score, (int, float)):
        try:
            score = float(score)
        except Exception:
            score = 0.0
    
    # interrupt() sends payload to frontend and PAUSES execution
    try:
        human_decision = interrupt({
            "type": "human_approval_required",
            "message": "Please review the generated answer before delivery.",
            "answer_preview": str(answer)[:800] if answer else "",
            "critique_score": score,
            "critique_feedback": str(feedback),
            "loop_count": int(loop_count) if isinstance(loop_count, int) else 0,
        })
    except Exception as e:
        # If interrupt fails, return rejection
        return {
            "human_approved": False,
            "human_feedback": f"Interrupt error: {str(e)}",
            "messages": [AIMessage(content="🛑 Human gate error - auto-rejected")],
        }
    
    # human_decision = {"decision": "approved"|"rejected", "feedback": "..."}
    if isinstance(human_decision, dict):
        decision = human_decision.get("decision", "rejected")
        human_feedback = human_decision.get("feedback", "")
    elif isinstance(human_decision, (list, tuple)) and len(human_decision) > 0:
        # Handle tuple return from interrupt
        if isinstance(human_decision[0], dict):
            decision = human_decision[0].get("decision", "rejected")
            human_feedback = human_decision[0].get("feedback", "")
        else:
            decision = "rejected"
            human_feedback = str(human_decision)
    else:
        decision = "rejected"
        human_feedback = str(human_decision) if human_decision else ""
    
    is_approved = str(decision).lower() == "approved"
    
    return {
        "human_approved": is_approved,
        "human_feedback": human_feedback if not is_approved else "",
        "messages": [AIMessage(content=f"🛑 Human {str(decision).upper()} | Feedback: {human_feedback[:100] if human_feedback else 'None'}")],
    }