"""
Agentic RAG Nexus — Kimi-Style Mobile Responsive UI
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
    initial_sidebar_state="collapsed",
)

# ============================================
# DARK THEME + MOBILE RESPONSIVE CSS
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
        padding-top: 0.5rem;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 0;
        max-width: 1400px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #262626;
    }
    [data-testid="stSidebar"] .block-container {
        background-color: #141414;
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
    
    /* User message */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #1e3a5f;
        border: 1px solid #2a4a6f;
    }
    
    /* Chat input */
    .stChatInputContainer {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 16px;
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
    
    /* Expander — file panel */
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
    }
    
    /* File uploader */
    .stFileUploader > div > div {
        background-color: #1a1a1a;
        border: 2px dashed #333;
        border-radius: 12px;
        color: #a3a3a3;
    }
    .stFileUploader > div > div:hover {
        border-color: #2563eb;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 10px;
        color: #e5e5e5;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    
    /* Hide defaults */
    #MainMenu, footer, header { visibility: hidden; }
    hr { border-color: #262626; }
    
    /* ==========================================
       MOBILE RESPONSIVE
       ========================================== */
    @media screen and (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        .stChatMessage [data-testid="stChatMessageContent"] {
            padding: 0.6rem 0.8rem;
            border-radius: 12px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
    <div style="margin-bottom: 0.8rem;">
        <div style="font-size: 1.4rem; font-weight: 700; color: #f5f5f5;">🧠 Agentic RAG Nexus</div>
        <div style="font-size: 0.8rem; color: #737373;">Multi-Agent Document Intelligence</div>
    </div>
""", unsafe_allow_html=True)

# ============================================
# MOBILE: Files Button (Opens expander, NOT sidebar toggle)
# ============================================
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("📁 Files", use_container_width=True, key="files_btn"):
        st.session_state.show_files = not st.session_state.get("show_files", False)
        st.rerun()

# ============================================
# SIDEBAR (Desktop) — Native Streamlit sidebar
# ============================================
render_sidebar()

# ============================================
# MOBILE FILE PANEL (Expander in main area)
# ============================================
if st.session_state.get("show_files", False):
    with st.expander("📁 Upload Documents", expanded=True):
        from frontend.utils.api_client import upload_document, list_documents
        
        uploaded_file = st.file_uploader(
            "Drop PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
            key="mobile_uploader",
        )
        
        if uploaded_file:
            upload_key = f"uploaded_{uploaded_file.name}"
            if upload_key not in st.session_state:
                with st.spinner("📤 Uploading..."):
                    result = upload_document(uploaded_file)
                    if result.get("error"):
                        st.error(f"❌ {result['error']}")
                    else:
                        st.success("✅ Uploaded!")
                        st.session_state[upload_key] = True
                        st.rerun()
            else:
                st.success(f"✅ {uploaded_file.name}")
        
        # Document list
        st.markdown("---")
        docs_data = list_documents()
        documents = docs_data.get("documents", []) if isinstance(docs_data, dict) else []
        
        if not documents:
            st.info("No documents yet")
        else:
            for doc in documents:
                if isinstance(doc, dict):
                    name = doc.get("filename", "Unknown")
                    chunks = doc.get("chunk_count", 0)
                    st.markdown(f"- **{name}**  \n  <span style='color:#737373;font-size:0.75rem;'>{chunks} chunks</span>", unsafe_allow_html=True)
        
        if st.button("❌ Close", use_container_width=True):
            st.session_state.show_files = False
            st.rerun()

# ============================================
# MAIN CHAT AREA
# ============================================

# ✅ ROOT LEVEL: chat input
render_chat_input()

# Responsive columns
chat_col, tracker_col = st.columns([3, 2], gap="large")

with chat_col:
    render_chat_interface()

with tracker_col:
    render_agent_tracker()

st.markdown("---")
st.caption("Built with LangGraph + FastAPI + Streamlit")