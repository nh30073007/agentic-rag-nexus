"""
Reusable NEXUS chat UI helpers.

The main Streamlit application logic lives in:
    frontend/app.py

This module intentionally does not contain a second chat-processing
pipeline, file uploader, or st.spinner().
"""

import html
import streamlit as st


def init_state():
    """Initialize shared NEXUS session state."""

    defaults = {
        "messages": [],
        "processing": False,
        "session_id": "",
        "agent_logs": [],
        "human_gate_active": False,
        "human_gate_resolved": False,
        "pending_answer": "",
        "pending_score": 0,
        "pending_feedback": "",
        "last_upload": None,
        "show_state_viz": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


def render_chat_loader(
    text="GENERATING ANSWER..."
):
    """
    Render a lightweight infinite loader.

    No st.spinner().
    No full-screen overlay.
    No blocking visual effect.
    """

    st.markdown(
        f"""
        <div class="nexus-loader-wrap">
            <div class="nexus-loader">

                <span class="nexus-loader-dot"></span>
                <span class="nexus-loader-dot"></span>
                <span class="nexus-loader-dot"></span>

                <span class="nexus-loader-text">
                    {html.escape(text)}
                </span>

            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_loader(
    text="PROCESSING DOCUMENT..."
):
    """
    Render a small upload-specific loader.
    """

    st.markdown(
        f"""
        <div class="nexus-upload-loader">

            <span class="nexus-upload-spinner"></span>

            <span>
                {html.escape(text)}
            </span>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_interface():
    """
    Compatibility wrapper.

    The production UI is handled by frontend/app.py.
    This function only renders the shared state if called.
    """

    init_state()

    st.markdown(
        "### AGENTIC RAG NEXUS"
    )

    st.caption(
        "MULTI-AGENT DOCUMENT INTELLIGENCE"
    )

    if st.session_state.get(
        "processing"
    ):

        render_chat_loader()

    for message in st.session_state.get(
        "messages",
        [],
    ):

        role = message.get(
            "role",
            "assistant",
        )

        content = message.get(
            "content",
            "",
        )

        if role == "user":

            with st.chat_message("user"):
                st.markdown(content)

        elif role == "assistant":

            with st.chat_message("assistant"):

                st.markdown(content)

                score = message.get(
                    "critique_score"
                )

                if score is not None:

                    st.caption(
                        f"QUALITY: {score}/10"
                    )

        else:

            st.caption(content)