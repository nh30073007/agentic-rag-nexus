"""HTTP client for FastAPI backend."""

import json
import os
import time

import requests


# ============================================
# Environment Config
# ============================================
LOCAL_URL = "http://localhost:8000/api/v1"
PROD_URL = "https://agentic-rag-nexus.onrender.com/api/v1"
API_BASE = os.getenv("API_BASE_URL", PROD_URL)

HEALTH_TIMEOUT = 10
DEFAULT_TIMEOUT = 30
UPLOAD_TIMEOUT = 120
STREAM_TIMEOUT = 120


class APIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


# ============================================
# Low-level Request Handler
# ============================================
def _request(method, endpoint, timeout=DEFAULT_TIMEOUT, retries=2, **kwargs):
    url = f"{API_BASE}{endpoint}"
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError as e:
            last_error = APIError(
                f"Cannot connect to backend (attempt {attempt}/{retries}). "
                "Backend may be sleeping — wait 30s and retry."
            )
            if attempt < retries:
                time.sleep(5 * attempt)

        except requests.exceptions.Timeout as e:
            last_error = APIError(
                f"Request timed out after {timeout}s (attempt {attempt}/{retries})."
            )
            if attempt < retries:
                time.sleep(5 * attempt)

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            text = e.response.text[:300]
            raise APIError(f"Server error {status}: {text}", status_code=status)

    raise last_error


# ============================================
# Safe JSON Parser — Handles tuple/list responses
# ============================================
def _safe_json(response):
    """Parse JSON, ensure dict return. Handles tuple/list gracefully."""
    try:
        data = response.json()
        if isinstance(data, dict):
            return data
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return data[0]  # Take first item if list of dicts
        else:
            return {"raw_response": data, "error": "Unexpected response format"}
    except Exception as e:
        return {"error": f"JSON parse failed: {str(e)}"}


# ============================================
# Public API Functions
# ============================================

def health_check():
    try:
        resp = _request("GET", "/health/health", timeout=HEALTH_TIMEOUT, retries=2)
        return _safe_json(resp)
    except APIError as e:
        return {"status": "unhealthy", "detail": str(e)}


def upload_document(file, collection_name="documents"):
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"collection_name": collection_name}
    try:
        resp = _request("POST", "/upload/upload", files=files, data=data, timeout=UPLOAD_TIMEOUT, retries=2)
        return _safe_json(resp)
    except APIError as e:
        return {"error": str(e), "status_code": e.status_code}


def list_documents():
    try:
        resp = _request("GET", "/upload/documents", timeout=DEFAULT_TIMEOUT, retries=2)
        return _safe_json(resp)
    except APIError:
        return {"documents": []}


def create_session():
    try:
        resp = _request("POST", "/session/create", timeout=DEFAULT_TIMEOUT, retries=2)
        return _safe_json(resp)
    except APIError:
        return {"session_id": "default-session"}


def get_session_history(session_id):
    try:
        resp = _request("GET", f"/session/{session_id}/history", timeout=DEFAULT_TIMEOUT, retries=2)
        return _safe_json(resp)
    except APIError:
        return {"history": []}


def get_session_status(session_id):
    """Get current session state — BULLETPROOF."""
    try:
        resp = _request("GET", f"/chat/session/{session_id}", timeout=DEFAULT_TIMEOUT, retries=2)
        result = _safe_json(resp)
        
        # Ensure we always return a dict with expected fields
        if not isinstance(result, dict):
            result = {}
        
        # Normalize nested state if present
        if "current_state" in result and isinstance(result["current_state"], dict):
            state = result["current_state"]
            return {
                "current_state": state,
                "generation": state.get("generation"),
                "human_approved": state.get("human_approved"),
                "critique_score": state.get("critique_score"),
                "critique_feedback": state.get("critique_feedback", ""),
            }
        return result
        
    except APIError:
        return {
            "current_state": {},
            "generation": None,
            "human_approved": None,
            "critique_score": None,
            "critique_feedback": "",
        }


def send_chat_stream(query, session_id, collection_name="documents"):
    payload = {
        "query": query,
        "session_id": session_id,
        "collection_name": collection_name,
    }
    url = f"{API_BASE}/chat/stream"

    try:
        resp = requests.post(url, json=payload, stream=True, timeout=STREAM_TIMEOUT)
        resp.raise_for_status()
        return resp
    except requests.exceptions.ConnectionError:
        raise APIError("Backend connection failed. It may be waking up — wait 30s.")
    except requests.exceptions.Timeout:
        raise APIError("Chat stream timed out.")
    except requests.exceptions.HTTPError as e:
        raise APIError(
            f"Server error {e.response.status_code}: {e.response.text[:300]}",
            status_code=e.response.status_code,
        )


def approve_answer(session_id, decision, feedback=""):
    payload = {
        "session_id": session_id,
        "decision": decision,
        "feedback": feedback,
    }
    try:
        resp = _request("POST", "/chat/approve", json=payload, timeout=DEFAULT_TIMEOUT, retries=2)
        return _safe_json(resp)
    except APIError as e:
        return {"error": str(e)}