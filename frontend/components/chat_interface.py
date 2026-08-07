"""Kimi-style chat — root-level input, error-free."""

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
            sid = session.get("session_id", "default") if isinstance(session, dict) else "default"
        except Exception:
            sid = "default"
        
        st.session_state.session_id = sid
        st.session_state.messages = []
        st.session_state.processing = False
        st.session_state.human_gate_active = False
        st.session_state.human_gate_resolved = False
        st.session_state.pending_answer = ""
        st.session_state.pending_score = 0
        st.session_state.pending_feedback = ""


def render_chat_input():
    """
    ✅ ROOT LEVEL ONLY — Must be called at root in app.py (NOT inside columns/containers)
    """
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
        '<div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">💬 Chat</div>',
        unsafe_allow_html=True,
    )

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg.get("role", "assistant")):
            st.markdown(str(msg.get("content", "")))
            if msg.get("sources"):
                with st.expander("📚 Sources"):
                    for src in msg.get("sources", []):
                        if isinstance(src, dict):
                            st.caption(f"- {src.get('source', 'unknown')}")
                        else:
                            st.caption(f"- {str(src)}")

    # Processing
    if st.session_state.processing:
        with st.chat_message("assistant"):
            _process_streaming_query()

    # Human gate
    if st.session_state.human_gate_active and not st.session_state.human_gate_resolved:
        with st.chat_message("assistant"):
            st.info("⏳ Waiting for your approval...")
            try:
                render_human_gate(
                    session_id=str(st.session_state.get("session_id", "default")),
                    answer_preview=str(st.session_state.get("pending_answer", "")),
                    critique_score=int(st.session_state.get("pending_score", 0) or 0),
                    critique_feedback=str(st.session_state.get("pending_feedback", "")),
                )
            except Exception as e:
                st.error(f"❌ Gate error: {str(e)}")
                st.session_state.human_gate_active = False
                st.rerun()


def _process_streaming_query():
    """Process stream with bulletproof error handling."""
    if not st.session_state.messages:
        _finish_processing("⚠️ No messages")
        return

    last_msg = st.session_state.messages[-1]
    if not isinstance(last_msg, dict) or last_msg.get("role") != "user":
        _finish_processing("⚠️ Invalid state")
        return

    query = str(last_msg.get("content", ""))
    if not query:
        _finish_processing("⚠️ Empty query")
        return

    status = st.empty()
    status.info("🔄 Agents are working...")

    try:
        response = send_chat_stream(
            query=query,
            session_id=str(st.session_state.get("session_id", "default")),
        )

        if response.status_code != 200:
            _try_show_pending_answer(f"Backend error: {response.status_code}")
            return

        human_gate_triggered = False
        last_node = ""

        for line in response.iter_lines():
            if not line:
                continue

            try:
                line_text = line.decode("utf-8", errors="ignore")
            except Exception:
                continue

            if not line_text.startswith("data: "):
                continue

            try:
                raw_data = json.loads(line_text[6:])
            except Exception:
                continue

            if not isinstance(raw_data, dict):
                continue

            msg_type = _safe_get(raw_data, "type")

            if msg_type == "node_update":
                try:
                    node = str(_safe_get(raw_data, "node", "unknown"))
                    msg_text = str(_safe_get(raw_data, "message", ""))

                    if node != last_node:
                        last_node = node
                        status.info(f"🔄 **{node.title()}** is working...")

                    add_agent_log(node, "completed", msg_text)

                    node_data = _safe_get(raw_data, "data", {})
                    if not isinstance(node_data, dict):
                        node_data = {}

                    if node == "critic":
                        score = node_data.get("critique_score")
                        feedback = str(node_data.get("critique_feedback", ""))
                        if score is not None:
                            try:
                                st.session_state.pending_score = float(score)
                                st.session_state.pending_feedback = feedback
                                status.info(f"🛡️ **Critic Score: {score}/10**")
                            except Exception:
                                pass

                    if node == "synthesizer":
                        generation = node_data.get("generation")
                        if generation:
                            try:
                                gen_text = str(generation)
                                st.session_state.pending_answer = gen_text
                                status.info(f"📝 **Draft ready** ({len(gen_text)} chars)")
                            except Exception:
                                pass

                    if node == "human_gate":
                        human_gate_triggered = True
                        st.session_state.human_gate_active = True
                        st.session_state.processing = False
                        status.info("🛑 **Human approval required**")
                        st.rerun()
                        return

                except Exception:
                    continue

            elif msg_type == "complete":
                status.success("✅ Agents finished")

            elif msg_type == "error":
                err_msg = str(_safe_get(raw_data, "message", "Unknown error"))
                _try_show_pending_answer(f"Agent error: {err_msg}")
                return

        if not human_gate_triggered:
            _try_show_pending_answer(None)

    except Exception as e:
        _try_show_pending_answer(f"Connection error: {str(e)}")


def _try_show_pending_answer(error_msg):
    """Show answer if available, otherwise error."""
    pending = st.session_state.get("pending_answer", "")

    if pending and len(pending) > 10:
        score = st.session_state.get("pending_score")
        msg = pending
        if score is not None:
            msg += f"\n\n---\n🛡️ **Critic Score: {score}/10**"
        if error_msg:
            msg += f"\n\n⚠️ *Note: {error_msg}*"
        _finish_processing(msg)
    else:
        if error_msg:
            _finish_processing(f"❌ {error_msg}")
        else:
            _finish_processing("⚠️ No answer generated. Try uploading documents first.")


def _finish_processing(content):
    """Safely add assistant message and stop processing."""
    try:
        st.session_state.messages.append({
            "role": "assistant",
            "content": str(content),
            "sources": [],
        })
    except Exception:
        pass
    
    st.session_state.processing = False
    st.rerun()