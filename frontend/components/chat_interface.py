"""Clean chat interface."""

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
        session = create_session()
        st.session_state.session_id = session.get("session_id", "default")
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
    Render chat input at ROOT LEVEL.
    MUST be called at root level in app.py (NOT inside columns/tabs/expander)
    """
    init_chat_session()

    # Only show input when not processing and no human gate active
    if not st.session_state.processing and not st.session_state.human_gate_active:
        query = st.chat_input("Ask a question about your documents...")

        if query:
            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.processing = True
            st.session_state.human_gate_resolved = False
            st.session_state.final_answer = None
            clear_agent_logs()
            st.rerun()
    return None


def render_chat_interface():
    """Render chat history, processing status, and human gate."""
    init_chat_session()

    st.markdown(
        '<div style="font-size: 1rem; font-weight: 600; color: #e5e5e5; margin-bottom: 1rem;">💬 Chat</div>',
        unsafe_allow_html=True,
    )

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📚 Sources"):
                    for src in msg["sources"]:
                        st.caption(f"- {src.get('source', 'unknown')}")

    # Processing
    if st.session_state.processing:
        with st.chat_message("assistant"):
            process_streaming_query()

    # Human gate
    if st.session_state.human_gate_active and not st.session_state.human_gate_resolved:
        with st.chat_message("assistant"):
            st.info("⏳ Waiting for your approval...")
            render_human_gate(
                session_id=st.session_state.session_id,
                answer_preview=st.session_state.get("pending_answer", ""),
                critique_score=st.session_state.get("pending_score", 0),
                critique_feedback=st.session_state.get("pending_feedback", ""),
            )


def process_streaming_query():
    last_message = st.session_state.messages[-1]
    query = last_message["content"]

    status_placeholder = st.empty()
    answer_placeholder = st.empty()

    status_placeholder.info("🔄 Agents are working...")

    human_gate_triggered = False

    try:
        response = send_chat_stream(query=query, session_id=st.session_state.session_id)

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

            if msg_type == "node_update":
                node = _safe_get(data, "node", "")
                msg = _safe_get(data, "message", "")

                add_agent_log(node, "completed", msg)

                if node == "critic":
                    node_data = _safe_get(data, "data", {})
                    score = _safe_get(node_data, "critique_score")
                    feedback = _safe_get(node_data, "critique_feedback", "")
                    if score is not None:
                        st.session_state.pending_score = score
                        st.session_state.pending_feedback = feedback

                if node == "synthesizer":
                    node_data = _safe_get(data, "data", {})
                    generation = _safe_get(node_data, "generation")
                    if generation:
                        st.session_state.pending_answer = generation

                if node == "human_gate":
                    human_gate_triggered = True
                    st.session_state.human_gate_active = True
                    st.session_state.processing = False

            elif msg_type == "complete":
                status_placeholder.success("✅ Complete")

            elif msg_type == "error":
                err_msg = _safe_get(data, "message", "Unknown error")
                status_placeholder.error(f"❌ Error: {err_msg}")

        # After stream ends
        if not human_gate_triggered:
            status = get_session_status(st.session_state.session_id)
            state = _safe_get(status, "current_state", {})

            generation = state.get("generation")
            human_approved = state.get("human_approved")
            critique_score = state.get("critique_score")

            if generation and human_approved is None and critique_score is not None and critique_score >= 7:
                st.session_state.pending_answer = generation
                st.session_state.pending_score = critique_score
                st.session_state.pending_feedback = state.get("critique_feedback", "")
                st.session_state.human_gate_active = True
                st.session_state.processing = False
                status_placeholder.info("🛑 Human approval required...")
                st.rerun()
                return

            if generation:
                answer_placeholder.markdown(generation)
                if critique_score:
                    status_placeholder.caption(f"🛡️ Critic Score: {critique_score}/10")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": generation,
                    "sources": [],
                })
                st.session_state.processing = False
            else:
                status_placeholder.warning("⚠️ No answer generated")

    except Exception as e:
        status_placeholder.error(f"❌ Error: {str(e)}")
        st.session_state.processing = False