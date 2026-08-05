"""
Agentic RAG Nexus — Kimi-Style Clean UI
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st

from frontend.components.agent_tracker import render_agent_tracker
from frontend.components.chat_interface import render_chat_interface, render_chat_input
from frontend.components.sidebar import render_sidebar

st.set_page_config(
    page_title="Agentic RAG Nexus",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d0d0d !important;
        color: #e5e5e5 !important;
    }

    /* Main background */
    .main .block-container {
        background-color: #0d0d0d !important;
        padding-top: 1.5rem;
        max-width: 1400px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #141414 !important;
        border-right: 1px solid #262626 !important;
    }
    [data-testid="stSidebar"] .block-container {
        background-color: #141414 !important;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #f5f5f5 !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }

    /* Text colors */
    p, li, label, .stMarkdown {
        color: #d4d4d4 !important;
    }

    /* Chat messages */
    .stChatMessage [data-testid="stChatMessageContent"] {
        background-color: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 16px !important;
        padding: 1rem 1.2rem !important;
        color: #e5e5e5 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
    }

    /* User message */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #1e3a5f !important;
        border: 1px solid #2a4a6f !important;
    }

    /* Input */
    .stChatInputContainer {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        border-radius: 16px !important;
    }
    .stChatInputContainer textarea {
        color: #e5e5e5 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #1a1a1a !important;
        color: #e5e5e5 !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #262626 !important;
        border-color: #444 !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 12px !important;
        color: #e5e5e5 !important;
    }
    .streamlit-expanderContent {
        background-color: #141414 !important;
        border: 1px solid #2a2a2a !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        color: #d4d4d4 !important;
    }

    /* File uploader */
    .stFileUploader > div > div {
        background-color: #1a1a1a !important;
        border: 2px dashed #333 !important;
        border-radius: 12px !important;
        color: #a3a3a3 !important;
    }

    /* Text input */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        color: #e5e5e5 !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background-color: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 12px !important;
    }
    [data-testid="stMetric"] label {
        color: #a3a3a3 !important;
    }
    [data-testid="stMetric"] .css-1xarl3l {
        color: #f5f5f5 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #444; }

    /* Hide defaults */
    #MainMenu, footer, header { visibility: hidden; }

    /* Divider */
    hr {
        border-color: #262626 !important;
    }

    /* Caption */
    .stCaption {
        color: #737373 !important;
    }
</style>
""", unsafe_allow_html=True)

render_sidebar()

# Header
st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 1.6rem; font-weight: 700; color: #f5f5f5; letter-spacing: -0.02em;">🧠 Agentic RAG Nexus</div>
        <div style="font-size: 0.85rem; color: #737373; margin-top: 0.2rem;">Multi-Agent Document Intelligence with Human-in-the-Loop</div>
    </div>
""", unsafe_allow_html=True)

# ✅ ROOT LEVEL: chat_input (MUST be outside columns/tabs/expander)
render_chat_input()

# Columns for chat history + agent tracker
chat_col, tracker_col = st.columns([3, 2], gap="large")

with chat_col:
    # Chat history, processing, human gate (NO chat_input here)
    render_chat_interface()

with tracker_col:
    render_agent_tracker()

st.markdown("---")
st.caption("Built with LangGraph + FastAPI + Streamlit")