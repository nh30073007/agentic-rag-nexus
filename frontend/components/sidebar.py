"""Sidebar — Persistent Conversation History, New Chat, Theme and Status."""

import uuid
from datetime import datetime

import streamlit as st


# =========================================================
# API IMPORTS
# =========================================================

try:

    from utils.api_client import (
        health_check,
        get_collection_stats,
        get_conversations,
        get_conversation,
        delete_conversation,
    )

except Exception:

    health_check = None
    get_collection_stats = None
    get_conversations = None
    get_conversation = None
    delete_conversation = None


# =========================================================
# THEME
# =========================================================

def get_current_theme():
    """Return current runtime theme."""

    if "theme_mode" not in st.session_state:

        st.session_state.theme_mode = "DARK"

    return st.session_state.theme_mode


def toggle_theme():
    """Instantly switch between DARK and LIGHT."""

    current_theme = get_current_theme()

    if current_theme == "DARK":

        st.session_state.theme_mode = "LIGHT"

    else:

        st.session_state.theme_mode = "DARK"


# =========================================================
# NEW CHAT
# =========================================================

def start_new_chat():
    """Reset UI and create a new conversation."""

    st.session_state.messages = []

    st.session_state.session_id = (
        f"sess_{uuid.uuid4().hex}"
    )

    st.session_state.processing = False

    st.session_state.agent_logs = []

    st.session_state.human_gate_active = False

    st.session_state.human_gate_resolved = False

    st.session_state.pending_answer = ""

    st.session_state.pending_score = 0

    st.session_state.current_conversation_title = (
        "New Chat"
    )

    st.session_state.active_conversation_id = (
        st.session_state.session_id
    )


# =========================================================
# LOAD OLD CONVERSATION
# =========================================================

def load_old_conversation(session_id: str):
    """Load a persistent conversation from backend."""

    if not get_conversation:

        st.error(
            "Conversation API is unavailable."
        )

        return False

    try:

        conversation = get_conversation(
            session_id
        )

        if not conversation:

            st.error(
                "Failed to load conversation."
            )

            return False

        messages = conversation.get(
            "messages",
            [],
        )

        st.session_state.messages = messages

        st.session_state.session_id = (
            conversation.get(
                "session_id",
                session_id,
            )
        )

        st.session_state.active_conversation_id = (
            session_id
        )

        st.session_state.current_conversation_title = (
            conversation.get(
                "title",
                "Conversation",
            )
        )

        st.session_state.processing = False

        st.session_state.agent_logs = []

        st.session_state.human_gate_active = False

        st.session_state.human_gate_resolved = False

        st.session_state.pending_answer = ""

        st.session_state.pending_score = 0

        return True

    except Exception as e:

        st.error(
            f"Failed to load conversation: {e}"
        )

        return False


# =========================================================
# GROUP CONVERSATIONS BY DATE
# =========================================================

def parse_conversation_date(value):
    """Convert backend ISO date to datetime."""

    if not value:

        return None

    try:

        value = value.replace(
            "Z",
            "+00:00",
        )

        return datetime.fromisoformat(
            value
        )

    except Exception:

        return None


def group_conversations(conversations):
    """
    Group conversations like ChatGPT:

    TODAY
    YESTERDAY
    PREVIOUS 7 DAYS
    OLDER
    """

    groups = {
        "TODAY": [],
        "YESTERDAY": [],
        "PREVIOUS 7 DAYS": [],
        "OLDER": [],
    }

    now = datetime.now()

    today = now.date()

    for conversation in conversations:

        date_value = (
            conversation.get("updated_at")
            or conversation.get("created_at")
        )

        conversation_date = (
            parse_conversation_date(
                date_value
            )
        )

        if not conversation_date:

            groups["OLDER"].append(
                conversation
            )

            continue

        if conversation_date.tzinfo:

            conversation_date = (
                conversation_date.replace(
                    tzinfo=None
                )
            )

        days_difference = (
            today
            - conversation_date.date()
        ).days

        if days_difference == 0:

            groups["TODAY"].append(
                conversation
            )

        elif days_difference == 1:

            groups["YESTERDAY"].append(
                conversation
            )

        elif days_difference <= 7:

            groups[
                "PREVIOUS 7 DAYS"
            ].append(
                conversation
            )

        else:

            groups["OLDER"].append(
                conversation
            )

    return groups


# =========================================================
# CONVERSATION BUTTON
# =========================================================

