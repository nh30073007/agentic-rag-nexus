"""Kimi-style smooth chat interface."""

import json

import streamlit as st

from frontend.components.agent_tracker import add_agent_log, clear_agent_logs
from frontend.components.human_gate_ui import render_human_gate
from frontend.utils.api_client import create_session, get_session_status, send_chat_stream


def _safe_get(data, key, default=None):
    if isinstance(data, dict):
        return data.get(key, default)
    return default


def init_chat_session():
    """Initialize chat session state."""
    if "session_id" not in st.session_state:
        try:
            session = create_session()
            st.session_state.session_id = session.get("session_id", "default")
        except Exception:
            st.session_state.session_id = "default"
        
        st.session_state.messages = []
        st.session_state.processing = False
        st.session_state.human_gate_active = False
        st.session_state.human_gate_resolved = False
        st.session_state.final_answer = None
        st.session_state.pending_answer = ""
        st.session_state.pending_score = 0
        st.session_state.pending_feedback = ""


def render_chat_input():
    """
    ROOT LEVEL chat input.
    MUST be called outside columns/tabs/expander in app.py.
    """
    init_chat_session()

    # Show input only when ready
    if not st.session_state.processing and not st.session_state.human_gate_active:
        query = st.chat_input(
            "Ask a question about your documents...",
            key="chat_input_main",
        )

        if query and query.strip():
            st.session_state.messages.append({
                "role": "user",
                "content": query.strip()
            })
            st.session_state.processing = True
            st.session_state.human_gate_resolved = False
            st.session_state.final_answer = None
            clear_agent_logs()
            st.rerun()


def render_chat_interface():
    """Render chat history, processing, and human gate."""
    init_chat_session()

    st.markdown(
        '<div style="font-size: 1rem; font-weight: 600; color: #e5e5e5; margin-bottom: 1rem;">💬 Chat</div>',
        unsafe_allow_html=True,
    )

    # ✅ Chat history — beautiful rendering
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📚 Sources"):
                    for src in msg["sources"]:
                        st.caption(f"- {src.get('source', 'unknown')}")

    # ✅ Processing state — typing indicator
    if st.session_state.processing:
        with st.chat_message("assistant"):
            with st.status("🤔 Thinking...", expanded=True) as status:
                result = _process_streaming_query()
                if result.get("success"):
                    status.update(label="✅ Done", state="complete", expanded=False)
                else:
                    status.update(label=f"❌ {result.get('error', 'Error')}", state="error")

    # ✅ Human gate
    if st.session_state.human_gate_active and not st.session_state.human_gate_resolved:
        with st.chat_message("assistant"):
            st.info("⏳ Waiting for your approval...")
            render_human_gate(
                session_id=st.session_state.session_id,
                answer_preview=st.session_state.get("pending_answer", ""),
                critique_score=st.session_state.get("pending_score", 0),
                critique_feedback=st.session_state.get("pending_feedback", ""),
            )


def _process_streaming_query():
    """
    Process streaming chat query.
    Returns dict: {"success": bool, "error": str|None}
    """
    if not st.session_state.messages:
        return {"success": False, "error": "No messages"}

    last_message = st.session_state.messages[-1]
    if last_message["role"] != "user":
        return {"success": False, "error": "Last message not from user"}

    query = last_message["content"]
    answer_placeholder = st.empty()
    full_answer = ""

    try:
        response = send_chat_stream(
            query=query,
            session_id=st.session_state.session_id,
        )

        # Check if response is valid
        if response.status_code != 200:
            error_msg = f"Backend error: {response.status_code}"
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ {error_msg}",
                "sources": [],
            })
            st.session_state.processing = False
            return {"success": False, "error": error_msg}

        human_gate_triggered = False

        for line in response.iter_lines():
            if not line:
                continue

            try:
                line = line.decode("utf-8")
            except Exception:
                continue

            if not line.startswith("data: "):
                continue

            try:
                data = json.loads(line[6:])
            except json.JSONDecodeError:
                continue

            msg_type = _safe_get(data, "type")

            # Agent tracker logs
            if msg_type == "node_update":
                node = _safe_get(data, "node", "")
                msg = _safe_get(data, "message", "")
                add_agent_log(node, "completed", msg)

                # Extract critic score
                if node == "critic":
                    node_data = _safe_get(data, "data", {})
                    score = _safe_get(node_data, "critique_score")
                    feedback = _safe_get(node_data, "critique_feedback", "")
                    if score is not None:
                        st.session_state.pending_score = score
                        st.session_state.pending_feedback = feedback

                # Extract synthesizer answer
                if node == "synthesizer":
                    node_data = _safe_get(data, "data", {})
                    generation = _safe_get(node_data, "generation")
                    if generation:
                        st.session_state.pending_answer = generation

                # Human gate triggered
                if node == "human_gate":
                    human_gate_triggered = True
                    st.session_state.human_gate_active = True
                    st.session_state.processing = False

            elif msg_type == "complete":
                pass  # Stream complete

            elif msg_type == "error":
                err_msg = _safe_get(data, "message", "Unknown error")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {err_msg}",
                    "sources": [],
                })
                st.session_state.processing = False
                return {"success": False, "error": err_msg}

        # After stream ends
        if not human_gate_triggered:
            # Check final session status
            try:
                status = get_session_status(st.session_state.session_id)
                state = _safe_get(status, "current_state", {})

                generation = state.get("generation")
                human_approved = state.get("human_approved")
                critique_score = state.get("critique_score")

                # Auto-approve if score >= 7 (optional, or show gate)
                if generation and human_approved is None and critique_score is not None:
                    if critique_score >= 7:
                        st.session_state.pending_answer = generation
                        st.session_state.pending_score = critique_score
                        st.session_state.pending_feedback = state.get("critique_feedback", "")
                        st.session_state.human_gate_active = True
                        st.session_state.processing = False
                        return {"success": True, "error": None}

                # Direct answer (no gate needed)
                if generation:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": generation,
                        "sources": [],
                    })
                    st.session_state.processing = False
                    return {"success": True, "error": None}
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "⚠️ No answer generated. Try uploading documents first.",
                        "sources": [],
                    })
                    st.session_state.processing = False
                    return {"success": False, "error": "No generation"}

            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Failed to get response: {str(e)}",
                    "sources": [],
                })
                st.session_state.processing = False
                return {"success": False, "error": str(e)}

        return {"success": True, "error": None}

    except Exception as e:
        error_msg = str(e)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Connection error: {error_msg}",
            "sources": [],
        })
        st.session_state.processing = False
        return {"success": False, "error": error_msg}