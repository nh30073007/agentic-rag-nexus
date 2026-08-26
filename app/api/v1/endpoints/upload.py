"""Document upload endpoint — with clear support."""

import os
import time
import uuid
import logging

from fastapi import APIRouter, File, Form, UploadFile, BackgroundTasks, HTTPException

from app.services.document_service import document_service
from app.services.vectorstore_service import vectorstore_service
from app.db.session import SessionLocal
from app.db.models.document import DocumentModel

router = APIRouter()
logger = logging.getLogger(__name__)

_upload_jobs = {}


def _process_file_task(job_id: str, file_path: str, filename: str, collection_name: str):
    try:
        _upload_jobs[job_id]["status"] = "parsing"
        chunks = document_service.process_file(file_path, filename)
        _upload_jobs[job_id]["status"] = "embedding"
        _upload_jobs[job_id]["total_chunks"] = len(chunks)

        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        vectorstore_service.add_documents(
            texts=texts,
            metadatas=metadatas,
            collection_name=collection_name,
        )

        db = SessionLocal()
        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            doc = DocumentModel(
                filename=filename,
                file_type=filename.split(".")[-1].lower(),
                file_size=file_size,
                collection_name=collection_name,
                chunk_count=len(chunks),
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
        except Exception as e:
            db.rollback()
            logger.error(f"DB error: {e}")
        finally:
            db.close()

        if os.path.exists(file_path):
            os.remove(file_path)

        _upload_jobs[job_id]["status"] = "completed"
        _upload_jobs[job_id]["chunk_count"] = len(chunks)

    except Exception as e:
        logger.error(f"Upload job {job_id} failed: {e}")
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
    job_id = f"upload_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    temp_dir = "/tmp/uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{job_id}_{file.filename}")

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")

    file_size = os.path.getsize(file_path)
    if file_size > 10 * 1024 * 1024:
        os.remove(file_path)
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

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
        "message": "File uploaded. Processing in background.",
        "filename": file.filename,
    }


@router.post("/clear")
async def clear_collection(collection_name: str = Form("documents")):
    """Clear all documents from a collection."""
    try:
        vectorstore_service.reset_collection(collection_name)
        return {"status": "cleared", "collection_name": collection_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str):
    job = _upload_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/documents")
async def list_documents():
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


@router.get("/collection/stats")
async def collection_stats(collection_name: str = "documents"):
    return vectorstore_service.get_collection_stats(collection_name)