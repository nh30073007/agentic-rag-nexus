"""Chat, streaming and persistent conversation history endpoints."""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.chat_history import ChatHistoryModel
from app.db.session import get_db
from app.graph.builder import build_graph
from app.graph.state import GraphState
from app.models.chat import (
    ChatRequest,
    ChatResponse,
    HumanApprovalRequest,
)
from app.services.llm_service import llm_service
from app.services.vectorstore_service import vectorstore_service


# =========================================================
# ROUTER / CONFIG
# =========================================================

router = APIRouter()

graph_app = build_graph()

LLM_TIMEOUT = getattr(
    settings,
    "LLM_API_TIMEOUT",
    120,
)

VECTOR_TIMEOUT = getattr(
    settings,
    "VECTOR_SEARCH_TIMEOUT",
    10,
)

logger = logging.getLogger(__name__)


# =========================================================
# CONVERSATION HELPERS
# =========================================================

def generate_conversation_title(query: str) -> str:
    """
    Generate a short conversation title
    from the first user query.
    """

    query = (query or "").strip()

    if not query:
        return "New Conversation"

    query = " ".join(query.split())

    max_length = 55

    if len(query) > max_length:
        return query[:max_length].rstrip() + "..."

    return query


def get_existing_conversation_title(
    db: Session,
    session_id: str,
):
    """
    Get existing conversation title.

    First message creates the title.
    Later messages use the same title.
    """

    first_row = (
        db.query(ChatHistoryModel)
        .filter(
            ChatHistoryModel.session_id == session_id
        )
        .order_by(
            ChatHistoryModel.created_at.asc()
        )
        .first()
    )

    if not first_row:
        return None

    title = getattr(
        first_row,
        "conversation_title",
        None,
    )

    if title:
        return title

    return generate_conversation_title(
        first_row.query
    )


def save_chat_to_history(
    db: Session,
    session_id: str,
    query: str,
    answer: str,
    critique_score=None,
    rewritten_query=None,
    human_approved: str = "approved",
    loop_count: int = 0,
):
    """
    Save one complete user + AI interaction.

    All rows with the same session_id
    belong to the same conversation.
    """

    try:

        conversation_title = (
            get_existing_conversation_title(
                db=db,
                session_id=session_id,
            )
        )

        if not conversation_title:

            conversation_title = (
                generate_conversation_title(
                    query
                )
            )

        chat_row = ChatHistoryModel(
            session_id=session_id,
            conversation_title=conversation_title,
            query=query,
            rewritten_query=rewritten_query,
            response=answer,
            critique_score=critique_score,
            human_approved=human_approved,
            loop_count=loop_count,
        )

        db.add(chat_row)

        db.commit()

        db.refresh(chat_row)

        logger.info(
            "Chat saved | session=%s | row=%s",
            session_id,
            chat_row.id,
        )

        return chat_row

    except Exception as e:

        db.rollback()

        logger.error(
            "Failed to save chat history: %s",
            str(e),
        )

        return None


def create_saved_response(
    db: Session,
    session_id: str,
    query: str,
    answer: str,
    critique_score,
    loop_count: int = 0,
    rewritten_query=None,
    human_approved: str = "approved",
):
    """
    Save response to database and return
    a normal ChatResponse.
    """

    save_chat_to_history(
        db=db,
        session_id=session_id,
        query=query,
        answer=answer,
        critique_score=critique_score,
        rewritten_query=rewritten_query,
        human_approved=human_approved,
        loop_count=loop_count,
    )

    return ChatResponse(
        session_id=session_id,
        query=query,
        answer=answer,
        critique_score=critique_score,
        loop_count=loop_count,
    )


# =========================================================
# CONVERSATION HISTORY API
# =========================================================

