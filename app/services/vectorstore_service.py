"""Vector store service — Google Gemini embeddings (FREE tier)."""

import os
import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

# ✅ Google Gemini — free tier, 1500 requests/day, no credit card
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from app.core.config import settings
from app.core.exceptions import VectorStoreError


class VectorStoreService:
    """Google Gemini embeddings — completely free."""

    def __init__(self):
        self.persist_dir = getattr(settings, 'CHROMA_PERSIST_DIR', '/tmp/chroma_db')
        self.collection_name = getattr(settings, 'CHROMA_COLLECTION_NAME', 'documents')
        self._embeddings = None
        self._client = None

    def _get_embeddings(self):
        if self._embeddings is None:
            if not GOOGLE_AVAILABLE:
                raise VectorStoreError("langchain-google-genai not installed. Run: pip install langchain-google-genai")

            # ✅ Read from env or settings
            api_key = os.getenv("GOOGLE_API_KEY") or getattr(settings, 'GOOGLE_API_KEY', None)
            
            if not api_key:
                raise VectorStoreError(
                    "GOOGLE_API_KEY not set.\n"
                    "1. Go to: https://aistudio.google.com/app/apikey\n"
                    "2. Click 'Create API key'\n"
                    "3. Copy the key\n"
                    "4. Add to Render: Dashboard → Environment → GOOGLE_API_KEY=AIzaSy..."
                )

            self._embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=api_key,
            )
            print("✅ Google Gemini embeddings initialized (FREE TIER)")
        return self._embeddings

    def _get_client(self):
        if self._client is None:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self, collection_name: Optional[str] = None):
        client = self._get_client()
        name = collection_name or self.collection_name
        return client.get_or_create_collection(name=name)

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        collection_name: Optional[str] = None,
    ) -> List[str]:
        try:
            if not texts:
                return []

            collection = self._get_collection(collection_name)
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in texts]
            if metadatas is None:
                metadatas = [{} for _ in texts]

            embeddings = self._get_embeddings().embed_documents(texts)

            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
            return ids
        except Exception as e:
            raise VectorStoreError(f"Failed to add documents: {str(e)}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        collection_name: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            collection = self._get_collection(collection_name)
            query_embedding = self._get_embeddings().embed_query(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict,
                include=["documents", "metadatas", "distances"],
            )
            
            output = []
            docs = results.get("documents", [[]])[0]
            mds = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            dists = results.get("distances", [[]])[0] if results.get("distances") else []
            
            if docs:
                for i in range(len(docs)):
                    output.append({
                        "content": docs[i],
                        "metadata": mds[i] if i < len(mds) else {},
                        "score": float(dists[i]) if i < len(dists) else 0.0,
                    })
            return output
        except Exception as e:
            raise VectorStoreError(f"Search failed: {str(e)}")

    def delete_collection(self, collection_name: Optional[str] = None) -> None:
        try:
            client = self._get_client()
            name = collection_name or self.collection_name
            client.delete_collection(name=name)
        except Exception as e:
            raise VectorStoreError(f"Failed to delete collection: {str(e)}")

    def get_collection_stats(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        try:
            collection = self._get_collection(collection_name)
            return {
                "collection_name": collection_name or self.collection_name,
                "document_count": collection.count(),
            }
        except Exception as e:
            raise VectorStoreError(f"Failed to get stats: {str(e)}")


vectorstore_service = VectorStoreService()