"""HTTP client — bulletproof."""

import json
import os
import time

import requests

API_BASE = os.getenv("API_BASE_URL", "https://agentic-rag-nexus.onrender.com/api/v1")
HEALTH_TIMEOUT = 10
DEFAULT_TIMEOUT = 30
UPLOAD_TIMEOUT = 120
STREAM_TIMEOUT = 120


class APIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def _request(method, endpoint, timeout=DEFAULT_TIMEOUT, retries=2, **kwargs):
    url = f"{API_BASE}{endpoint}"
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            last_error = APIError(f"Cannot connect (attempt {attempt}/{retries}).", status_code=0)
            if attempt < retries:
                time.sleep(5 * attempt)
        except requests.exceptions.Timeout:
            last_error = APIError(f"Timeout after {timeout}s.", status_code=0)
            if attempt < retries:
                time.sleep(5 * attempt)
        except requests.exceptions.HTTPError as e:
            raise APIError(f"HTTP {e.response.status_code}", status_code=e.response.status_code)
    raise last_error


def _safe_json(response):
    """Parse JSON, always return dict."""
    try:
        data = response.json()
        if isinstance(data, dict):
            return data
        elif isinstance(data, (list, tuple)) and len(data) > 0:
            # Try first element
            if isinstance(data[0], dict):
                return data[0]
            return {"raw_list": list(data), "error": "List response"}
        else:
            return {"raw": str(data), "error": "Unexpected format"}
    except Exception as e:
        return {"error": f"Parse failed: {str(e)}"}


def health_check():
    try:
        return _safe_json(_request("GET", "/health/health", timeout=HEALTH_TIMEOUT))
    except Exception as e:
        return {"status": "unhealthy", "detail": str(e)}


def upload_document(file, collection_name="documents"):
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"collection_name": collection_name}
    try:
        return _safe_json(_request("POST", "/upload/upload", files=files, data=data, timeout=UPLOAD_TIMEOUT))
    except APIError as e:
        return {"error": str(e)}


def list_documents():
    try:
        return _safe_json(_request("GET", "/upload/documents"))
    except Exception:
        return {"documents": []}


def create_session():
    try:
        return _safe_json(_request("POST", "/session/create"))
    except Exception:
        return {"session_id": "default"}


def get_session_status(session_id):
    """Get session — extra safe."""
    try:
        resp = _request("GET", f"/chat/session/{session_id}")
        result = _safe_json(resp)
        
        if not isinstance(result, dict):
            result = {}
        
        # Normalize nested state
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
    except Exception as e:
        return {
            "current_state": {},
            "generation": None,
            "human_approved": None,
            "critique_score": None,
            "critique_feedback": "",
            "error": str(e),
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
        raise APIError("Backend sleeping — wait 30s.")
    except requests.exceptions.Timeout:
        raise APIError("Stream timeout.")
    except requests.exceptions.HTTPError as e:
        raise APIError(f"HTTP {e.response.status_code}")


def approve_answer(session_id, decision, feedback=""):
    payload = {
        "session_id": session_id,
        "decision": decision,
        "feedback": feedback,
    }
    try:
        return _safe_json(_request("POST", "/chat/approve", json=payload))
    except Exception as e:
        return {"error": str(e)}