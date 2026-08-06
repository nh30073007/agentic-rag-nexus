"""Document upload endpoint - Render OOM safe."""

import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, BackgroundTasks, HTTPException

from app.services.document_service import document_service
from app.services.vector_store_service import vectorstore_service
from app.db.session import SessionLocal
from app.db.models.document import DocumentModel

router = APIRouter()

# Job tracker (in-memory; use Redis in production)
_upload_jobs = {}


def _process_file_task(job_id: str, file_path: str, filename: str, collection_name: str):
    """Background task - OOM safe processing."""
    try:
        _upload_jobs[job_id]["status"] = "parsing"
        
        # Step 1: Parse (low memory)
        chunks = document_service.process_file(file_path, filename)
        _upload_jobs[job_id]["status"] = "embedding"
        _upload_jobs[job_id]["total_chunks"] = len(chunks)
        
        # Step 2: Extract texts
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        # Step 3: Embed & store (batch size 8, memory safe)
        vectorstore_service.add_documents(
            texts=texts,
            metadatas=metadatas,
            collection_name=collection_name,
        )
        
        # Step 4: Save metadata to DB
        db = SessionLocal()
        try:
            doc = DocumentModel(
                filename=filename,
                file_type=filename.split(".")[-1].lower(),
                file_size=os.path.getsize(file_path),
                collection_name=collection_name,
                chunk_count=len(chunks),
            )
            db.add(doc)
            db.commit()
        finally:
            db.close()
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            
        _upload_jobs[job_id]["status"] = "completed"
        _upload_jobs[job_id]["chunk_count"] = len(chunks)
        
    except Exception as e:
        _upload_jobs[job_id]["status"] = "failed"
        _upload_jobs[job_id]["error"] = str(e)
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_name: str = Form("documents"),
):
    """
    Upload document → immediate response → background processing.
    Prevents Render 30s timeout + 512MB OOM.
    """
    job_id = f"upload_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    
    # Save to /tmp (Render writable)
    temp_dir = "/tmp/uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{job_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")
    
    # File size check (Render has disk limits too)
    file_size = os.path.getsize(file_path)
    if file_size > 10 * 1024 * 1024:  # 10MB limit
        os.remove(file_path)
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    
    # Queue background job
    _upload_jobs[job_id] = {
        "status": "queued",
        "filename": file.filename,
        "file_size": file_size,
        "collection_name": collection_name,
    }
    
    background_tasks.add_task(
        _process_file_task,
        job_id,
        file_path,
        file.filename,
        collection_name,
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "File uploaded. Processing in background (10-30s).",
        "filename": file.filename,
        "file_size": file_size,
    }


@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str):
    """Check background upload status."""
    job = _upload_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    db = SessionLocal()
    try:
        docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
        return {
            "documents": [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "file_size": d.file_size,
                    "collection_name": d.collection_name,
                    "chunk_count": d.chunk_count,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in docs
            ]
        }
    finally:
        db.close()