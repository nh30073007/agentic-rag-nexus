"""Sidebar — mobile responsive file upload."""

import streamlit as st

from frontend.utils.api_client import upload_document, list_documents


def render_sidebar():
    with st.sidebar:
        # Mobile-friendly header
        st.markdown(
            '<div style="font-size: 1.1rem; font-weight: 700; color: #f5f5f5; margin-bottom: 0.5rem;">📁 Documents</div>',
            unsafe_allow_html=True,
        )

        # ✅ Modern file uploader
        uploaded_file = st.file_uploader(
            "Drop PDF, DOCX, or TXT here",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
            key="sidebar_uploader",
            help="Upload documents to chat with them",
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

        # Document List
        st.markdown("---")
        st.caption("📄 Your Documents")

        docs_data = list_documents()
        documents = docs_data.get("documents", []) if isinstance(docs_data, dict) else []

        if not documents:
            st.info("No documents yet")
        else:
            for doc in documents:
                if isinstance(doc, dict):
                    name = doc.get("filename", "Unknown")
                    chunks = doc.get("chunk_count", 0)
                    st.markdown(
                        f"- **{name}**  \n"
                        f"  <span style='color:#737373;font-size:0.75rem;'>{chunks} chunks</span>",
                        unsafe_allow_html=True,
                    )