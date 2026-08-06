"""Kimi-style chat — bulletproof against any backend response format."""

import json

import streamlit as st

from frontend.components.agent_tracker import add_agent_log, clear_agent_logs
from frontend.components.human_gate_ui import render_human_gate
from frontend.utils.api_client import create_session, get_session_status, send_chat_stream


def _safe_get(data, key, default=None):
    """Safely get from dict. NEVER crashes."""
    try:
        if isinstance(data, dict):
            return data.get(key, default)
        return default
    except Exception:
        return default


def init_chat_session():
    """Initialize session state safely."""
    if "session_id" not in st.session_state:
        try:
            session = create_session()
            if isinstance(session, dict):
                sid = session.get("session_id", "default")
            else:
                sid = "default"
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
        st.session_state.agent_logs = []
        st.session_state.debug_log = []  # For troubleshooting


def _log_debug(msg):
    """Add debug message (invisible to user, stored in session)."""
    if "debug_log" not in st.session_state:
        st.session_state.debug_log = []
    st.session_state.debug_log.append(str(msg))
    # Keep last 20 only
    st.session_state.debug_log = st.session_state.debug_log[-20:]


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
    """Render chat with full error isolation."""
    init_chat_session()

    st.markdown(
        '<div style="font-size: 1rem; font-weight: 600; color: #e5e5e5; margin-bottom: 1rem;">💬 Chat</div>',
        unsafe_allow_html=True,
    )

    # Show chat history
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

    # Processing state
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
                st.error(f"❌ Human gate error: {str(e)}")
                st.session_state.human_gate_active = False
                st.rerun()


def _process_streaming_query():
    """Process stream with per-line error isolation."""
    if not st.session_state.messages:
        _add_assistant_message("⚠️ No messages found.")
        return

    last_msg = st.session_state.messages[-1]
    if not isinstance(last_msg, dict) or last_msg.get("role") != "user":
        _add_assistant_message("⚠️ Invalid message state.")
        return

    query = str(last_msg.get("content", ""))
    if not query:
        _add_assistant_message("⚠️ Empty question.")
        return

    # Status placeholder
    status = st.empty()
    status.info("🔄 Connecting to agents...")

    try:
        response = send_chat_stream(
            query=query,
            session_id=str(st.session_state.get("session_id", "default")),
        )

        if response.status_code != 200:
            _add_assistant_message(f"❌ Backend error: {response.status_code}")
            return

        human_gate_triggered = False
        last_node = ""
        line_count = 0

        for line in response.iter_lines():
            line_count += 1
            if not line:
                continue

            # Parse line with full isolation
            try:
                line_text = line.decode("utf-8", errors="ignore")
            except Exception as e:
                _log_debug(f"Decode error line {line_count}: {e}")
                continue

            if not line_text.startswith("data: "):
                continue

            # Parse JSON
            try:
                raw_data = json.loads(line_text[6:])
            except Exception as e:
                _log_debug(f"JSON error line {line_count}: {e} | text: {line_text[:100]}")
                continue

            # Ensure dict
            if not isinstance(raw_data, dict):
                _log_debug(f"Non-dict line {line_count}: {type(raw_data)} | {str(raw_data)[:100]}")
                continue

            msg_type = _safe_get(raw_data, "type")

            # ==========================================
            # NODE UPDATE
            # ==========================================
            if msg_type == "node_update":
                try:
                    node = str(_safe_get(raw_data, "node", "unknown"))
                    msg_text = str(_safe_get(raw_data, "message", ""))

                    if node != last_node:
                        last_node = node
                        status.info(f"🔄 **{node.title()}** is working...")

                    add_agent_log(node, "completed", msg_text)

                    # Extract node data safely
                    node_data = _safe_get(raw_data, "data", {})
                    if not isinstance(node_data, dict):
                        node_data = {}

                    # CRITIC
                    if node == "critic":
                        score = node_data.get("critique_score")
                        feedback = str(node_data.get("critique_feedback", ""))
                        if score is not None:
                            try:
                                st.session_state.pending_score = int(score)
                                st.session_state.pending_feedback = feedback
                                status.info(f"🛡️ **Critic Score: {score}/10**")
                            except Exception as e:
                                _log_debug(f"Score parse error: {e}")

                    # SYNTHESIZER
                    if node == "synthesizer":
                        generation = node_data.get("generation")
                        if generation:
                            try:
                                gen_text = str(generation)
                                st.session_state.pending_answer = gen_text
                                status.info(f"📝 **Draft ready** ({len(gen_text)} chars)")
                            except Exception as e:
                                _log_debug(f"Generation parse error: {e}")

                    # HUMAN GATE
                    if node == "human_gate":
                        human_gate_triggered = True
                        st.session_state.human_gate_active = True
                        st.session_state.processing = False
                        status.info("🛑 **Human approval required**")
                        st.rerun()
                        return

                except Exception as e:
                    _log_debug(f"Node update error: {e}")
                    continue

            # ==========================================
            # COMPLETE
            # ==========================================
            elif msg_type == "complete":
                status.success("✅ Agents finished")

            # ==========================================
            # ERROR
            # ==========================================
            elif msg_type == "error":
                err_msg = str(_safe_get(raw_data, "message", "Unknown error"))
                _add_assistant_message(f"❌ Agent error: {err_msg}")
                return

        # ==========================================
        # AFTER STREAM — Get final answer
        # ==========================================
        if not human_gate_triggered:
            _finalize_after_stream(status)

    except Exception as e:
        _add_assistant_message(f"❌ Connection error: {str(e)}")


