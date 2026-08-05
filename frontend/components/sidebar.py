"""Clean sidebar with high contrast."""

import streamlit as st

from frontend.utils.api_client import list_documents, upload_document


def render_sidebar():
    with st.sidebar:
        # Logo area
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0.5rem 1rem; border-bottom: 1px solid #262626; margin-bottom: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 0.3rem;">📚</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #f5f5f5;">Document Hub</div>
                <div style="font-size: 0.8rem; color: #a3a3a3; margin-top: 0.2rem;">Manage knowledge base</div>
            </div>
        """, unsafe_allow_html=True)

        # Upload section
        st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #e5e5e5; margin-bottom: 0.8rem;">⬆️ Upload Document</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Choose PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
        )

        collection = st.text_input(
            "Collection Name",
            value="documents",
            help="Group documents into collections",
        )

        if uploaded_file:
            if st.button("🚀 Process & Store", type="primary", use_container_width=True):
                with st.spinner("Reading document..."):
                    result = upload_document(uploaded_file, collection)
                    if "error" in result:
                        st.error(f"❌ {result['error'][:200]}")
                    else:
                        st.success(f"✅ **{result.get('filename', 'File')}** uploaded")
                        st.caption(f"📊 {result.get('chunks', 0)} chunks indexed")

        st.markdown('<div style="border-top: 1px solid #262626; margin: 1.2rem 0;"></div>', unsafe_allow_html=True)

        # Document list
        st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #e5e5e5; margin-bottom: 0.8rem;">📑 Stored Documents</div>', unsafe_allow_html=True)

        docs_data = list_documents()
        docs = docs_data.get("documents", [])

        if docs:
            for doc in docs:
                with st.expander(f"📄 {doc['filename'][:30]}{'...' if len(doc['filename']) > 30 else ''}"):
                    st.markdown(f"""
                        <div style="font-size: 0.85rem; color: #d4d4d4; line-height: 1.8;">
                            <div><strong style="color: #a3a3a3;">Type:</strong> {doc['file_type'].upper()}</div>
                            <div><strong style="color: #a3a3a3;">Chunks:</strong> {doc['chunk_count']}</div>
                            <div><strong style="color: #a3a3a3;">Collection:</strong> <code style="background: #1a1a1a; padding: 2px 6px; border-radius: 4px; color: #d4d4d4;">{doc['collection_name']}</code></div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="text-align: center; padding: 2rem 1rem;">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem; opacity: 0.3;">📭</div>
                    <div style="font-size: 0.85rem; color: #525252;">No documents uploaded yet</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="border-top: 1px solid #262626; margin: 1.2rem 0;"></div>', unsafe_allow_html=True)
        st.caption("Agentic RAG Nexus v1.0")