"""
Agentic RAG Nexus — Kimi-Style Unified Chat UI
Features: Day/Night Mode | Mobile Responsive | File Upload in Chat Bar
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st

from frontend.components.agent_tracker import render_agent_tracker
from frontend.components.chat_interface import render_chat_interface
from frontend.components.sidebar import render_sidebar
from frontend.utils.api_client import upload_document

# ============================================
# SESSION STATE INIT
# ============================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "chat_input_key" not in st.session_state:
    st.session_state.chat_input_key = 0
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None


def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"


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
# THEME CSS
# ============================================
DARK_THEME = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d0d0d;
        color: #e5e5e5;
    }
    
    .main .block-container {
        background-color: #0d0d0d;
        padding: 1rem 1.5rem 6rem 1.5rem;
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
        display: flex;
        justify-content: space-between;
        align-items: center;
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
    
    /* Theme Toggle Button */
    .theme-toggle {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        color: #e5e5e5;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .theme-toggle:hover {
        background-color: #262626;
        border-color: #444;
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
    
    /* Chat Input Area — Unified Bar */
    .chat-input-wrapper {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #0d0d0d;
        border-top: 1px solid #262626;
        padding: 1rem 1.5rem;
        z-index: 100;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .stChatInputContainer {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 16px;
    }
    .stChatInputContainer textarea {
        color: #e5e5e5;
    }
    
    /* File Uploader as Icon */
    .file-upload-icon button {
        background: transparent !important;
        border: none !important;
        color: #737373 !important;
        font-size: 1.2rem !important;
        padding: 0.5rem !important;
    }
    .file-upload-icon button:hover {
        color: #e5e5e5 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #1a1a1a;
        color: #e5e5e5;
        border: 1px solid #333;
        border-radius: 10px;
        font-weight: 500;
    }
    .stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        border: none;
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
    
    /* Mobile */
    @media screen and (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem 0.75rem 5rem 0.75rem;
        }
        .app-title { font-size: 1.2rem; }
        .chat-input-wrapper {
            padding: 0.75rem;
        }
    }
</style>
"""

LIGHT_THEME = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8f9fa;
        color: #1a1a1a;
    }
    
    .main .block-container {
        background-color: #f8f9fa;
        padding: 1rem 1.5rem 6rem 1.5rem;
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
        display: flex;
        justify-content: space-between;
        align-items: center;
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
    
    .theme-toggle {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        color: #1a1a1a;
        cursor: pointer;
    }
    .theme-toggle:hover {
        background-color: #f0f0f0;
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
    
    .chat-input-wrapper {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #f8f9fa;
        border-top: 1px solid #e5e5e5;
        padding: 1rem 1.5rem;
        z-index: 100;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .stChatInputContainer {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 16px;
    }
    .stChatInputContainer textarea {
        color: #1a1a1a;
    }
    
    .file-upload-icon button {
        background: transparent !important;
        border: none !important;
        color: #666 !important;
        font-size: 1.2rem !important;
    }
    .file-upload-icon button:hover {
        color: #1a1a1a !important;
    }
    
    .stButton > button {
        background-color: #ffffff;
        color: #1a1a1a;
        border: 1px solid #ddd;
    }
    .stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        border: none;
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
    
    @media screen and (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem 0.75rem 5rem 0.75rem;
        }
        .app-title { font-size: 1.2rem; }
        .chat-input-wrapper { padding: 0.75rem; }
    }
</style>
"""

# Apply theme
if st.session_state.theme == "dark":
    st.markdown(DARK_THEME, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_THEME, unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
header_col1, header_col2 = st.columns([6, 1])
with header_col1:
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <div class="app-title">🧠 Agentic RAG Nexus</div>
                <div class="app-subtitle">Multi-Agent Document Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_col2:
    theme_emoji = "☀️" if st.session_state.theme == "dark" else "🌙"
    theme_label = "Light" if st.session_state.theme == "dark" else "Dark"
    if st.button(f"{theme_emoji} {theme_label}", key="theme_toggle", use_container_width=True):
        toggle_theme()
        st.rerun()

# ============================================
# SIDEBAR — Document List Only
# ============================================
render_sidebar()

# ============================================
# MAIN CONTENT
# ============================================
chat_col, tracker_col = st.columns([3, 2], gap="large")

with chat_col:
    render_chat_interface()

with tracker_col:
    render_agent_tracker()

# ============================================
# UNIFIED CHAT BAR (Bottom Fixed)
# ============================================
st.markdown('<div class="chat-input-wrapper">', unsafe_allow_html=True)

# File upload as attachment icon
upload_col, input_col = st.columns([1, 12])

with upload_col:
    st.markdown('<div class="file-upload-icon">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "📎",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        key=f"chat_upload_{st.session_state.chat_input_key}",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Handle file upload immediately
    if uploaded_file:
        file_key = f"uploaded_{uploaded_file.name}"
        if file_key not in st.session_state:
            with st.spinner("📤 Uploading..."):
                result = upload_document(uploaded_file)
                if result.get("error"):
                    st.error(f"❌ {result['error']}")
                else:
                    st.session_state[file_key] = True
                    st.session_state.uploaded_file_name = uploaded_file.name
                    st.session_state.chat_input_key += 1  # Reset file uploader
                    st.rerun()
        else:
            st.caption(f"✅ {uploaded_file.name}")

with input_col:
    # Chat input from chat_interface module
    from frontend.components.chat_interface import render_chat_input
    render_chat_input()

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Built with LangGraph + FastAPI + Streamlit")