"""Vector store service — PERMANENT FIX: fastembed (no API key, 33MB model)."""

import os
import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

# ✅ PERMANENT FIX: fastembed — 33MB model, no API key, CPU only
try:
    from langchain_community.embeddings import FastEmbedEmbeddings
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False

from app.core.config import settings
from app.core.exceptions import VectorStoreError


class VectorStoreService:
    """FastEmbed — permanent solution. No API key, no credits, no OOM."""

    def __init__(self):
        self.persist_dir = getattr(settings, 'CHROMA_PERSIST_DIR', '/tmp/chroma_db')
        self.collection_name = getattr(settings, 'CHROMA_COLLECTION_NAME', 'documents')
        self._embeddings = None
        self._client = None

    def _get_embeddings(self):
        if self._embeddings is None:
            if not FASTEMBED_AVAILABLE:
                raise VectorStoreError(
                    "fastembed not installed. "
                    "Add 'fastembed==0.4.0' to requirements.txt"
                )

            # ✅ BAAI/bge-small-en-v1.5 = 33MB, excellent quality, CPU only
            self._embeddings = FastEmbedEmbeddings(
                model_name="BAAI/bge-small-en-v1.5",
                cache_dir="/tmp/fastembed_cache",  # Render writable
                threads=2,  # Limit CPU usage on free tier
            )
            print("✅ FastEmbed initialized (BAAI/bge-small-en-v1.5, 33MB, no API key)")
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