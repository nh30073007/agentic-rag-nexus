"""Document upload endpoint."""

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError
from app.db.models.document import DocumentModel
from app.db.session import SessionLocal
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form(default="documents"),
):
    """
    Upload a document (PDF, DOCX, TXT) and store in vector DB.
    """
    # Validate file type
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    # Validate file size
    contents = await file.read()
    file_size = len(contents)
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="File too large")

    # Save temp file
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / f"{uuid.uuid4()}_{file.filename}"

    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        # Process and store
        doc_service = DocumentService()
        chunk_count, ids = doc_service.process_and_store(
            file_path=str(temp_path),
            filename=file.filename,
            file_type=file_ext,
            collection_name=collection_name,
        )

        # Save metadata to DB
        db = SessionLocal()
        try:
            doc_meta = DocumentModel(
                filename=file.filename,
                file_type=file_ext,
                file_size=file_size,
                collection_name=collection_name,
                chunk_count=chunk_count,
            )
            db.add(doc_meta)
            db.commit()
            db.refresh(doc_meta)

            return {
                "message": "Document uploaded successfully",
                "document_id": doc_meta.id,
                "filename": file.filename,
                "chunks": chunk_count,
                "collection": collection_name,
            }
        finally:
            db.close()

    except DocumentProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_path.exists():
            os.remove(temp_path)


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
                    "chunk_count": d.chunk_count,
                    "collection_name": d.collection_name,
                    "created_at": d.created_at,
                }
                for d in docs
            ],
            "total": len(docs),
        }
    finally:
        db.close()