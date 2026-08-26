import streamlit as st

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Agentic RAG Nexus",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.title("📁 Documents")
    st.write("This is the sidebar")
    
    uploaded_file = st.file_uploader(
        "Upload a file",
        type=["pdf", "docx", "txt"],
        key="clean_uploader"
    )
    
    if uploaded_file:
        st.success(f"✅ {uploaded_file.name} uploaded!")
    
    st.divider()
    st.caption("Your documents will appear here")

# ============================================
# MAIN CONTENT
# ============================================
st.title("Main Content Area")
st.write("If you can see the sidebar on the left, it's working!")