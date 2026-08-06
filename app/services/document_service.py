"""Document processing - memory optimized for Render."""

import os
from typing import List, Dict, Any

from pypdf import PdfReader


class DocumentService:
    """Process documents with low memory footprint."""

    def process_file(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Process file and return chunks."""
        ext = filename.split(".")[-1].lower()
        
        if ext == "pdf":
            return self._process_pdf(file_path, filename)
        elif ext == "txt":
            return self._process_txt(file_path, filename)
        elif ext in ["docx", "doc"]:
            return self._process_docx(file_path, filename)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _process_pdf(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Process PDF page by page (low memory)."""
        chunks = []
        reader = PdfReader(file_path)
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                chunks.append({
                    "text": text.strip(),
                    "metadata": {
                        "source": filename,
                        "page": page_num + 1,
                        "type": "pdf",
                    }
                })
        return chunks

    def _process_txt(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Process TXT file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        
        # Simple chunking by paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return [
            {
                "text": p,
                "metadata": {"source": filename, "type": "txt"}
            }
            for p in paragraphs
        ]

    def _process_docx(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Process DOCX file."""
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            
            return [
                {
                    "text": p,
                    "metadata": {"source": filename, "type": "docx"}
                }
                for p in paragraphs
            ]
        except ImportError:
            raise ValueError("python-docx not installed")


# Singleton
document_service = DocumentService()