"""Sidebar — Modern file upload + document list."""

import streamlit as st

from frontend.utils.api_client import upload_document, list_documents


def render_sidebar():
    with st.sidebar:
        # Header
        st.markdown(
            '<div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;">📁 Documents</div>',
            unsafe_allow_html=True,
        )

        # Modern File Uploader
        uploaded_file = st.file_uploader(
            "Drop PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
            key="sidebar_uploader",
            help="Upload documents to chat with them",
        )

        if uploaded_file:
            file_key = f"uploaded_{uploaded_file.name}"

            if file_key not in st.session_state:
                with st.spinner("📤 Uploading..."):
                    result = upload_document(uploaded_file)

                    if result.get("error"):
                        st.error(f"❌ {result['error']}")
                    else:
                        st.success("✅ Uploaded successfully!")
                        st.session_state[file_key] = True
                        st.rerun()
            else:
                st.caption(f"✅ {uploaded_file.name}")

        # Document List
        st.markdown("---")
        st.caption("📄 Your Documents")

        docs_data = list_documents()
        documents = docs_data.get("documents", []) if isinstance(docs_data, dict) else []

        if not documents:
            st.info("No documents yet")
        else:
            st.markdown(f"**{len(documents)}** document(s)")
            for doc in documents:
                if isinstance(doc, dict):
                    name = doc.get("filename", "Unknown")
                    chunks = doc.get("chunk_count", 0)
                    st.markdown(
                        f"- **{name}**  \n"
                        f"  <span style='opacity:0.6;font-size:0.75rem;'>{chunks} chunks</span>",
                        unsafe_allow_html=True,
                    )