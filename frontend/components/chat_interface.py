"""Kimi-style smooth chat interface with robust error handling."""

import json

import streamlit as st

from frontend.components.agent_tracker import add_agent_log, clear_agent_logs
from frontend.components.human_gate_ui import render_human_gate
from frontend.utils.api_client import create_session, get_session_status, send_chat_stream


def _safe_get(data, key, default=None):
    """Safely get value from dict, handles non-dict gracefully."""
    if isinstance(data, dict):
        return data.get(key, default)
    return default


def init_chat_session():
    """Initialize chat session state."""
    if "session_id" not in st.session_state:
        try:
            session = create_session()
            # Ensure session is dict
            if isinstance(session, dict):
                st.session_state.session_id = session.get("session_id", "default")
            else:
                st.session_state.session_id = "default"
        except Exception:
            st.session_state.session_id = "default"
        
        st.session_state.messages = []
        st.session_state.processing = False
        st.session_state.human_gate_active = False
        st.session_state.human_gate_resolved = False
        st.session_state.pending_answer = ""
        st.session_state.pending_score = 0
        st.session_state.pending_feedback = ""
        st.session_state.agent_logs = []


def render_chat_input():
    """ROOT LEVEL chat input."""
    init_chat_session()

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
            st.session_state.pending_answer = ""
            st.session_state.pending_score = 0
            st.session_state.pending_feedback = ""
            clear_agent_logs()
            st.rerun()


def render_chat_interface():
    """Render chat history, processing, and human gate."""
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
            _process_streaming_query()

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


def _process_streaming_query():
    """Process streaming chat with full error handling."""
    if not st.session_state.messages:
        _finish_processing("⚠️ No messages to process.")
        return

    last_message = st.session_state.messages[-1]
    if last_message.get("role") != "user":
        _finish_processing("⚠️ Last message is not from user.")
        return

    query = last_message.get("content", "")
    if not query:
        _finish_processing("⚠️ Empty query.")
        return

    # Status indicator
    status_placeholder = st.empty()
    status_placeholder.info("🔄 Agents are working...")

    # Live answer building
    answer_placeholder = st.empty()
    live_answer = ""

    try:
        response = send_chat_stream(
            query=query,
            session_id=st.session_state.session_id,
        )

        if response.status_code != 200:
            _finish_processing(f"❌ Backend error: {response.status_code}")
            return

        human_gate_triggered = False
        last_node = ""

        for line in response.iter_lines():
            if not line:
                continue

            try:
                line_decoded = line.decode("utf-8")
            except Exception:
                continue

            if not line_decoded.startswith("data: "):
                continue

            try:
                data = json.loads(line_decoded[6:])
            except json.JSONDecodeError:
                continue

            # Ensure data is dict
            if not isinstance(data, dict):
                continue

            msg_type = _safe_get(data, "type")

            # ============================================
            # NODE UPDATE — Show each agent step
            # ============================================
            if msg_type == "node_update":
                node = _safe_get(data, "node", "")
                msg = _safe_get(data, "message", "")
                
                if node and node != last_node:
                    last_node = node
                    status_placeholder.info(f"🔄 **{node.title()}** is working...")

                add_agent_log(node, "completed", msg)

                node_data = _safe_get(data, "data", {})
                # Ensure node_data is dict
                if not isinstance(node_data, dict):
                    node_data = {}

                # CRITIC — Capture score & feedback
                if node == "critic":
                    score = node_data.get("critique_score")
                    feedback = node_data.get("critique_feedback", "")
                    
                    if score is not None:
                        st.session_state.pending_score = score
                        st.session_state.pending_feedback = feedback
                        status_placeholder.info(f"🛡️ **Critic Score: {score}/10**")

                # SYNTHESIZER — Capture answer preview
                if node == "synthesizer":
                    generation = node_data.get("generation")
                    if generation:
                        st.session_state.pending_answer = generation
                        live_answer = generation
                        answer_placeholder.markdown(f"📝 *Draft: {live_answer[:200]}...*")

                # HUMAN GATE — Trigger approval
                if node == "human_gate":
                    human_gate_triggered = True
                    st.session_state.human_gate_active = True
                    st.session_state.processing = False
                    status_placeholder.info("🛑 **Human approval required**")
                    st.rerun()
                    return

            # ============================================
            # STREAM COMPLETE
            # ============================================
            elif msg_type == "complete":
                status_placeholder.success("✅ Complete")

            # ============================================
            # STREAM ERROR
            # ============================================
            elif msg_type == "error":
                err_msg = _safe_get(data, "message", "Unknown streaming error")
                _finish_processing(f"❌ Error: {err_msg}")
                return

        # ============================================
        # AFTER STREAM ENDS
        # ============================================
        if not human_gate_triggered:
            # Get final state from backend
            try:
                status_data = get_session_status(st.session_state.session_id)
                
                # status_data is guaranteed dict by api_client
                state = status_data.get("current_state", {})
                if not isinstance(state, dict):
                    state = {}

                generation = state.get("generation") or st.session_state.get("pending_answer")
                human_approved = state.get("human_approved")
                critique_score = state.get("critique_score") or st.session_state.get("pending_score")
                critique_feedback = state.get("critique_feedback", "") or st.session_state.get("pending_feedback", "")

                # Show critic badge if available
                if critique_score is not None:
                    status_placeholder.success(f"🛡️ Critic Score: {critique_score}/10")

                # HUMAN GATE LOGIC: Show gate if score exists (any score, or >= 5)
                # Backend decides when to show gate, but we handle gracefully
                if generation and human_approved is None:
                    # Show human gate for all scores (let user decide)
                    st.session_state.pending_answer = generation
                    st.session_state.pending_score = critique_score or 0
                    st.session_state.pending_feedback = critique_feedback
                    st.session_state.human_gate_active = True
                    st.session_state.processing = False
                    status_placeholder.info("🛑 Review the answer before finalizing...")
                    st.rerun()
                    return

                # DIRECT ANSWER (already approved or no gate needed)
                if generation:
                    answer_placeholder.empty()
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": generation,
                        "sources": [],
                    })
                    st.session_state.processing = False
                else:
                    _finish_processing("⚠️ No answer was generated. Try uploading documents first.")

            except Exception as e:
                _finish_processing(f"❌ Failed to finalize: {str(e)}")

    except Exception as e:
        _finish_processing(f"❌ Connection error: {str(e)}")


def _finish_processing(message):
    """Helper to end processing and show message."""
    st.session_state.messages.append({
        "role": "assistant",
        "content": message,
        "sources": [],
    })
    st.session_state.processing = False
    st.rerun()