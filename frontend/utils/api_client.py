"""
HTTP client — all backend endpoints.
"""

import os
from typing import Optional, List, Dict, Any

import requests


# =========================================================
# CONFIG
# =========================================================

DEFAULT_API_BASE = (
    "https://agentic-rag-nexus.onrender.com/api/v1"
)

API_BASE = os.getenv(
    "API_BASE_URL",
    DEFAULT_API_BASE,
).rstrip("/")


print(f"🔗 Backend API: {API_BASE}")

# =========================================================
# INTERNAL REQUEST HELPER
# =========================================================

def _get_json(
    response: requests.Response,
) -> Optional[Dict[str, Any]]:
    """
    Safely return JSON response.

    Returns None if the backend sends invalid JSON.
    """

    try:
        return response.json()
    except ValueError:
        return None


# =========================================================
# DOCUMENT API
# =========================================================

def upload_document(
    file,
    collection_name: str = "documents",
) -> Optional[Dict[str, Any]]:
    """Upload a document to the backend."""

    try:

        files = {
            "file": (
                file.name,
                file.getvalue(),
                file.type,
            )
        }

        data = {
            "collection_name": collection_name,
        }

        response = requests.post(
            f"{API_BASE}/upload/upload",
            files=files,
            data=data,
            timeout=60,
        )

        if response.status_code == 200:
            return _get_json(response)

        print(
            "Upload failed:",
            response.status_code,
            response.text,
        )

        return None

    except requests.RequestException as e:

        print(f"Upload error: {e}")

        return None

    except Exception as e:

        print(f"Unexpected upload error: {e}")

        return None


def list_documents() -> List[Dict[str, Any]]:
    """Get all uploaded documents."""

    try:

        response = requests.get(
            f"{API_BASE}/upload/documents",
            timeout=5,
        )

        if response.status_code == 200:

            data = _get_json(response)

            if data:
                return data.get(
                    "documents",
                    [],
                )

        return []

    except requests.RequestException as e:

        print(f"List documents error: {e}")

        return []

    except Exception as e:

        print(
            f"Unexpected document error: {e}"
        )

        return []


def get_collection_stats(
    collection_name: str = "documents",
) -> Optional[Dict[str, Any]]:
    """Get vector collection statistics."""

    try:

        response = requests.get(
            f"{API_BASE}/upload/collection/stats",
            params={
                "collection_name": collection_name,
            },
            timeout=5,
        )

        if response.status_code == 200:
            return _get_json(response)

        return None

    except requests.RequestException as e:

        print(f"Collection stats error: {e}")

        return None

    except Exception as e:

        print(
            f"Unexpected collection stats error: {e}"
        )

        return None


# =========================================================
# CHAT API
# =========================================================

def chat_ask(
    query: str,
    session_id: str,
    collection_name: str = "documents",
) -> Optional[Dict[str, Any]]:
    """
    Send a chat message.

    The backend automatically:
    - Creates history for a new session_id
    - Saves user query
    - Saves AI response
    - Keeps the conversation persistent
    """

    try:

        payload = {
            "query": query,
            "session_id": session_id,
            "collection_name": collection_name,
        }

        response = requests.post(
            f"{API_BASE}/chat/ask",
            json=payload,
            timeout=130,
        )

        if response.status_code == 200:
            return _get_json(response)

        print(
            "Chat failed:",
            response.status_code,
            response.text,
        )

        return None

    except requests.Timeout:

        print(
            "Chat request timed out."
        )

        return {
            "error": (
                "Request timed out. "
                "The AI model may still be loading."
            )
        }

    except requests.RequestException as e:

        print(f"Chat error: {e}")

        return None

    except Exception as e:

        print(
            f"Unexpected chat error: {e}"
        )

        return None


# =========================================================
# CONVERSATION HISTORY API
# =========================================================