@router.get("/conversations")
def get_conversations(
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get all conversations.

    Conversations are grouped by session_id.
    Latest conversation activity appears first.
    """

    try:

        limit = max(
            1,
            min(limit, 500),
        )

        rows = (
            db.query(ChatHistoryModel)
            .order_by(
                ChatHistoryModel.created_at.desc()
            )
            .all()
        )

        conversations = {}
        conversation_order = []

        for row in rows:

            session_id = row.session_id

            if session_id not in conversations:

                title = getattr(
                    row,
                    "conversation_title",
                    None,
                )

                if not title:

                    title = generate_conversation_title(
                        row.query
                    )

                conversations[session_id] = {
                    "session_id": session_id,
                    "title": title,
                    "created_at": (
                        row.created_at.isoformat()
                        if row.created_at
                        else None
                    ),
                    "updated_at": (
                        row.created_at.isoformat()
                        if row.created_at
                        else None
                    ),
                    "message_count": 0,
                }

                conversation_order.append(
                    session_id
                )

            conversations[session_id][
                "message_count"
            ] += 1

        result = [
            conversations[session_id]
            for session_id in conversation_order[:limit]
        ]

        return {
            "conversations": result,
            "total": len(result),
        }

    except Exception as e:

        logger.error(
            "Failed to get conversations: %s",
            str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to load conversation history.",
        )


@router.get("/conversations/{session_id}")
def get_conversation(
    session_id: str,
    db: Session = Depends(get_db),
):
    """
    Load one complete conversation.
    """

    try:

        rows = (
            db.query(ChatHistoryModel)
            .filter(
                ChatHistoryModel.session_id
                == session_id
            )
            .order_by(
                ChatHistoryModel.created_at.asc(),
                ChatHistoryModel.id.asc(),
            )
            .all()
        )

        if not rows:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        first_row = rows[0]

        title = getattr(
            first_row,
            "conversation_title",
            None,
        )

        if not title:

            title = generate_conversation_title(
                first_row.query
            )

        messages = []

        for row in rows:

            messages.append(
                {
                    "id": f"user_{row.id}",
                    "role": "user",
                    "content": row.query,
                    "created_at": (
                        row.created_at.isoformat()
                        if row.created_at
                        else None
                    ),
                }
            )

            if row.response:

                messages.append(
                    {
                        "id": (
                            f"assistant_{row.id}"
                        ),
                        "role": "assistant",
                        "content": row.response,
                        "critique_score": (
                            row.critique_score
                        ),
                        "human_approved": (
                            row.human_approved
                        ),
                        "loop_count": (
                            row.loop_count
                        ),
                        "created_at": (
                            row.created_at.isoformat()
                            if row.created_at
                            else None
                        ),
                    }
                )

        return {
            "session_id": session_id,
            "title": title,
            "messages": messages,
            "message_count": len(messages),
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(
            "Failed to load conversation %s: %s",
            session_id,
            str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to load conversation.",
        )


@router.delete("/conversations/{session_id}")
def delete_conversation(
    session_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete all messages belonging
    to one conversation.
    """

    try:

        deleted_count = (
            db.query(ChatHistoryModel)
            .filter(
                ChatHistoryModel.session_id
                == session_id
            )
            .delete(
                synchronize_session=False
            )
        )

        if deleted_count == 0:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        db.commit()

        return {
            "success": True,
            "session_id": session_id,
            "deleted_rows": deleted_count,
        }

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        logger.error(
            "Failed to delete conversation: %s",
            str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation.",
        )


# =========================================================
# VAGUE QUERY DETECTION
# =========================================================

def _is_vague_query(query: str) -> bool:
    """
    Detect vague/follow-up queries
    about the document.
    """

    vague_keywords = [
        "more",
        "tell me",
        "explain more",
        "about this",
        "this pdf",
        "the document",
        "summarize",
        "overview",
        "what else",
        "details",
        "describe",
        "elaborate",
        "anything else",
        "further",
        "about it",
    ]

    q = (query or "").lower()

    return any(
        keyword in q
        for keyword in vague_keywords
    )


# =========================================================
# STREAM GRAPH EVENTS
# =========================================================

async def stream_graph_events(
    state: GraphState,
):
    """
    Stream LangGraph execution events.
    """

    config = {
        "configurable": {
            "thread_id": state["session_id"],
        }
    }

    try:

        async for event in graph_app.astream(
            state,
            config,
            stream_mode="updates",
        ):

            for node_name, node_data in event.items():

                if node_name == "__start__":
                    continue

                messages = node_data.get(
                    "messages",
                    [],
                )

                msg_text = ""

                if messages:

                    last_message = messages[-1]

                    if hasattr(
                        last_message,
                        "content",
                    ):

                        msg_text = str(
                            last_message.content
                        )

                    else:

                        msg_text = str(
                            last_message
                        )

                payload = {
                    "type": "node_update",
                    "node": node_name,
                    "data": {
                        key: value
                        for key, value
                        in node_data.items()
                        if key != "messages"
                    },
                    "message": msg_text,
                    "timestamp": (
                        str(uuid.uuid4())[:8]
                    ),
                }

                json_payload = json.dumps(
                    payload,
                    default=str,
                )

                yield (
                    f"data: {json_payload}\n\n"
                )

        complete_payload = {
            "type": "complete",
            "message": "Processing complete",
        }

        complete_json = json.dumps(
            complete_payload,
            default=str,
        )

        yield (
            f"data: {complete_json}\n\n"
        )

    except Exception as e:

        logger.error(
            "Stream error: %s",
            str(e),
        )

        error_payload = {
            "type": "error",
            "message": str(e),
        }

        error_json = json.dumps(
            error_payload,
            default=str,
        )

        yield (
            f"data: {error_json}\n\n"
        )


# =========================================================
# STREAM ENDPOINT
# =========================================================

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
):
    """
    Stream the full agentic RAG pipeline.
    """

    session_id = (
        request.session_id
        or str(uuid.uuid4())
    )

    initial_state: GraphState = {
        "query": request.query,
        "session_id": session_id,
        "collection_name": (
            request.collection_name
            or "documents"
        ),
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
        "max_iterations": (
            settings.MAX_ITERATIONS
        ),
        "messages": [],
        "metadata": {},
    }

    return StreamingResponse(
        stream_graph_events(
            initial_state
        ),
        media_type="text/event-stream",
    )


