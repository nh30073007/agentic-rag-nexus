"""Sidebar component — smooth upload without brightness drop."""

import streamlit as st

from frontend.utils.api_client import upload_document, list_documents


def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="font-size: 1.1rem; font-weight: 700; color: #f5f5f5; margin-bottom: 0.5rem;">📁 Documents</div>',
            unsafe_allow_html=True,
        )

        # File Upload — NO spinner flash, smooth transition
        uploaded_file = st.file_uploader(
            "Upload PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
            key="sidebar_uploader",
        )

        if uploaded_file:
            # Use session state to prevent re-upload on every rerun
            upload_key = f"uploaded_{uploaded_file.name}"
            
            if upload_key not in st.session_state:
                with st.container():
                    st.info("📤 Uploading... please wait")
                    result = upload_document(uploaded_file)
                    
                    if result.get("error"):
                        st.error(f"❌ {result['error']}")
                    else:
                        st.success("✅ Uploaded successfully!")
                        st.session_state[upload_key] = True
                        st.rerun()
            else:
                st.success(f"✅ {uploaded_file.name} ready")

        # Document List
        st.markdown("---")
        st.caption("📄 Uploaded Documents")

        docs_data = list_documents()
        documents = docs_data.get("documents", [])

        if not documents:
            st.info("No documents yet")
        else:
            for doc in documents:
                name = doc.get("filename", "Unknown")
                chunks = doc.get("chunk_count", 0)
                st.markdown(f"- **{name}**  \n  <span style='color:#737373;font-size:0.75rem;'>{chunks} chunks</span>", unsafe_allow_html=True)