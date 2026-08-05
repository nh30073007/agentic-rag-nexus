"""Document processing service."""

import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from docx import Document as DocxDocument

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError
from app.services.vectorstore_service import vectorstore_service


class DocumentService:
    """Service for parsing and processing documents."""

    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            raise DocumentProcessingError(f"PDF parsing failed: {str(e)}")

    def parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX."""
        try:
            doc = DocxDocument(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            raise DocumentProcessingError(f"DOCX parsing failed: {str(e)}")

    def parse_txt(self, file_path: str) -> str:
        """Read text file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise DocumentProcessingError(f"TXT reading failed: {str(e)}")

    def parse_file(self, file_path: str, file_type: str) -> str:
        """Parse file based on type."""
        ext = file_type.lower()
        if ext == "pdf":
            return self.parse_pdf(file_path)
        elif ext in ["docx", "doc"]:
            return self.parse_docx(file_path)
        elif ext == "txt":
            return self.parse_txt(file_path)
        else:
            raise DocumentProcessingError(f"Unsupported file type: {ext}")

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        return self.text_splitter.split_text(text)

    def process_and_store(
        self,
        file_path: str,
        filename: str,
        file_type: str,
        collection_name: Optional[str] = None,
    ) -> Tuple[int, List[str]]:
        """
        Full pipeline: parse -> chunk -> embed -> store.
        Returns (chunk_count, ids).
        """
        # 1. Parse
        raw_text = self.parse_file(file_path, file_type)

        if not raw_text.strip():
            raise DocumentProcessingError("No text extracted from document")

        # 2. Chunk
        chunks = self.chunk_text(raw_text)

        if not chunks:
            raise DocumentProcessingError("No chunks generated from document")

        # 3. Prepare metadata
        metadatas = []
        ids = []
        base_id = str(uuid.uuid4())
        for i, chunk in enumerate(chunks):
            metadatas.append({
                "source": filename,
                "file_type": file_type,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "doc_id": base_id,
            })
            ids.append(f"{base_id}_{i}")

        # 4. Store in vector DB
        stored_ids = vectorstore_service.add_documents(
            texts=chunks,
            metadatas=metadatas,
            ids=ids,
            collection_name=collection_name,
        )

        return len(chunks), stored_ids


# Singleton instance
document_service = DocumentService()