def render_conversation_item(conversation):
    """Render one conversation item."""

    session_id = conversation.get(
        "session_id",
        ""
    )

    title = conversation.get(
        "title",
        "New Conversation",
    )

    active_id = st.session_state.get(
        "active_conversation_id"
    )

    is_active = (
        active_id == session_id
    )

    if len(title) > 42:

        title = (
            title[:42].rstrip()
            + "..."
        )

    button_label = (
        f"💬 {title}"
    )

    if is_active:

        button_label = (
            f"● {title}"
        )

    col1, col2 = st.columns(
        [8, 1]
    )

    with col1:

        if st.button(
            button_label,
            key=f"conversation_{session_id}",
            use_container_width=True,
        ):

            if load_old_conversation(
                session_id
            ):

                st.rerun()

    with col2:

        if st.button(
            "×",
            key=f"delete_{session_id}",
            help="Delete conversation",
        ):

            if delete_conversation:

                deleted = delete_conversation(
                    session_id
                )

                if deleted:

                    if (
                        st.session_state.get(
                            "active_conversation_id"
                        )
                        == session_id
                    ):

                        start_new_chat()

                    st.rerun()

                else:

                    st.error(
                        "Could not delete conversation."
                    )


# =========================================================
# RENDER CONVERSATION HISTORY
# =========================================================

def render_conversation_history():
    """Render persistent history from database."""

    st.markdown(
        "**CONVERSATION HISTORY**"
    )

    if not get_conversations:

        st.caption(
            "HISTORY API UNAVAILABLE"
        )

        return

    try:

        conversations = get_conversations(
            limit=100
        )

    except Exception:

        conversations = []

    if not conversations:

        st.caption(
            "NO CONVERSATIONS YET"
        )

        return

    groups = group_conversations(
        conversations
    )

    for group_name, items in groups.items():

        if not items:

            continue

        st.caption(
            group_name
        )

        for conversation in items:

            render_conversation_item(
                conversation
            )


# =========================================================
# RENDER SIDEBAR
# =========================================================

def render_sidebar():

    with st.sidebar:


        # ================================================
        # BRAND
        # ================================================

        st.title("NEXUS")

        st.caption(
            "AGENTIC RAG SYSTEM"
        )

        st.divider()


        # ================================================
        # INSTANT THEME SWITCH
        # ================================================

        current_theme = get_current_theme()

        if current_theme == "DARK":

            theme_button = (
                "☀ SWITCH TO LIGHT"
            )

        else:

            theme_button = (
                "◐ SWITCH TO DARK"
            )

        if st.button(
            theme_button,
            use_container_width=True,
            key="theme_toggle_btn",
        ):

            toggle_theme()

            # Instantly re-run the app.
            # CSS reads the new theme_mode immediately.
            st.rerun()


        st.divider()


        # ================================================
        # NEW CHAT
        # ================================================

        if st.button(
            "＋ NEW CHAT",
            use_container_width=True,
            key="new_chat_sidebar_btn",
        ):

            start_new_chat()

            st.rerun()


        st.divider()


        # ================================================
        # PERSISTENT CONVERSATION HISTORY
        # ================================================

        render_conversation_history()


        st.divider()


        # ================================================
        # SYSTEM STATUS
        # ================================================

        st.markdown(
            "**SYSTEM STATUS**"
        )


        # Backend health

        backend_ok = False

        try:

            if health_check:

                health = health_check()

                if (
                    health is not None
                    and health.get("status")
                    == "healthy"
                ):

                    backend_ok = True

        except Exception:

            backend_ok = False


        if backend_ok:

            st.success(
                "BACKEND: ONLINE"
            )

        else:

            st.warning(
                "BACKEND: OFFLINE"
            )


        # ================================================
        # VECTORSTORE STATUS
        # ================================================

        try:

            if get_collection_stats:

                stats = get_collection_stats()

            else:

                stats = None

            if stats:

                count = stats.get(
                    "document_count",
                    0,
                )

                st.info(
                    f"VECTORSTORE: "
                    f"{count} CHUNKS"
                )

            else:

                st.caption(
                    "VECTORSTORE: UNKNOWN"
                )

        except Exception:

            st.caption(
                "VECTORSTORE: UNAVAILABLE"
            )


        st.divider()


        # ================================================
        # FOOTER
        # ================================================

        st.caption(
            "LANGGRAPH + OLLAMA + FASTEMBED"
        )