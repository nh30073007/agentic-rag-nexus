"""Vector store service using ChromaDB directly."""

import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings
from app.core.exceptions import VectorStoreError


class VectorStoreService:
    """Service for vector database operations."""

    def __init__(self):
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self._embeddings = None
        self._client = None

    def _get_embeddings(self):
        """Lazy load embeddings model."""
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embeddings

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
        return client.get_or_create_collection(name=name)

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        collection_name: Optional[str] = None,
    ) -> List[str]:
        """Add documents to vector store."""
        try:
            collection = self._get_collection(collection_name)
            embeddings = self._get_embeddings().embed_documents(texts)
            
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in texts]
            
            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas or [{} for _ in texts],
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
        """Search similar documents."""
        try:
            collection = self._get_collection(collection_name)
            query_embedding = self._get_embeddings().embed_query(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict,
            )
            
            output = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    output.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": float(results["distances"][0][i]) if results["distances"] else 0.0,
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