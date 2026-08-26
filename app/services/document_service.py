"""Document processing service - PDF, DOCX, TXT parsing."""

import os
import tempfile
from typing import List, Dict, Any, Union

from pypdf import PdfReader
from docx import Document
import markdown


class DocumentService:
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200

    def process_file(self, file_input: Union[str, bytes], filename: str) -> List[Dict[str, Any]]:
        """Process uploaded file and return chunks. Accepts file path or bytes."""
        ext = filename.split(".")[-1].lower()
        
        # ✅ FIX: Handle both file path (str) and file content (bytes)
        if isinstance(file_input, str):
            # It's a file path
            with open(file_input, 'rb') as f:
                file_content = f.read()
        else:
            file_content = file_input
        
        if ext == "pdf":
            text = self._read_pdf(file_content)
        elif ext == "docx":
            text = self._read_docx(file_content)
        elif ext == "txt":
            text = self._read_txt(file_content)
        elif ext == "md":
            text = self._read_md(file_content)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        # Chunk the text
        chunks = self._chunk_text(text)
        
        # Add metadata
        return [
            {
                "text": chunk,
                "metadata": {
                    "source": filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
            }
            for i, chunk in enumerate(chunks)
        ]

    def _read_pdf(self, content: bytes) -> str:
        """Read PDF file from bytes."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            reader = PdfReader(tmp_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            os.unlink(tmp_path)
            return text
        except Exception as e:
            raise Exception(f"PDF reading failed: {str(e)}")

    def _read_docx(self, content: bytes) -> str:
        """Read DOCX file from bytes."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            doc = Document(tmp_path)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            
            os.unlink(tmp_path)
            return text
        except Exception as e:
            raise Exception(f"DOCX reading failed: {str(e)}")

    def _read_txt(self, content: bytes) -> str:
        """Read TXT file."""
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1")

    def _read_md(self, content: bytes) -> str:
        """Read Markdown file."""
        try:
            text = content.decode("utf-8")
            html = markdown.markdown(text)
            import re
            text = re.sub(r'<[^>]+>', '', html)
            return text
        except Exception as e:
            raise Exception(f"Markdown reading failed: {str(e)}")

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        words = text.split()
        chunks = []
        step = self.chunk_size - self.chunk_overlap
        
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks


# Singleton
document_service = DocumentService()