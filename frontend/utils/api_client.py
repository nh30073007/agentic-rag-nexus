"""HTTP client for FastAPI backend."""

import json
import os
import time

import requests
import streamlit as st

# ✅ Auto-detect environment (local vs Streamlit Cloud)
LOCAL_URL = "http://localhost:8000/api/v1"
PROD_URL = "https://agentic-rag-nexus.onrender.com/api/v1"
API_BASE = os.getenv("API_BASE_URL", PROD_URL)

# Render free tier wake-up time
MAX_RETRIES = 3
BACKEND_TIMEOUT = 60  # seconds (Render sleep থেকে wake up হতে 30-60s লাগে)


def _request_with_retry(method, endpoint, **kwargs):
    """
    Make HTTP request with retry logic for Render sleep mode.
    """
    url = f"{API_BASE}{endpoint}"
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method,
                url,
                timeout=BACKEND_TIMEOUT,
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait_time = attempt * 5  # 5s, 10s, 15s
                time.sleep(wait_time)
            continue

        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(10)
            continue

        except requests.exceptions.HTTPError as e:
            # Don't retry 4xx errors (client errors)
            if 400 <= e.response.status_code < 500:
                raise
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(5)
            continue

    # All retries exhausted
    raise last_error


def _safe_request(method, endpoint, **kwargs):
    """
    Wrapper that catches errors and returns safe defaults for UI.
    """
    try:
        return _request_with_retry(method, endpoint, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error("🔴 Backend is sleeping or unreachable. Please wait 30-60s and refresh.")
        raise
    except requests.exceptions.Timeout:
        st.error("⏱️ Backend is taking too long to respond. It may be waking up...")
        raise
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Server error {e.response.status_code}: {e.response.text[:200]}")
        raise


def upload_document(file, collection_name="documents"):
    """Upload a document to the backend."""
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"collection_name": collection_name}
    try:
        response = _safe_request("POST", "/upload/upload", files=files, data=data)
        return response.json()
    except Exception:
        return {"error": "Upload failed. Is backend running?"}


def list_documents():
    """List all uploaded documents."""
    try:
        response = _safe_request("GET", "/upload/documents")
        return response.json()
    except Exception:
        return {"documents": []}


def create_session():
    """Create a new chat session."""
    try:
        response = _safe_request("POST", "/session/create")
        return response.json()
    except Exception:
        return {"session_id": "fallback-session", "error": "Backend unreachable"}


def get_session_history(session_id):
    """Get chat history."""
    try:
        response = _safe_request("GET", f"/session/{session_id}/history")
        return response.json()
    except Exception:
        return {"history": []}


def send_chat_stream(query, session_id, collection_name="documents"):
    """Send chat query and return SSE stream."""
    payload = {
        "query": query,
        "session_id": session_id,
        "collection_name": collection_name,
    }
    # Stream requests need manual handling - don't use _safe_request
    try:
        response = requests.post(
            f"{API_BASE}/chat/stream",
            json=payload,
            stream=True,
            timeout=BACKEND_TIMEOUT,
        )
        return response
    except requests.exceptions.ConnectionError:
        st.error("🔴 Backend is sleeping. Please wait 30-60s and try again.")
        raise
    except requests.exceptions.Timeout:
        st.error("⏱️ Backend timeout. It may be waking up from sleep...")
        raise


def approve_answer(session_id, decision, feedback=""):
    """Send human approval/rejection."""
    payload = {
        "session_id": session_id,
        "decision": decision,
        "feedback": feedback,
    }
    try:
        response = _safe_request("POST", "/chat/approve", json=payload)
        return response.json()
    except Exception:
        return {"error": "Approval failed"}


def get_session_status(session_id):
    """Get current session state."""
    try:
        response = _safe_request("GET", f"/chat/session/{session_id}")
        return response.json()
    except Exception:
        return {}