def get_conversations(
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Get all saved conversations.

    Used by the sidebar to show:

    TODAY
    YESTERDAY
    OLDER
    """

    try:

        response = requests.get(
            f"{API_BASE}/chat/conversations",
            params={
                "limit": limit,
            },
            timeout=10,
        )

        if response.status_code == 200:

            data = _get_json(response)

            if data:
                return data.get(
                    "conversations",
                    [],
                )

        print(
            "Failed to load conversations:",
            response.status_code,
            response.text,
        )

        return []

    except requests.RequestException as e:

        print(
            f"Conversation list error: {e}"
        )

        return []

    except Exception as e:

        print(
            f"Unexpected conversation error: {e}"
        )

        return []


def get_conversation(
    session_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Load one complete conversation.

    Returns:

    {
        "session_id": "...",
        "title": "...",
        "messages": [
            {
                "role": "user",
                "content": "Hello"
            },
            {
                "role": "assistant",
                "content": "Hi..."
            }
        ]
    }
    """

    if not session_id:
        return None

    try:

        response = requests.get(
            f"{API_BASE}/chat/conversations/{session_id}",
            timeout=10,
        )

        if response.status_code == 200:
            return _get_json(response)

        print(
            "Failed to load conversation:",
            response.status_code,
            response.text,
        )

        return None

    except requests.RequestException as e:

        print(
            f"Load conversation error: {e}"
        )

        return None

    except Exception as e:

        print(
            f"Unexpected load error: {e}"
        )

        return None


def delete_conversation(
    session_id: str,
) -> bool:
    """
    Delete a complete conversation.

    Returns True if successfully deleted.
    """

    if not session_id:
        return False

    try:

        response = requests.delete(
            f"{API_BASE}/chat/conversations/{session_id}",
            timeout=10,
        )

        if response.status_code == 200:

            data = _get_json(response)

            if data:
                return data.get(
                    "success",
                    False,
                )

        print(
            "Delete conversation failed:",
            response.status_code,
            response.text,
        )

        return False

    except requests.RequestException as e:

        print(
            f"Delete conversation error: {e}"
        )

        return False

    except Exception as e:

        print(
            f"Unexpected delete error: {e}"
        )

        return False


# =========================================================
# BACKEND HEALTH API
# =========================================================

def backend_health_check() -> Optional[Dict[str, Any]]:
    """
    Check whether the FastAPI backend is alive.

    Endpoint:
        GET /api/v1/health
    """

    try:

        response = requests.get(
            f"{API_BASE}/health",
            timeout=10,
        )

        if response.status_code == 200:

            return _get_json(response)

        print(
            "Backend health check failed:",
            response.status_code,
            response.text,
        )

        return None

    except requests.RequestException as e:

        print(
            f"Backend health error: {e}"
        )

        return None

    except Exception as e:

        print(
            f"Unexpected backend health error: {e}"
        )

        return None


# =========================================================
# LLM HEALTH API
# =========================================================

def llm_health_check() -> Optional[Dict[str, Any]]:
    """
    Check whether the configured LLM service is available.

    Endpoint:
        GET /api/v1/chat/health/llm
    """

    try:

        response = requests.get(
            f"{API_BASE}/chat/health/llm",
            timeout=10,
        )

        if response.status_code == 200:
            return _get_json(response)

        print(
            "LLM health check failed:",
            response.status_code,
            response.text,
        )

        return None

    except requests.RequestException as e:

        print(
            f"LLM health error: {e}"
        )

        return None

    except Exception as e:

        print(
            f"Unexpected LLM health error: {e}"
        )

        return None


# =========================================================
# BACKWARD-COMPATIBLE HEALTH API
# =========================================================

def health_check() -> Optional[Dict[str, Any]]:
    """
    Backward-compatible health check.

    This now checks the FastAPI backend itself instead of
    the LLM-specific endpoint.

    This is intentionally kept under the original function
    name so existing frontend code continues to work.
    """

    return backend_health_check()


# =========================================================
# HUMAN APPROVAL API
# =========================================================

def approve_answer(
    session_id: str,
    decision: str,
    feedback: str = "",
) -> Optional[Dict[str, Any]]:
    """Approve or reject an AI answer."""

    try:

        payload = {
            "session_id": session_id,
            "decision": decision,
            "feedback": feedback,
        }

        response = requests.post(
            f"{API_BASE}/chat/approve",
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            return _get_json(response)

        print(
            "Approval request failed:",
            response.status_code,
            response.text,
        )

        return None

    except requests.RequestException as e:

        print(f"Approval error: {e}")

        return None

    except Exception as e:

        print(
            f"Unexpected approval error: {e}"
        )

        return None