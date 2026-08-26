"""Clean agent tracker."""

import streamlit as st


def render_agent_tracker():

    st.markdown(
        """
        <div style="margin-bottom: 1rem;">
            <div style="
                font-size: 1rem;
                font-weight: 600;
                color: var(--nexus-text);
            ">
                🔄 Agent Execution
            </div>

            <div style="
                font-size: 0.8rem;
                color: var(--nexus-muted);
                margin-top: 0.2rem;
            ">
                Real-time pipeline monitoring
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "agent_logs" not in st.session_state:

        st.session_state.agent_logs = []

    container = st.container()

    with container:

        if not st.session_state.agent_logs:

            st.markdown(
                """
                <div style="
                    text-align: center;
                    padding: 3rem 1rem;
                ">
                    <div style="
                        font-size: 2rem;
                        margin-bottom: 0.5rem;
                        opacity: 0.25;
                    ">
                        ⏳
                    </div>

                    <div style="
                        font-size: 0.85rem;
                        color: var(--nexus-muted);
                    ">
                        Waiting for query...
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        for log in st.session_state.agent_logs:

            _render_agent_card(
                log
            )


def _render_agent_card(log):

    status = log.get(
        "status",
        "running"
    )

    agent = log.get(
        "agent",
        "Unknown"
    )

    message = log.get(
        "message",
        ""
    )


    # =====================================================
    # ICONS
    # =====================================================

    icons = {
        "query_analyzer": "🔍",
        "retriever": "📚",
        "synthesizer": "✍️",
        "critic": "🛡️",
        "human_gate": "🛑",

        "ANALYZER": "🔍",
        "RETRIEVER": "📚",
        "SYNTHESIZER": "✍️",
        "CRITIC": "🛡️",
    }

    icon = icons.get(
        agent,
        "⚙️"
    )


    # =====================================================
    # STATUS
    # =====================================================

    status_lower = str(
        status
    ).lower()

    if status_lower in (
        "completed",
        "done",
    ):

        status_color = "#22c55e"

        status_bg = (
            "rgba(34, 197, 94, 0.10)"
        )

        status_text = "Done"

    elif status_lower in (
        "running",
        "active",
    ):

        status_color = "#eab308"

        status_bg = (
            "rgba(234, 179, 8, 0.10)"
        )

        status_text = "Running"

    else:

        status_color = "#ef4444"

        status_bg = (
            "rgba(239, 68, 68, 0.10)"
        )

        status_text = "Wait"


    # =====================================================
    # AGENT NAMES
    # =====================================================

    names = {
        "query_analyzer": "Query Analyst",
        "retriever": "Document Retriever",
        "synthesizer": "Answer Synthesizer",
        "critic": "Quality Critic",
        "human_gate": "Human Review",

        "ANALYZER": "Query Analyst",
        "RETRIEVER": "Document Retriever",
        "SYNTHESIZER": "Answer Synthesizer",
        "CRITIC": "Quality Critic",
    }

    name = names.get(
        agent,
        str(agent)
        .replace("_", " ")
        .title()
    )


    # =====================================================
    # THEME-AWARE AGENT CARD
    # =====================================================

    st.markdown(
        f"""
        <div style="
            background: var(--nexus-secondary-bg);
            border: 1px solid var(--nexus-border);
            border-radius: 12px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.5rem;
            color: var(--nexus-text);
        ">

            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.2rem;
            ">

                <div style="
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">

                    <span style="
                        font-size: 1rem;
                    ">
                        {icon}
                    </span>

                    <span style="
                        font-weight: 600;
                        color: var(--nexus-text);
                        font-size: 0.85rem;
                    ">
                        {name}
                    </span>

                </div>


                <div style="
                    background: {status_bg};
                    color: {status_color};
                    padding: 2px 10px;
                    border-radius: 20px;
                    font-size: 0.7rem;
                    font-weight: 600;
                ">
                    {status_text}
                </div>

            </div>


            <div style="
                font-size: 0.8rem;
                color: var(--nexus-muted);
                margin-left: 1.6rem;
            ">
                {message}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# ADD AGENT LOG
# =========================================================

def add_agent_log(
    agent_name,
    status,
    message=""
):

    if "agent_logs" not in st.session_state:

        st.session_state.agent_logs = []

    for log in st.session_state.agent_logs:

        if log["agent"] == agent_name:

            log["status"] = status

            log["message"] = message

            return

    st.session_state.agent_logs.append(
        {
            "agent": agent_name,
            "status": status,
            "message": message,
        }
    )


# =========================================================
# CLEAR AGENT LOGS
# =========================================================

def clear_agent_logs():

    st.session_state.agent_logs = []