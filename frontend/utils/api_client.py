"""HTTP client for FastAPI backend."""

import json

import requests
import streamlit as st

API_BASE = "http://localhost:8000/api/v1"


def upload_document(file, collection_name="documents"):
    """Upload a document to the backend."""
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"collection_name": collection_name}
    response = requests.post(f"{API_BASE}/upload/upload", files=files, data=data)
    return response.json() if response.status_code == 201 else {"error": response.text}


def list_documents():
    """List all uploaded documents."""
    response = requests.get(f"{API_BASE}/upload/documents")
    return response.json() if response.status_code == 200 else {"documents": []}


def create_session():
    """Create a new chat session."""
    response = requests.post(f"{API_BASE}/session/create")
    return response.json() if response.status_code == 200 else {}


def get_session_history(session_id):
    """Get chat history."""
    response = requests.get(f"{API_BASE}/session/{session_id}/history")
    return response.json() if response.status_code == 200 else {"history": []}


def send_chat_stream(query, session_id, collection_name="documents"):
    """Send chat query and return SSE stream."""
    payload = {
        "query": query,
        "session_id": session_id,
        "collection_name": collection_name,
    }
    response = requests.post(
        f"{API_BASE}/chat/stream",  # FIXED: was /chat/chat/stream
        json=payload,
        stream=True,
    )
    return response


def approve_answer(session_id, decision, feedback=""):
    """Send human approval/rejection."""
    payload = {
        "session_id": session_id,
        "decision": decision,
        "feedback": feedback,
    }
    response = requests.post(f"{API_BASE}/chat/approve", json=payload)
    return response.json() if response.status_code == 200 else {"error": response.text}


def get_session_status(session_id):
    """Get current session state."""
    response = requests.get(f"{API_BASE}/chat/session/{session_id}")
    return response.json() if response.status_code == 200 else {}