def _finalize_after_stream(status_placeholder):
    """Get final answer — bulletproof against any backend format."""
    try:
        status_placeholder.info("📡 Finalizing answer...")

        session_id = str(st.session_state.get("session_id", "default"))
        raw_status = get_session_status(session_id)

        # ✅ ULTRA-DEFENSIVE: Handle ANY format backend sends
        if isinstance(raw_status, dict):
            status_data = raw_status
        elif isinstance(raw_status, (list, tuple)) and len(raw_status) > 0:
            # If tuple/list, try first element
            if isinstance(raw_status[0], dict):
                status_data = raw_status[0]
            else:
                status_data = {}
        else:
            status_data = {}

        # Extract state safely
        state = status_data.get("current_state", {}) if isinstance(status_data, dict) else {}
        if not isinstance(state, dict):
            state = {}

        # Get generation
        generation = state.get("generation")
        if not generation:
            generation = st.session_state.get("pending_answer", "")

        human_approved = state.get("human_approved")
        
        critique_score = state.get("critique_score")
        if critique_score is None:
            critique_score = st.session_state.get("pending_score")

        critique_feedback = state.get("critique_feedback", "")
        if not critique_feedback:
            critique_feedback = st.session_state.get("pending_feedback", "")

        # Show score
        if critique_score is not None:
            try:
                status_placeholder.success(f"🛡️ Critic Score: {critique_score}/10")
            except Exception:
                pass

        # Show human gate if answer exists but not approved
        if generation and human_approved is None:
            st.session_state.pending_answer = str(generation)
            st.session_state.pending_score = int(critique_score or 0)
            st.session_state.pending_feedback = str(critique_feedback)
            st.session_state.human_gate_active = True
            st.session_state.processing = False
            status_placeholder.info("🛑 Review the answer before finalizing...")
            st.rerun()
            return

        # Direct answer
        if generation:
            _add_assistant_message(str(generation))
        else:
            _add_assistant_message("⚠️ No answer generated. Try uploading documents first.")

    except Exception as e:
        _add_assistant_message(f"❌ Finalize error: {str(e)}")


def _add_assistant_message(content):
    """Safely add assistant message and stop processing."""
    try:
        st.session_state.messages.append({
            "role": "assistant",
            "content": str(content),
            "sources": [],
        })
    except Exception as e:
        # Absolute fallback
        st.session_state.messages = st.session_state.messages or []
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"System error: {str(e)}",
        })
    
    st.session_state.processing = False
    st.rerun()