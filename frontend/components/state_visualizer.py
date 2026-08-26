"""State visualizer — LangGraph state tree view."""

import streamlit as st


def render_state_visualizer():
    """Render system state visualization."""
    st.markdown("**SYSTEM STATE TREE**")
    st.divider()
    
    # Session info
    st.write(f"SESSION ID: {st.session_state.get('session_id', 'NONE')}")
    st.write(f"PROCESSING: {st.session_state.get('processing', False)}")
    st.write(f"HUMAN GATE: {st.session_state.get('human_gate_active', False)}")
    st.write(f"TOTAL MESSAGES: {len(st.session_state.get('messages', []))}")
    
    # Agent logs
    logs = st.session_state.get("agent_logs", [])
    if logs:
        st.divider()
        st.write("AGENT LOGS:")
        for log in logs:
            agent = log.get("agent", "UNKNOWN")
            status = log.get("status", "UNKNOWN")
            msg = log.get("message", "")
            st.text(f"  [{agent}] [{status}] {msg}")
    
    # Pending state
    if st.session_state.get("human_gate_active"):
        st.divider()
        st.write("PENDING REVIEW:")
        st.text(f"  SCORE: {st.session_state.get('pending_score', 0)}/10")
        st.text(f"  ANSWER LENGTH: {len(st.session_state.get('pending_answer', ''))} chars")
    
    # Document cache
    st.divider()
    st.write("DOCUMENT CACHE:")
    try:
        from utils.api_client import get_collection_stats
        stats = get_collection_stats()
        if stats:
            st.text(f"  CHUNKS: {stats.get('document_count', 0)}")
            st.text(f"  COLLECTION: {stats.get('collection_name', 'documents')}")
        else:
            st.text("  NO DATA")
    except Exception:
        st.text("  UNABLE TO FETCH")