# =========================================================
# MAIN CHAT ENDPOINT
# =========================================================

@router.post("/ask")
async def chat_sync(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Synchronous chat with:

    - Semantic document search
    - Fallback retrieval
    - General knowledge fallback
    - Timeout handling
    - Persistent conversation history
    """

    session_id = (
        request.session_id
        or str(uuid.uuid4())
    )

    query = (
        request.query
        or ""
    ).strip()

    if not query:

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    collection_name = (
        request.collection_name
        or "documents"
    )

    is_vague = _is_vague_query(
        query
    )

    logger.info(
        "CHAT | query=%s | vague=%s",
        query[:60],
        is_vague,
    )

    try:

        # =============================================
        # 1. SEMANTIC SEARCH
        # =============================================

        docs = []

        try:

            docs = await asyncio.wait_for(
                asyncio.to_thread(
                    vectorstore_service.search,
                    query,
                    5,
                    collection_name,
                ),
                timeout=VECTOR_TIMEOUT,
            )

            logger.info(
                "Semantic search returned %s docs",
                len(docs),
            )

        except asyncio.TimeoutError:

            logger.warning(
                "Vector search timeout"
            )

        except Exception as e:

            logger.warning(
                "Vector search error: %s",
                str(e),
            )

        # =============================================
        # 2. FALLBACK RETRIEVAL
        # =============================================

        if not docs:

            logger.info(
                "No semantic match. "
                "Trying fallback retrieval."
            )

            try:

                docs = await asyncio.wait_for(
                    asyncio.to_thread(
                        vectorstore_service.get_all_documents,
                        collection_name,
                        10,
                    ),
                    timeout=VECTOR_TIMEOUT,
                )

            except asyncio.TimeoutError:

                logger.warning(
                    "Fallback retrieval timeout"
                )

                docs = []

            except Exception as e:

                logger.warning(
                    "Fallback retrieval error: %s",
                    str(e),
                )

                docs = []

        # =============================================
        # 3. GENERAL KNOWLEDGE FALLBACK
        # =============================================

        if not docs:

            logger.info(
                "No documents found. "
                "Using general knowledge."
            )

            try:

                answer = await asyncio.wait_for(
                    asyncio.to_thread(
                        llm_service.chat_sync_simple,
                        query,
                    ),
                    timeout=60.0,
                )

                return create_saved_response(
                    db=db,
                    session_id=session_id,
                    query=query,
                    answer=answer,
                    critique_score=6.0,
                    loop_count=0,
                )

            except asyncio.TimeoutError:

                answer = (
                    "⚠️ Request timed out. "
                    "Ollama might be loading. "
                    "Please try again."
                )

                return create_saved_response(
                    db=db,
                    session_id=session_id,
                    query=query,
                    answer=answer,
                    critique_score=2.0,
                    loop_count=0,
                )

            except Exception as e:

                logger.error(
                    "General knowledge fallback error: %s",
                    str(e),
                )

                answer = (
                    "⚠️ Service temporarily unavailable. "
                    "Please check if Ollama is running."
                )

                return create_saved_response(
                    db=db,
                    session_id=session_id,
                    query=query,
                    answer=answer,
                    critique_score=2.0,
                    loop_count=0,
                )

        # =============================================
        # 4. BUILD DOCUMENT CONTEXT
        # =============================================

        context_parts = []

        if is_vague:

            max_docs = 3
            max_chars = 300

            system_prompt = (
                "You are a document analysis assistant.\n\n"
                "The user wants to know more about the "
                "uploaded documents.\n\n"
                "Provide a brief, well-organized summary "
                "using the provided context.\n\n"
                "Keep it concise in 2-3 paragraphs."
            )

        else:

            max_docs = 3
            max_chars = 600

            system_prompt = (
                "You are a document analysis assistant.\n\n"
                "Answer based ONLY on the provided context.\n\n"
                "If the answer is not in the context, say: "
                "'I cannot find this information in the "
                "documents.'\n\n"
                "Be concise."
            )

        for i, doc in enumerate(
            docs[:max_docs]
        ):

            if not isinstance(
                doc,
                dict,
            ):
                continue

            content = doc.get(
                "content",
                "",
            )

            metadata = doc.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            source = metadata.get(
                "source",
                f"doc_{i + 1}",
            )

            if content:

                context_parts.append(
                    f"[{source}]: "
                    f"{str(content)[:max_chars]}"
                )

        context = "\n\n".join(
            context_parts
        )

        logger.info(
            "Context built | chars=%s | docs=%s",
            len(context),
            len(context_parts),
        )

        user_prompt = (
            f"Context:\n\n"
            f"{context}\n\n"
            f"Question:\n\n"
            f"{query}\n\n"
            f"Answer:"
        )

        # =============================================
        # 5. GENERATE ANSWER
        # =============================================

        try:

            answer = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_service.chat_sync,
                    system_prompt,
                    user_prompt,
                ),
                timeout=LLM_TIMEOUT,
            )

            answer = (
                answer
                if answer is not None
                else ""
            )

            # Ollama failure fallback
            if (
                "⚠️ Ollama couldn't"
                in answer
            ):

                logger.warning(
                    "Ollama failed. "
                    "Trying simple chat fallback."
                )

                answer = await asyncio.wait_for(
                    asyncio.to_thread(
                        llm_service.chat_sync_simple,
                        query,
                    ),
                    timeout=60.0,
                )

                critique_score = 5.0

            # Short answer fallback
            elif (
                not answer.strip()
                or len(answer.strip()) < 10
            ):

                logger.warning(
                    "Answer too short. "
                    "Trying simple chat fallback."
                )

                answer = await asyncio.wait_for(
                    asyncio.to_thread(
                        llm_service.chat_sync_simple,
                        query,
                    ),
                    timeout=60.0,
                )

                critique_score = 5.0

            else:

                critique_score = 8.0

            return create_saved_response(
                db=db,
                session_id=session_id,
                query=query,
                answer=answer,
                critique_score=critique_score,
                loop_count=0,
            )

        # =============================================
        # GENERATION TIMEOUT
        # =============================================

        except asyncio.TimeoutError:

            logger.error(
                "Generation timeout after %s seconds",
                LLM_TIMEOUT,
            )

            answer = (
                f"⚠️ Generation timed out after "
                f"{LLM_TIMEOUT} seconds.\n\n"
                "Local Ollama models can be slow. "
                "Try:\n"
                "1. `ollama run phi3` to keep "
                "the model loaded\n"
                "2. Use `phi3:mini` for faster "
                "responses\n"
                "3. Ask a shorter or more "
                "specific question"
            )

            return create_saved_response(
                db=db,
                session_id=session_id,
                query=query,
                answer=answer,
                critique_score=2.0,
                loop_count=0,
            )

        except Exception as e:

            logger.error(
                "Generation error: %s",
                str(e),
            )

            try:

                answer = await asyncio.wait_for(
                    asyncio.to_thread(
                        llm_service.chat_sync_simple,
                        query,
                    ),
                    timeout=60.0,
                )

                return create_saved_response(
                    db=db,
                    session_id=session_id,
                    query=query,
                    answer=answer,
                    critique_score=5.0,
                    loop_count=0,
                )

            except Exception as fallback_error:

                logger.error(
                    "Generation fallback error: %s",
                    str(fallback_error),
                )

                answer = (
                    "⚠️ Service temporarily unavailable. "
                    "Please check if Ollama is running."
                )

                return create_saved_response(
                    db=db,
                    session_id=session_id,
                    query=query,
                    answer=answer,
                    critique_score=2.0,
                    loop_count=0,
                )

    # =============================================
    # UNEXPECTED ERROR FALLBACK
    # =============================================

    except Exception as e:

        logger.error(
            "Unexpected chat error: %s",
            str(e),
        )

        try:

            answer = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_service.chat_sync_simple,
                    query,
                ),
                timeout=60.0,
            )

            return create_saved_response(
                db=db,
                session_id=session_id,
                query=query,
                answer=answer,
                critique_score=5.0,
                loop_count=0,
            )

        except Exception as fallback_error:

            logger.error(
                "Final fallback error: %s",
                str(fallback_error),
            )

            answer = (
                "⚠️ Service temporarily unavailable. "
                "Please check if Ollama is running."
            )

            return create_saved_response(
                db=db,
                session_id=session_id,
                query=query,
                answer=answer,
                critique_score=2.0,
                loop_count=0,
            )


# =========================================================
# HUMAN APPROVAL
# =========================================================

@router.post("/approve")
async def human_approve(
    request: HumanApprovalRequest,
):
    """
    Resume graph execution with
    human approval or rejection.
    """

    from langgraph.types import Command

    config = {
        "configurable": {
            "thread_id": request.session_id,
        }
    }

    try:

        await graph_app.ainvoke(
            Command(
                resume={
                    "decision": request.decision,
                    "feedback": (
                        request.feedback
                        or ""
                    ),
                }
            ),
            config,
        )

        final_state = (
            await graph_app.aget_state(
                config
            )
        )

        values = (
            final_state.values
            if hasattr(
                final_state,
                "values",
            )
            else {}
        )

        generation = values.get(
            "generation",
            "",
        )

        critique_score = values.get(
            "critique_score"
        )

        if request.decision == "approved":

            return {
                "session_id": (
                    request.session_id
                ),
                "decision": "approved",
                "final_answer": generation,
                "critique_score": critique_score,
                "message": (
                    "Answer approved and delivered."
                ),
            }

        return {
            "session_id": request.session_id,
            "decision": "rejected",
            "message": (
                "Answer rejected. "
                "Graph will retry with feedback."
            ),
        }

    except Exception as e:

        logger.error(
            "Human approval error: %s",
            str(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# SESSION STATUS
# =========================================================

@router.get("/session/{session_id}")
async def get_session_status(
    session_id: str,
):
    """
    Get current LangGraph state
    of a session.
    """

    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }

    try:

        state = await graph_app.aget_state(
            config
        )

        values = (
            state.values
            if hasattr(
                state,
                "values",
            )
            else {}
        )

        next_nodes = (
            state.next
            if hasattr(
                state,
                "next",
            )
            else []
        )

        return {
            "session_id": session_id,
            "current_state": {
                "query": values.get(
                    "query"
                ),
                "generation": values.get(
                    "generation"
                ),
                "rewritten_query": values.get(
                    "rewritten_query"
                ),
                "current_node": (
                    next_nodes[0]
                    if next_nodes
                    else "completed"
                ),
                "next_nodes": list(
                    next_nodes
                ),
                "loop_count": values.get(
                    "loop_count",
                    0,
                ),
                "critique_score": values.get(
                    "critique_score"
                ),
                "critique_feedback": values.get(
                    "critique_feedback"
                ),
                "human_approved": values.get(
                    "human_approved"
                ),
                "documents_count": len(
                    values.get(
                        "documents",
                        [],
                    )
                    or []
                ),
            },
        }

    except Exception as e:

        logger.error(
            "Session status error: %s",
            str(e),
        )

        raise HTTPException(
            status_code=404,
            detail=(
                "Session not found: "
                f"{str(e)}"
            ),
        )


# =========================================================
# LLM HEALTH
# =========================================================

@router.get("/health/llm")
async def health_check_llm():
    """Check whether Ollama is running."""

    return llm_service.health_check()