import streamlit as st
import requests
import uuid
import html
import os

from components.sidebar import render_sidebar

try:
    from utils.api_client import (
        chat_ask,
        approve_answer,
    )
except Exception:
    chat_ask = None
    approve_answer = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NEXUS",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME STATE
# ============================================================

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "DARK"


# ============================================================
# THEME CSS
# ============================================================

def apply_theme_css():

    theme = st.session_state.get(
        "theme_mode",
        "DARK",
    )

    if theme == "LIGHT":

        background = "#ffffff"
        secondary_background = "#f5f5f5"
        text = "#111111"
        muted_text = "#666666"
        border = "#dddddd"
        input_background = "#ffffff"
        code_background = "#f4f4f4"
        sidebar_background = "#f7f7f8"
        chat_assistant = "#f7f7f8"
        chat_user = "#ffffff"
        hover_background = "#eeeeee"

    else:

        background = "#000000"
        secondary_background = "#111111"
        text = "#ffffff"
        muted_text = "#a3a3a3"
        border = "#2a2a2a"
        input_background = "#171717"
        code_background = "#111111"
        sidebar_background = "#0d0d0d"
        chat_assistant = "#111111"
        chat_user = "#000000"
        hover_background = "#1c1c1c"

    st.markdown(
        f"""
        <style>

        :root {{
            --nexus-bg: {background};
            --nexus-secondary-bg: {secondary_background};
            --nexus-text: {text};
            --nexus-muted: {muted_text};
            --nexus-border: {border};
            --nexus-input-bg: {input_background};
            --nexus-code-bg: {code_background};
            --nexus-sidebar-bg: {sidebar_background};
            --nexus-chat-assistant: {chat_assistant};
            --nexus-chat-user: {chat_user};
            --nexus-hover-bg: {hover_background};
        }}

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        .stApp {{
            background-color: var(--nexus-bg) !important;
            color: var(--nexus-text) !important;
        }}

        [data-testid="stMain"] {{
            background-color: var(--nexus-bg) !important;
        }}

        [data-testid="stMainBlockContainer"] {{
            background-color: var(--nexus-bg) !important;
        }}

        [data-testid="stAppViewBlockContainer"] {{
            background-color: var(--nexus-bg) !important;
            opacity: 1 !important;
        }}

        h1,
        h2,
        h3,
        h4,
        h5,
        h6,
        p,
        span,
        div,
        label,
        li {{
            color: var(--nexus-text);
        }}

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {{
            color: var(--nexus-muted) !important;
        }}

        [data-testid="stSidebar"] {{
            background-color: var(--nexus-sidebar-bg) !important;
        }}

        [data-testid="stSidebar"] > div {{
            background-color: var(--nexus-sidebar-bg) !important;
        }}

        [data-testid="stSidebarContent"] {{
            background-color: var(--nexus-sidebar-bg) !important;
        }}

        .stButton > button {{
            background-color: var(--nexus-secondary-bg) !important;
            color: var(--nexus-text) !important;
            border: 1px solid var(--nexus-border) !important;
            transition:
                background-color 0.15s ease,
                border-color 0.15s ease !important;
        }}

        .stButton > button:hover {{
            background-color: var(--nexus-hover-bg) !important;
            border-color: var(--nexus-muted) !important;
            color: var(--nexus-text) !important;
        }}

        .stButton > button:focus {{
            color: var(--nexus-text) !important;
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {{
            background-color: var(--nexus-input-bg) !important;
            color: var(--nexus-text) !important;
            border-color: var(--nexus-border) !important;
        }}

        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder {{
            color: var(--nexus-muted) !important;
        }}

        [data-testid="stChatInput"] {{
            background-color: var(--nexus-input-bg) !important;
            border-color: var(--nexus-border) !important;
        }}

        [data-testid="stChatInput"] textarea {{
            background-color: var(--nexus-input-bg) !important;
            color: var(--nexus-text) !important;
        }}

        [data-testid="stChatInput"] textarea::placeholder {{
            color: var(--nexus-muted) !important;
        }}

        [data-testid="stChatInput"] button {{
            color: var(--nexus-text) !important;
        }}

        [data-testid="stFileUploader"] {{
            background-color: var(--nexus-secondary-bg) !important;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            background-color: var(--nexus-secondary-bg) !important;
            border-color: var(--nexus-border) !important;
        }}

        [data-testid="stFileUploaderDropzone"] * {{
            color: var(--nexus-text) !important;
        }}

        [data-testid="stChatMessage"] {{
            background-color: var(--nexus-chat-assistant) !important;
            color: var(--nexus-text) !important;
            transition: none !important;
        }}

        [data-testid="stChatMessageContent"] {{
            color: var(--nexus-text) !important;
        }}

        [data-testid="stChatMessageContent"] * {{
            color: var(--nexus-text);
        }}

        [data-testid="stExpander"] {{
            background-color: var(--nexus-secondary-bg) !important;
            border-color: var(--nexus-border) !important;
        }}

        [data-testid="stExpander"] * {{
            color: var(--nexus-text) !important;
        }}

        pre,
        code,
        [data-testid="stCodeBlock"] {{
            background-color: var(--nexus-code-bg) !important;
            color: var(--nexus-text) !important;
        }}

        [data-testid="stMetric"] {{
            background-color: var(--nexus-secondary-bg) !important;
            border-color: var(--nexus-border) !important;
        }}

        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"] {{
            color: var(--nexus-text) !important;
        }}

        hr {{
            border-color: var(--nexus-border) !important;
        }}

        [data-testid="stCheckbox"] {{
            color: var(--nexus-text) !important;
        }}

        [data-testid="stCheckbox"] label {{
            color: var(--nexus-text) !important;
        }}

        [data-testid="stAlert"] {{
            border-color: var(--nexus-border) !important;
        }}

        #MainMenu {{
            visibility: hidden !important;
        }}

        footer {{
            visibility: hidden !important;
        }}

        [data-testid="stAppViewContainer"]::before {{
            display: none !important;
        }}

        [data-testid="stStatusWidget"] {{
            display: none !important;
        }}

        .nexus-loader-wrap {{
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 18px 0 24px 0;
            color: var(--nexus-text);
        }}

        .nexus-loader {{
            display: flex;
            align-items: center;
            gap: 7px;
        }}

        .nexus-loader-dot {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: currentColor;
            animation: nexus-pulse 1.25s infinite ease-in-out;
        }}

        .nexus-loader-dot:nth-child(1) {{
            animation-delay: 0s;
        }}

        .nexus-loader-dot:nth-child(2) {{
            animation-delay: 0.15s;
        }}

        .nexus-loader-dot:nth-child(3) {{
            animation-delay: 0.30s;
        }}

        .nexus-loader-text {{
            margin-left: 8px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.3px;
            opacity: 0.75;
        }}

        @keyframes nexus-pulse {{
            0%, 70%, 100% {{
                transform: scale(0.65);
                opacity: 0.35;
            }}

            35% {{
                transform: scale(1.0);
                opacity: 1;
            }}
        }}

        .nexus-upload-loader {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 0;
            font-size: 13px;
            font-weight: 600;
            color: var(--nexus-text);
        }}

        .nexus-upload-spinner {{
            width: 16px;
            height: 16px;
            border: 2px solid var(--nexus-border);
            border-top-color: currentColor;
            border-radius: 50%;
            animation: nexus-spin 0.8s linear infinite;
        }}

        @keyframes nexus-spin {{
            to {{
                transform: rotate(360deg);
            }}
        }}

        .nexus-status {{
            text-align: center;
            font-size: 12px;
            color: var(--nexus-muted);
            padding: 5px 0 10px 0;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


apply_theme_css()


# ============================================================
# API CONFIG
# ============================================================

# IMPORTANT:
# Streamlit Cloud cannot use localhost to reach your Render backend.
#
# Optional environment variable:
# BACKEND_URL=https://agentic-rag-nexus.onrender.com
#
# If BACKEND_URL is not configured, production Render URL is used.

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://agentic-rag-nexus.onrender.com",
).rstrip("/")

API_BASE = f"{BACKEND_URL}/api/v1"


# ============================================================
# API HELPERS
# ============================================================

def api_post(
    endpoint,
    json_data=None,
    files=None,
    data=None,
    timeout=130,
):
    """POST request helper."""

    url = f"{API_BASE}{endpoint}"

    try:

        if files is not None:

            return requests.post(
                url,
                files=files,
                data=data,
                timeout=timeout,
            )

        return requests.post(
            url,
            json=json_data,
            timeout=timeout,
        )

    except requests.exceptions.Timeout:

        return None

    except requests.exceptions.RequestException:

        return None

    except Exception:

        return None


def api_get(
    endpoint,
    timeout=10,
):
    """GET request helper."""

    url = f"{API_BASE}{endpoint}"

    try:

        return requests.get(
            url,
            timeout=timeout,
        )

    except Exception:

        return None


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "messages": [],
    "processing": False,
    "session_id": f"sess_{uuid.uuid4().hex}",
    "active_conversation_id": None,
    "current_conversation_title": "New Chat",
    "last_upload": None,
    "doc_count": 0,
    "agent_logs": [],
    "human_gate_active": False,
    "human_gate_resolved": False,
    "pending_answer": "",
    "pending_score": 0,
    "pending_feedback": "",
}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


if st.session_state.active_conversation_id is None:

    st.session_state.active_conversation_id = (
        st.session_state.session_id
    )


# ============================================================
# CUSTOM LOADERS
# ============================================================

def render_chat_loader(
    text="GENERATING ANSWER...",
):

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
    text="PROCESSING DOCUMENT...",
):

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


# ============================================================
# SIDEBAR
# ============================================================

try:

    render_sidebar()

except Exception as e:

    with st.sidebar:

        st.error(
            f"SIDEBAR ERROR: {e}"
        )

        st.title("NEXUS")


# ============================================================
# HEADER
# ============================================================

st.header(
    "AGENTIC RAG NEXUS"
)

st.caption(
    "MULTI-AGENT DOCUMENT INTELLIGENCE"
)

st.divider()


# ============================================================
# AGENT PIPELINE
# ============================================================

if (
    st.session_state.processing
    or st.session_state.get("agent_logs")
):

    st.subheader(
        "AGENT PIPELINE"
    )

    cols = st.columns(4)

    agents = [
        ("ANALYZER", "WAIT"),
        ("RETRIEVER", "WAIT"),
        ("SYNTHESIZER", "WAIT"),
        ("CRITIC", "WAIT"),
    ]

    for log in st.session_state.get(
        "agent_logs",
        [],
    ):

        log_agent = (
            log.get(
                "agent",
                "",
            )
            .upper()
        )

        for i, (
            name,
            _,
        ) in enumerate(agents):

            if log_agent == name:

                agents[i] = (
                    name,
                    log.get(
                        "status",
                        "WAIT",
                    ).upper(),
                )

    for col, (
        name,
        status,
    ) in zip(
        cols,
        agents,
    ):

        col.metric(
            name,
            status,
        )

    st.divider()


# ============================================================
# HUMAN QUALITY GATE
# ============================================================

if st.session_state.get(
    "human_gate_active"
):

    st.subheader(
        "QUALITY REVIEW GATE"
    )

    score = st.session_state.get(
        "pending_score",
        0,
    )

    answer = st.session_state.get(
        "pending_answer",
        "",
    )

    c1, c2 = st.columns(2)

    c1.metric(
        "SCORE",
        f"{score}/10",
    )

    if score >= 8:

        quality = "EXCELLENT"

    elif score >= 6:

        quality = "ACCEPTABLE"

    else:

        quality = "NEEDS WORK"

    c2.metric(
        "STATUS",
        quality,
    )

    with st.expander(
        "REVIEW ANSWER",
        expanded=True,
    ):

        st.write(answer)

    feedback = st.text_area(
        "YOUR FEEDBACK",
        key="gate_fb",
    )

    b1, b2 = st.columns(2)


    # --------------------------------------------------------
    # APPROVE
    # --------------------------------------------------------

    with b1:

        if st.button(
            "APPROVE",
            use_container_width=True,
            key="approve_answer_btn",
        ):

            final_answer = answer

            try:

                if approve_answer:

                    result = approve_answer(
                        session_id=(
                            st.session_state.session_id
                        ),
                        decision="approved",
                        feedback=feedback,
                    )

                    if result:

                        final_answer = result.get(
                            "final_answer",
                            answer,
                        )

                else:

                    result = api_post(
                        "/chat/approve",
                        json_data={
                            "session_id": (
                                st.session_state.session_id
                            ),
                            "decision": "approved",
                            "feedback": feedback,
                        },
                    )

                    if (
                        result is not None
                        and result.status_code == 200
                    ):

                        try:

                            final_answer = (
                                result.json().get(
                                    "final_answer",
                                    answer,
                                )
                            )

                        except Exception:

                            final_answer = answer

            except Exception:

                final_answer = answer

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": final_answer,
                    "critique_score": score,
                }
            )

            st.session_state.human_gate_active = False

            st.session_state.human_gate_resolved = True

            st.session_state.processing = False

            st.rerun()


    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

    with b2:

        if st.button(
            "REJECT",
            use_container_width=True,
            key="reject_answer_btn",
        ):

            if not feedback.strip():

                st.warning(
                    "FEEDBACK REQUIRED"
                )

            else:

                try:

                    if approve_answer:

                        approve_answer(
                            session_id=(
                                st.session_state.session_id
                            ),
                            decision="rejected",
                            feedback=feedback,
                        )

                    else:

                        api_post(
                            "/chat/approve",
                            json_data={
                                "session_id": (
                                    st.session_state.session_id
                                ),
                                "decision": "rejected",
                                "feedback": feedback,
                            },
                        )

                except Exception:

                    pass

                st.session_state.human_gate_active = False

                st.session_state.human_gate_resolved = False

                st.session_state.processing = True

                st.rerun()

    st.divider()


# ============================================================
# CHAT HISTORY
# ============================================================

chat_box = st.container()

with chat_box:

    for msg in st.session_state.messages:

        role = msg.get(
            "role",
            "",
        )

        content = msg.get(
            "content",
            "",
        )

        if role == "user":

            with st.chat_message("user"):

                st.markdown(content)

        elif role == "assistant":

            with st.chat_message("assistant"):

                st.markdown(content)

                score = msg.get(
                    "critique_score"
                )

                if score is not None:

                    st.caption(
                        f"QUALITY: {score}/10"
                    )

                sources = msg.get(
                    "sources",
                    [],
                )

                if sources:

                    source_text = ", ".join(
                        str(x)
                        for x in sources[:3]
                    )

                    st.caption(
                        f"SOURCES: {source_text}"
                    )

        else:

            st.caption(content)


# ============================================================
# CHAT GENERATION LOADER
# ============================================================

if st.session_state.processing:

    render_chat_loader(
        "GENERATING ANSWER..."
    )


# ============================================================
# EMPTY STATE
# ============================================================

if (
    not st.session_state.messages
    and not st.session_state.processing
    and not st.session_state.get(
        "human_gate_active"
    )
):

    st.code(
        """NEXUS CHAT INTERFACE v3.0
-------------------------
UPLOAD A DOCUMENT BELOW AND ASK QUESTIONS.
USE 'CLEAR ALL DOCS' BEFORE UPLOADING NEW FILE."""
    )


# ============================================================
# FILE UPLOAD
# ============================================================

st.subheader(
    "ATTACH FILE"
)

replace_old = st.checkbox(
    "REPLACE OLD DOCUMENTS (RECOMMENDED)",
    value=True,
    key="replace_check",
)

uploaded = st.file_uploader(
    "PDF, DOCX, TXT, MD",
    type=[
        "pdf",
        "docx",
        "txt",
        "md",
    ],
    label_visibility="collapsed",
)


# ============================================================
# FILE PROCESSING
# ============================================================

if (
    uploaded is not None
    and st.session_state.last_upload
    != uploaded.name
):

    upload_placeholder = st.empty()

    upload_placeholder.markdown(
        """
        <div class="nexus-upload-loader">

            <span class="nexus-upload-spinner"></span>

            <span>
                PROCESSING DOCUMENT...
            </span>

        </div>
        """,
        unsafe_allow_html=True,
    )

    try:

        # ----------------------------------------------------
        # CLEAR OLD DOCUMENTS
        # ----------------------------------------------------

        if replace_old:

            clear_response = api_post(
                "/upload/clear",
                json_data={
                    "collection_name": "documents",
                },
                timeout=20,
            )

            if clear_response is None:

                upload_placeholder.empty()

                st.error(
                    "FAILED TO CONNECT TO BACKEND WHILE CLEARING DOCUMENTS."
                )

                st.code(
                    f"BACKEND: {BACKEND_URL}"
                )

                st.stop()

            if clear_response.status_code != 200:

                upload_placeholder.empty()

                st.error(
                    f"FAILED TO CLEAR OLD DOCUMENTS "
                    f"(HTTP {clear_response.status_code})"
                )

                try:

                    st.code(
                        clear_response.text
                    )

                except Exception:

                    pass

                st.stop()


        # ----------------------------------------------------
        # PREPARE FILE
        # ----------------------------------------------------

        file_bytes = uploaded.getvalue()

        files = {
            "file": (
                uploaded.name,
                file_bytes,
                uploaded.type or "application/octet-stream",
            )
        }

        data = {
            "collection_name": "documents",
        }


        # ----------------------------------------------------
        # UPLOAD TO FASTAPI
        # ----------------------------------------------------

        response = api_post(
            "/upload/upload",
            files=files,
            data=data,
            timeout=120,
        )

        upload_placeholder.empty()


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if (
            response is not None
            and response.status_code in (200, 201)
        ):

            st.session_state.last_upload = (
                uploaded.name
            )

            st.session_state.messages.append(
                {
                    "role": "system",
                    "content": (
                        f"[ FILE ATTACHED: "
                        f"{uploaded.name} ]"
                    ),
                }
            )

            st.success(
                f"UPLOADED: {uploaded.name}"
            )

            st.rerun()


        # ----------------------------------------------------
        # BACKEND ERROR
        # ----------------------------------------------------

        elif response is not None:

            st.error(
                f"UPLOAD FAILED "
                f"(HTTP {response.status_code})"
            )

            try:

                error_body = response.text

                if error_body:

                    st.code(
                        error_body
                    )

            except Exception:

                pass


        # ----------------------------------------------------
        # CONNECTION ERROR
        # ----------------------------------------------------

        else:

            st.error(
                "UPLOAD FAILED: BACKEND UNREACHABLE"
            )

            st.code(
                f"Backend URL: {BACKEND_URL}"
            )

            st.info(
                "Please verify that the Render backend is running."
            )


    except Exception as e:

        upload_placeholder.empty()

        st.error(
            f"UPLOAD ERROR: {str(e)}"
        )


st.divider()


# ============================================================
# CHAT INPUT
# ============================================================

if (
    not st.session_state.processing
    and not st.session_state.get(
        "human_gate_active"
    )
):

    prompt = st.chat_input(
        "TYPE YOUR QUESTION...",
    )

    if (
        prompt
        and prompt.strip()
    ):

        user_query = prompt.strip()

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_query,
            }
        )

        st.session_state.processing = True

        st.session_state.agent_logs = [
            {
                "agent": "ANALYZER",
                "status": "ACTIVE",
            },
            {
                "agent": "RETRIEVER",
                "status": "WAIT",
            },
            {
                "agent": "SYNTHESIZER",
                "status": "WAIT",
            },
            {
                "agent": "CRITIC",
                "status": "WAIT",
            },
        ]

        st.rerun()


# ============================================================
# PROCESSING PIPELINE
# ============================================================

if st.session_state.processing:

    if not st.session_state.messages:

        st.session_state.processing = False

        st.rerun()

    last = st.session_state.messages[-1]

    if last.get("role") != "user":

        st.session_state.processing = False

        st.rerun()

    query = last.get(
        "content",
        "",
    )

    try:

        if chat_ask:

            response_data = chat_ask(
                query=query,
                session_id=(
                    st.session_state.session_id
                ),
                collection_name="documents",
            )

            success = (
                response_data is not None
                and not response_data.get(
                    "error"
                )
            )

        else:

            response = api_post(
                "/chat/ask",
                json_data={
                    "query": query,
                    "session_id": (
                        st.session_state.session_id
                    ),
                    "collection_name": "documents",
                },
                timeout=130,
            )

            if (
                response is not None
                and response.status_code == 200
            ):

                response_data = response.json()

                success = True

            else:

                response_data = None

                success = False


        # ----------------------------------------------------
        # SUCCESSFUL RESPONSE
        # ----------------------------------------------------

        if success:

            returned_session_id = (
                response_data.get(
                    "session_id"
                )
            )

            if returned_session_id:

                st.session_state.session_id = (
                    returned_session_id
                )

                st.session_state.active_conversation_id = (
                    returned_session_id
                )


            if st.session_state.get(
                "current_conversation_title"
            ) in (
                None,
                "",
                "New Chat",
            ):

                title = query

                if len(title) > 55:

                    title = (
                        title[:55].rstrip()
                        + "..."
                    )

                st.session_state.current_conversation_title = (
                    title
                )


            answer = response_data.get(
                "answer",
                "NO ANSWER.",
            )

            score = response_data.get(
                "critique_score"
            )


            st.session_state.agent_logs = [
                {
                    "agent": "ANALYZER",
                    "status": "DONE",
                },
                {
                    "agent": "RETRIEVER",
                    "status": "DONE",
                },
                {
                    "agent": "SYNTHESIZER",
                    "status": "DONE",
                },
                {
                    "agent": "CRITIC",
                    "status": "DONE",
                },
            ]


            if (
                score is not None
                and score < 7
            ):

                st.session_state.human_gate_active = True

                st.session_state.pending_answer = (
                    answer
                )

                st.session_state.pending_score = (
                    score
                )

                st.session_state.pending_feedback = (
                    response_data.get(
                        "critique_feedback",
                        "",
                    )
                )

                st.session_state.processing = False

                st.rerun()


            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "critique_score": score,
                    "sources": response_data.get(
                        "used_sources",
                        [],
                    ),
                }
            )

            st.session_state.processing = False

            st.rerun()


        # ----------------------------------------------------
        # BACKEND ERROR
        # ----------------------------------------------------

        else:

            if response_data:

                error_message = (
                    response_data.get(
                        "error",
                        "BACKEND ERROR",
                    )
                )

            else:

                error_message = (
                    "BACKEND UNREACHABLE"
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        f"[ ERROR: "
                        f"{error_message} ]"
                    ),
                }
            )

            st.session_state.processing = False

            st.rerun()


    except Exception as e:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    f"[ ERROR: {str(e)} ]"
                ),
            }
        )

        st.session_state.processing = False

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "NEXUS | LANGGRAPH + OLLAMA + FASTEMBED"
)