"""
Agentic RAG Nexus — Mobile Responsive Kimi-Style UI
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
    initial_sidebar_state="collapsed",  # ✅ Mobile: sidebar hidden by default
)

# ============================================
# MOBILE RESPONSIVE CSS
# ============================================
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
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1400px;
    }
    
    /* Sidebar — mobile friendly */
    [data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #262626;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #f5f5f5;
        font-weight: 600;
    }
    
    /* Chat messages — Kimi style */
    .stChatMessage [data-testid="stChatMessageContent"] {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 16px;
        padding: 0.8rem 1rem;
        color: #e5e5e5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    /* User message — blue tint */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #1e3a5f;
        border: 1px solid #2a4a6f;
    }
    
    /* Chat input — fixed at bottom */
    .stChatInputContainer {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 16px;
        margin-bottom: 0.5rem;
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
    
    /* File uploader — modern drag & drop */
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
    
    /* ==========================================
       MOBILE RESPONSIVE — Media Queries
       ========================================== */
    @media screen and (max-width: 768px) {
        /* Mobile: smaller padding */
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            padding-top: 0.5rem;
        }
        
        /* Mobile: header smaller */
        .header-title {
            font-size: 1.2rem !important;
        }
        .header-subtitle {
            font-size: 0.75rem !important;
        }
        
        /* Mobile: chat bubbles full width */
        .stChatMessage [data-testid="stChatMessageContent"] {
            padding: 0.6rem 0.8rem;
            border-radius: 12px;
        }
        
        /* Mobile: agent tracker hidden or stacked */
        [data-testid="column"] {
            width: 100% !important;
        }
        
        /* Mobile: sidebar button visible */
        [data-testid="stSidebarCollapsedControl"] {
            background-color: #1a1a1a;
            border: 1px solid #333;
        }
    }
    
    /* ==========================================
       TABLET RESPONSIVE
       ========================================== */
    @media screen and (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# MOBILE HEADER
# ============================================
st.markdown("""
    <div style="margin-bottom: 1rem;">
        <div class="header-title" style="font-size: 1.4rem; font-weight: 700; color: #f5f5f5;">🧠 Agentic RAG Nexus</div>
        <div class="header-subtitle" style="font-size: 0.8rem; color: #737373; margin-top: 0.2rem;">Multi-Agent Document Intelligence</div>
    </div>
""", unsafe_allow_html=True)

# ============================================
# MOBILE: Sidebar Toggle Button (Top Right)
# ============================================
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("📁 Files", use_container_width=True):
        st.sidebar.toggle()

# ============================================
# SIDEBAR — File Upload (Mobile Friendly)
# ============================================
render_sidebar()

# ============================================
# MAIN CHAT AREA
# ============================================

# ✅ ROOT LEVEL: chat input (must be outside columns)
render_chat_input()

# Responsive columns: mobile = stacked, desktop = side by side
chat_col, tracker_col = st.columns([3, 2], gap="large")

with chat_col:
    render_chat_interface()

with tracker_col:
    # On mobile, this stacks below chat automatically
    render_agent_tracker()

st.markdown("---")
st.caption("Built with LangGraph + FastAPI + Streamlit")