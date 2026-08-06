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


def _safe_state(state):
    """Ensure state is dict — handles tuple/list from LangGraph."""
    if isinstance(state, dict):
        return state
    if isinstance(state, (list, tuple)) and len(state) > 0:
        if isinstance(state[0], dict):
            return state[0]
    return {}


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
        st.session_state.debug_log = []


def _log_debug(msg):
    """Add debug message."""
    if "debug_log" not in st.session_state:
        st.session_state.debug_log = []
    st.session_state.debug_log.append(str(msg))
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

    # Debug logs (hidden expander for troubleshooting)
    if st.session_state.get("debug_log"):
        with st.expander("🐛 Debug Logs", expanded=False):
            for log in st.session_state.debug_log[-10:]:
                st.text(log)


def _process_streaming_query():
    """Process stream — show answer even on backend error."""
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

    status = st.empty()
    status.info("🔄 Connecting to agents...")

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
        line_count = 0
        stream_error = None

        for line in response.iter_lines():
            line_count += 1
            if not line:
                continue

            try:
                line_text = line.decode("utf-8", errors="ignore")
            except Exception as e:
                continue

            if not line_text.startswith("data: "):
                continue

            try:
                raw_data = json.loads(line_text[6:])
            except Exception:
                continue

            # ✅ DEFENSIVE: raw_data might be tuple after backend fixes
            if isinstance(raw_data, (list, tuple)) and len(raw_data) > 0:
                if isinstance(raw_data[0], dict):
                    raw_data = raw_data[0]
                else:
                    continue
            elif not isinstance(raw_data, dict):
                continue

            msg_type = _safe_get(raw_data, "type")

            # NODE UPDATE
            if msg_type == "node_update":
                try:
                    node = str(_safe_get(raw_data, "node", "unknown"))
                    msg_text = str(_safe_get(raw_data, "message", ""))

                    if node != last_node:
                        last_node = node
                        status.info(f"🔄 **{node.title()}** is working...")

                    add_agent_log(node, "completed", msg_text)

                    # Extract node data safely — might be tuple
                    node_data = _safe_get(raw_data, "data", {})
                    node_data = _safe_state(node_data)  # Handle tuple

                    # CRITIC
                    if node == "critic":
                        score = node_data.get("critique_score")
                        feedback = str(node_data.get("critique_feedback", ""))
                        if score is not None:
                            try:
                                st.session_state.pending_score = float(score)
                                st.session_state.pending_feedback = feedback
                                status.info(f"🛡️ **Critic Score: {score}/10**")
                            except Exception as e:
                                _log_debug(f"Score parse: {e}")

                    # SYNTHESIZER
                    if node == "synthesizer":
                        generation = node_data.get("generation")
                        if generation:
                            try:
                                gen_text = str(generation)
                                st.session_state.pending_answer = gen_text
                                status.info(f"📝 **Answer ready** ({len(gen_text)} chars)")
                            except Exception as e:
                                _log_debug(f"Gen parse: {e}")

                    # HUMAN GATE
                    if node == "human_gate":
                        human_gate_triggered = True
                        st.session_state.human_gate_active = True
                        st.session_state.processing = False
                        status.info("🛑 **Human approval required**")
                        st.rerun()
                        return

                except Exception as e:
                    _log_debug(f"Node error: {e}")
                    continue

            elif msg_type == "complete":
                status.success("✅ Agents finished")

            elif msg_type == "error":
                err_msg = str(_safe_get(raw_data, "message", "Unknown error"))
                stream_error = err_msg
                _log_debug(f"Stream error: {err_msg}")
                # Don't return immediately — try to show pending answer
                break

        # After stream — show answer if we have one, even on error
        if not human_gate_triggered:
            if stream_error and st.session_state.get("pending_answer"):
                # Backend errored but we have a synthesized answer!
                _show_answer_with_note(stream_error)
            else:
                _finalize_after_stream(status)

    except Exception as e:
        _try_show_pending_answer(f"Connection error: {str(e)}")


def _finalize_after_stream(status_placeholder):
    """Get final answer from backend."""
    try:
        status_placeholder.info("📡 Finalizing...")

        session_id = str(st.session_state.get("session_id", "default"))
        raw_status = get_session_status(session_id)

        # ✅ ULTRA-DEFENSIVE
        status_data = _safe_state(raw_status)
        state = _safe_state(status_data.get("current_state", {}))

        generation = state.get("generation")
        if not generation:
            generation = st.session_state.get("pending_answer", "")

        human_approved = state.get("human_approved")
        critique_score = state.get("critique_score") or st.session_state.get("pending_score")
        critique_feedback = state.get("critique_feedback", "") or st.session_state.get("pending_feedback", "")

        if critique_score is not None:
            try:
                status_placeholder.success(f"🛡️ Critic Score: {critique_score}/10")
            except Exception:
                pass

        # Show human gate
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
        _try_show_pending_answer(f"Finalize error: {str(e)}")


def _try_show_pending_answer(error_msg):
    """Show pending answer if available, otherwise show error."""
    pending = st.session_state.get("pending_answer", "")
    
    if pending and len(pending) > 10:
        score = st.session_state.get("pending_score")
        msg = pending
        if score is not None:
            msg += f"\n\n---\n🛡️ **Critic Score: {score}/10**"
        if error_msg:
            msg += f"\n\n⚠️ *Note: {error_msg}*"
        _add_assistant_message(msg)
    else:
        if error_msg:
            _add_assistant_message(f"❌ {error_msg}")
        else:
            _add_assistant_message("⚠️ No answer generated. Try uploading documents first.")


def _show_answer_with_note(note):
    """Show the synthesized answer with an error note."""
    pending = st.session_state.get("pending_answer", "")
    score = st.session_state.get("pending_score")
    
    msg = pending
    if score is not None:
        msg += f"\n\n---\n🛡️ **Critic Score: {score}/10**"
    msg += f"\n\n⚠️ *Backend note: {note}*"
    
    _add_assistant_message(msg)


def _add_assistant_message(content):
    """Safely add assistant message and stop processing."""
    try:
        st.session_state.messages.append({
            "role": "assistant",
            "content": str(content),
            "sources": [],
        })
    except Exception as e:
        st.session_state.messages = st.session_state.messages or []
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"System error: {str(e)}",
        })
    
    st.session_state.processing = False
    st.rerun()