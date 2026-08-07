"""
Agentic RAG Nexus — Kimi-Style UI
Day/Night Mode | Mobile Responsive | Root-Level Chat Input
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st

from frontend.components.agent_tracker import render_agent_tracker
from frontend.components.chat_interface import render_chat_interface, render_chat_input
from frontend.components.sidebar import render_sidebar

# ============================================
# THEME STATE
# ============================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"


def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    st.rerun()


# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Agentic RAG Nexus",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================
# CSS THEMES
# ============================================
DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d0d0d;
        color: #e5e5e5;
    }
    
    .main .block-container {
        background-color: #0d0d0d;
        padding-top: 1rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        padding-bottom: 6rem;
        max-width: 1400px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #262626;
    }
    [data-testid="stSidebar"] .block-container {
        background-color: #141414;
    }
    
    /* Header */
    .app-header {
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #262626;
    }
    .app-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f5f5f5;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.8rem;
        color: #737373;
        margin-top: 0.2rem;
    }
    
    /* Chat Messages */
    .stChatMessage [data-testid="stChatMessageContent"] {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        color: #e5e5e5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #1e3a5f;
        border: 1px solid #2a4a6f;
    }
    
    /* Chat Input — Root Level Styling */
    .stChatInputContainer {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 16px;
        position: fixed;
        bottom: 1rem;
        left: 50%;
        transform: translateX(-50%);
        width: calc(100% - 3rem);
        max-width: 800px;
        z-index: 100;
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
    
    /* File Uploader in Sidebar */
    .stFileUploader > div > div {
        background-color: #1a1a1a;
        border: 2px dashed #333;
        border-radius: 12px;
        color: #a3a3a3;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 10px;
        color: #e5e5e5;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        color: #e5e5e5;
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
    
    /* Hide defaults */
    #MainMenu, footer, header { visibility: hidden; }
    hr { border-color: #262626; }
    .stCaption { color: #737373; }
    
    /* Mobile */
    @media screen and (max-width: 768px) {
        .main .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
            padding-bottom: 5rem;
        }
        .app-title { font-size: 1.2rem; }
        .stChatInputContainer {
            width: calc(100% - 1.5rem);
        }
    }
</style>
"""

LIGHT_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8f9fa;
        color: #1a1a1a;
    }
    
    .main .block-container {
        background-color: #f8f9fa;
        padding-top: 1rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        padding-bottom: 6rem;
        max-width: 1400px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e5e5;
    }
    [data-testid="stSidebar"] .block-container {
        background-color: #ffffff;
    }
    
    .app-header {
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e5e5e5;
    }
    .app-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a1a1a;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.2rem;
    }
    
    .stChatMessage [data-testid="stChatMessageContent"] {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        color: #1a1a1a;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #dbeafe;
        border: 1px solid #bfdbfe;
    }
    
    .stChatInputContainer {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 16px;
        position: fixed;
        bottom: 1rem;
        left: 50%;
        transform: translateX(-50%);
        width: calc(100% - 3rem);
        max-width: 800px;
        z-index: 100;
    }
    .stChatInputContainer textarea {
        color: #1a1a1a;
    }
    
    .stButton > button {
        background-color: #ffffff;
        color: #1a1a1a;
        border: 1px solid #ddd;
        border-radius: 10px;
    }
    .stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        border: none;
    }
    
    .stFileUploader > div > div {
        background-color: #ffffff;
        border: 2px dashed #ddd;
        border-radius: 12px;
        color: #666;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 10px;
        color: #1a1a1a;
    }
    
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        color: #1a1a1a;
    }
    
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 12px;
    }
    
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
    
    #MainMenu, footer, header { visibility: hidden; }
    hr { border-color: #e5e5e5; }
    .stCaption { color: #666; }
    
    @media screen and (max-width: 768px) {
        .main .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
            padding-bottom: 5rem;
        }
        .app-title { font-size: 1.2rem; }
        .stChatInputContainer { width: calc(100% - 1.5rem); }
    }
</style>
"""

# Apply theme
if st.session_state.theme == "dark":
    st.markdown(DARK_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
header_col1, header_col2 = st.columns([6, 1])
with header_col1:
    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title">🧠 Agentic RAG Nexus</div>
            <div class="app-subtitle">Multi-Agent Document Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_col2:
    emoji = "☀️" if st.session_state.theme == "dark" else "🌙"
    label = "Light" if st.session_state.theme == "dark" else "Dark"
    if st.button(f"{emoji} {label}", key="theme_btn", use_container_width=True):
        toggle_theme()

# ============================================
# SIDEBAR — File Upload + Document List
# ============================================
render_sidebar()

# ============================================
# MAIN CONTENT — Chat + Agent Tracker
# ============================================
chat_col, tracker_col = st.columns([3, 2], gap="large")

with chat_col:
    render_chat_interface()

with tracker_col:
    render_agent_tracker()

# ============================================
# ✅ ROOT LEVEL: Chat Input (NO columns, NO containers!)
# ============================================
render_chat_input()

st.markdown("---")
st.caption("Built with LangGraph + FastAPI + Streamlit")