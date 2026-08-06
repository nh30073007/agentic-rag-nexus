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

# ✅ Smooth dark theme — NO aggressive !important on inputs
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d0d0d;
        color: #e5e5e5;
    }
    
    .main .block-container {
        background-color: #0d0d0d;
        padding-top: 1.5rem;
        max-width: 1400px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #262626;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #f5f5f5;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Chat messages — Kimi style */
    .stChatMessage [data-testid="stChatMessageContent"] {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        color: #e5e5e5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        transition: all 0.2s ease;
    }
    
    /* User message — blue tint */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #1e3a5f;
        border: 1px solid #2a4a6f;
    }
    
    /* Chat input — fixed at bottom, no brightness issue */
    .stChatInputContainer {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 16px;
        transition: border-color 0.2s ease;
    }
    .stChatInputContainer:focus-within {
        border-color: #2563eb;
    }
    .stChatInputContainer textarea {
        color: #e5e5e5;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #1a1a1a;
        color: #e5e5e5;
        border: 1px solid #333;
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #262626;
        border-color: #444;
    }
    .stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
    }
    
    /* File uploader — smooth, no flash */
    .stFileUploader > div > div {
        background-color: #1a1a1a;
        border: 2px dashed #333;
        border-radius: 12px;
        color: #a3a3a3;
        transition: all 0.2s ease;
    }
    .stFileUploader > div > div:hover {
        border-color: #2563eb;
        background-color: #1a1a1a;
    }
    /* Upload complete state — NO brightness drop */
    .stFileUploader [data-testid="stFileUploaderFile"] {
        background-color: #1a1a1a;
        color: #e5e5e5;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 10px;
        color: #e5e5e5;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #2563eb;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        color: #e5e5e5;
    }
    .streamlit-expanderContent {
        background-color: #141414;
        border: 1px solid #2a2a2a;
        border-top: none;
        border-radius: 0 0 12px 12px;
        color: #d4d4d4;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #444; }
    
    /* Hide defaults */
    #MainMenu, footer, header { visibility: hidden; }
    
    hr { border-color: #262626; }
    .stCaption { color: #737373; }
    
    /* Spinner — no dimming */
    .stSpinner > div {
        border-color: #2563eb transparent transparent transparent;
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

# ✅ ROOT LEVEL: chat input (must be outside columns)
render_chat_input()

# Columns
chat_col, tracker_col = st.columns([3, 2], gap="large")

with chat_col:
    render_chat_interface()

with tracker_col:
    render_agent_tracker()

st.markdown("---")
st.caption("Built with LangGraph + FastAPI + Streamlit")