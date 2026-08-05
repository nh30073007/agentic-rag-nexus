"""Sidebar component with document upload and backend status."""

import streamlit as st

from frontend.utils.api_client import upload_document, list_documents, API_BASE


def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="font-size: 1.1rem; font-weight: 700; color: #f5f5f5; margin-bottom: 0.5rem;">📁 Documents</div>',
            unsafe_allow_html=True,
        )

        # ✅ Backend Status Check
        backend_alive = _check_backend_status()
        
        if not backend_alive:
            st.warning("🔴 Backend is sleeping")
            if st.button("🚀 Wake Up Backend", use_container_width=True):
                _wake_backend()
            st.info("Click 'Wake Up' and wait 30s, then refresh")
            st.stop()  # Don't render rest if backend down

        # File Upload
        uploaded_file = st.file_uploader(
            "Upload PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
        )

        if uploaded_file:
            with st.spinner("Uploading..."):
                result = upload_document(uploaded_file)
                if result.get("error"):
                    st.error(f"❌ {result['error']}")
                else:
                    st.success("✅ Uploaded!")
                    st.rerun()

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
                st.markdown(f"- {name}")


def _check_backend_status():
    """Quick check if backend is reachable."""
    import requests
    try:
        response = requests.get(
            f"{API_BASE}/health/health",
            timeout=5  # Short timeout for quick check
        )
        return response.status_code == 200
    except Exception:
        return False


def _wake_backend():
    """Open backend URL to wake it up."""
    import webbrowser
    wake_url = API_BASE.replace("/api/v1", "")
    webbrowser.open(wake_url)
    st.success("✅ Opening backend... wait 30s and refresh")