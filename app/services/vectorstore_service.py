"""Vector store service - Render Free Tier Optimized (No heavy models)."""

import os
import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.core.config import settings
from app.core.exceptions import VectorStoreError


class VectorStoreService:
    """Lightweight vector store - uses ChromaDB default embeddings (~20MB)."""

    def __init__(self):
        # ✅ Render-safe: /tmp path (writable ephemeral storage)
        self.persist_dir = getattr(settings, 'CHROMA_PERSIST_DIR', '/tmp/chroma_db')
        self.collection_name = getattr(settings, 'CHROMA_COLLECTION_NAME', 'documents')
        
        self._client = None
        self._embedding_fn = None

    def _get_embeddings(self):
        """ChromaDB default - tiny ONNX model, no download, ~20MB RAM."""
        if self._embedding_fn is None:
            self._embedding_fn = DefaultEmbeddingFunction()
        return self._embedding_fn

    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self, collection_name: Optional[str] = None):
        """Get or create collection."""
        client = self._get_client()
        name = collection_name or self.collection_name
        return client.get_or_create_collection(
            name=name,
            embedding_function=self._get_embeddings(),
        )

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        collection_name: Optional[str] = None,
    ) -> List[str]:
        """Add documents - memory safe batching."""
        try:
            if not texts:
                return []

            collection = self._get_collection(collection_name)
            
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in texts]
            if metadatas is None:
                metadatas = [{} for _ in texts]

            # ✅ Small batches to stay under 512MB
            batch_size = 8
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]
                
                collection.add(
                    documents=batch_texts,
                    metadatas=batch_metas,
                    ids=batch_ids,
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
        """Search similar documents."""
        try:
            collection = self._get_collection(collection_name)
            
            results = collection.query(
                query_texts=[query],
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
        """Delete a collection."""
        try:
            client = self._get_client()
            name = collection_name or self.collection_name
            client.delete_collection(name=name)
        except Exception as e:
            raise VectorStoreError(f"Failed to delete collection: {str(e)}")

    def get_collection_stats(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            collection = self._get_collection(collection_name)
            return {
                "collection_name": collection_name or self.collection_name,
                "document_count": collection.count(),
            }
        except Exception as e:
            raise VectorStoreError(f"Failed to get stats: {str(e)}")


# Singleton instance
vectorstore_service = VectorStoreService()