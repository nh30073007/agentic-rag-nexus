"""Sidebar — Document list only. File upload moved to chat bar."""

import streamlit as st

from frontend.utils.api_client import list_documents


def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;">📁 Documents</div>',
            unsafe_allow_html=True,
        )

        # Document List
        docs_data = list_documents()
        documents = docs_data.get("documents", []) if isinstance(docs_data, dict) else []

        if not documents:
            st.info("No documents yet")
        else:
            st.caption(f"📄 {len(documents)} document(s)")
            for doc in documents:
                if isinstance(doc, dict):
                    name = doc.get("filename", "Unknown")
                    chunks = doc.get("chunk_count", 0)
                    st.markdown(
                        f"- **{name}**  \n"
                        f"  <span style='opacity:0.6;font-size:0.75rem;'>{chunks} chunks</span>",
                        unsafe_allow_html=True,
                    )

        st.markdown("---")
        st.caption("Upload via chat bar 📎")