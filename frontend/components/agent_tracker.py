"""Clean agent tracker."""

import streamlit as st


def render_agent_tracker():
    st.markdown("""
        <div style="margin-bottom: 1rem;">
            <div style="font-size: 1rem; font-weight: 600; color: #e5e5e5;">🔄 Agent Execution</div>
            <div style="font-size: 0.8rem; color: #737373; margin-top: 0.2rem;">Real-time pipeline monitoring</div>
        </div>
    """, unsafe_allow_html=True)

    if "agent_logs" not in st.session_state:
        st.session_state.agent_logs = []

    container = st.container()

    with container:
        if not st.session_state.agent_logs:
            st.markdown("""
                <div style="text-align: center; padding: 3rem 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem; opacity: 0.2;">⏳</div>
                    <div style="font-size: 0.85rem; color: #525252;">Waiting for query...</div>
                </div>
            """, unsafe_allow_html=True)

        for log in st.session_state.agent_logs:
            _render_agent_card(log)


def _render_agent_card(log):
    status = log.get("status", "running")
    agent = log.get("agent", "Unknown")
    message = log.get("message", "")

    icons = {
        "query_analyzer": "🔍",
        "retriever": "📚",
        "synthesizer": "✍️",
        "critic": "🛡️",
        "human_gate": "🛑",
    }
    icon = icons.get(agent, "⚙️")

    if status == "completed":
        status_color = "#22c55e"
        status_bg = "rgba(34, 197, 94, 0.1)"
        status_text = "Done"
    elif status == "running":
        status_color = "#eab308"
        status_bg = "rgba(234, 179, 8, 0.1)"
        status_text = "Running"
    else:
        status_color = "#ef4444"
        status_bg = "rgba(239, 68, 68, 0.1)"
        status_text = "Wait"

    names = {
        "query_analyzer": "Query Analyst",
        "retriever": "Document Retriever",
        "synthesizer": "Answer Synthesizer",
        "critic": "Quality Critic",
        "human_gate": "Human Review",
    }
    name = names.get(agent, agent.replace("_", " ").title())

    st.markdown(f"""
        <div style="
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.5rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1rem;">{icon}</span>
                    <span style="font-weight: 600; color: #e5e5e5; font-size: 0.85rem;">{name}</span>
                </div>
                <div style="
                    background: {status_bg};
                    color: {status_color};
                    padding: 2px 10px;
                    border-radius: 20px;
                    font-size: 0.7rem;
                    font-weight: 600;
                ">{status_text}</div>
            </div>
            <div style="font-size: 0.8rem; color: #a3a3a3; margin-left: 1.6rem;">{message}</div>
        </div>
    """, unsafe_allow_html=True)


def add_agent_log(agent_name, status, message=""):
    if "agent_logs" not in st.session_state:
        st.session_state.agent_logs = []

    for log in st.session_state.agent_logs:
        if log["agent"] == agent_name:
            log["status"] = status
            log["message"] = message
            return

    st.session_state.agent_logs.append({
        "agent": agent_name,
        "status": status,
        "message": message,
    })


def clear_agent_logs():
    st.session_state.agent_logs = []