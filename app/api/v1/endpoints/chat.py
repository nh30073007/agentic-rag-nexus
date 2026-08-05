"""Chat and streaming endpoints."""

import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from app.core.config import settings
from app.graph.builder import build_graph
from app.graph.state import GraphState
from app.models.chat import ChatRequest, ChatResponse, HumanApprovalRequest
from app.services.session_service import SessionService

router = APIRouter()

# Compiled graph instance
graph_app = build_graph()


async def stream_graph_events(state: GraphState):
    """Stream LangGraph execution events in real-time."""
    config = {"configurable": {"thread_id": state["session_id"]}}
    
    try:
        async for event in graph_app.astream(state, config, stream_mode="updates"):
            for node_name, node_data in event.items():
                if node_name == "__start__":
                    continue
                
                messages = node_data.get("messages", [])
                msg_text = ""
                if messages:
                    msg_text = str(messages[-1].content) if hasattr(messages[-1], "content") else str(messages[-1])
                
                payload = {
                    "type": "node_update",
                    "node": node_name,
                    "data": {k: v for k, v in node_data.items() if k != "messages"},
                    "message": msg_text,
                    "timestamp": str(uuid.uuid4())[:8],
                }
                yield f"data: {json.dumps(payload)}\n\n"
        
        yield f"data: {json.dumps({'type': 'complete', 'message': 'Processing complete'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream the full agentic RAG pipeline with real-time updates."""
    session_id = request.session_id or str(uuid.uuid4())
    
    initial_state: GraphState = {
        "query": request.query,
        "session_id": session_id,
        "collection_name": request.collection_name or "documents",
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
        "max_iterations": settings.MAX_ITERATIONS,
        "messages": [],
        "metadata": {},
    }
    
    return StreamingResponse(
        stream_graph_events(initial_state),
        media_type="text/event-stream",
    )


@router.post("/ask")
async def chat_sync(request: ChatRequest):
    """Synchronous chat (non-streaming)."""
    session_id = request.session_id or str(uuid.uuid4())
    
    initial_state: GraphState = {
        "query": request.query,
        "session_id": session_id,
        "collection_name": request.collection_name or "documents",
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
        "max_iterations": settings.MAX_ITERATIONS,
        "messages": [],
        "metadata": {},
    }
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        result = await graph_app.ainvoke(initial_state, config)
        
        return ChatResponse(
            session_id=session_id,
            query=request.query,
            rewritten_query=result.get("rewritten_query"),
            answer=result.get("generation", "No answer generated"),
            sources=[{"content": d.get("content", "")[:200], "source": d.get("metadata", {}).get("source", "unknown")} 
                     for d in (result.get("documents") or [])],
            critique_score=result.get("critique_score"),
            critique_feedback=result.get("critique_feedback"),
            human_approved=result.get("human_approved"),
            loop_count=result.get("loop_count", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def human_approve(request: HumanApprovalRequest):
    """Resume graph execution with human approval/rejection."""
    config = {"configurable": {"thread_id": request.session_id}}
    
    try:
        # Resume the graph with human decision
        await graph_app.ainvoke(
            Command(resume={
                "decision": request.decision,
                "feedback": request.feedback or "",
            }),
            config,
        )
        
        # Fetch the FINAL state after graph completes
        final_state = await graph_app.aget_state(config)
        values = final_state.values if hasattr(final_state, "values") else {}
        
        generation = values.get("generation", "")
        critique_score = values.get("critique_score")
        
        if request.decision == "approved":
            return {
                "session_id": request.session_id,
                "decision": "approved",
                "final_answer": generation,
                "critique_score": critique_score,
                "message": "Answer approved and delivered.",
            }
        else:
            return {
                "session_id": request.session_id,
                "decision": "rejected",
                "message": "Answer rejected. Graph will retry with feedback.",
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_status(session_id: str):
    """Get current state of a session."""
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        state = await graph_app.aget_state(config)
        
        values = state.values if hasattr(state, "values") else {}
        next_nodes = state.next if hasattr(state, "next") else []
        
        return {
            "session_id": session_id,
            "current_state": {
                "query": values.get("query"),
                "generation": values.get("generation"),
                "rewritten_query": values.get("rewritten_query"),
                "current_node": next_nodes[0] if next_nodes else "completed",
                "next_nodes": list(next_nodes),
                "loop_count": values.get("loop_count", 0),
                "critique_score": values.get("critique_score"),
                "critique_feedback": values.get("critique_feedback"),
                "human_approved": values.get("human_approved"),
                "documents_count": len(values.get("documents", [])),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")