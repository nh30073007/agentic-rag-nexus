"""Vector store service — FastEmbed."""

import os
import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

try:
    from langchain_community.embeddings import FastEmbedEmbeddings
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False

from app.core.config import settings
from app.core.exceptions import VectorStoreError


class VectorStoreService:
    def __init__(self):
        self.persist_dir = getattr(settings, 'CHROMA_PERSIST_DIR', './vectorstore')
        self.collection_name = getattr(settings, 'CHROMA_COLLECTION_NAME', 'documents')
        self._embeddings = None
        self._client = None

    def _get_embeddings(self):
        if self._embeddings is None:
            if not FASTEMBED_AVAILABLE:
                raise VectorStoreError("fastembed not installed")
            self._embeddings = FastEmbedEmbeddings(
                model_name="BAAI/bge-small-en-v1.5",
                cache_dir="./embeddings_cache",
                threads=2,
            )
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

    def add_documents(self, texts, metadatas=None, ids=None, collection_name=None):
        try:
            if not texts:
                return []
            collection = self._get_collection(collection_name)
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in texts]
            if metadatas is None:
                metadatas = [{} for _ in texts]
            embeddings = self._get_embeddings().embed_documents(texts)
            collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
            return ids
        except Exception as e:
            raise VectorStoreError(f"Failed to add: {str(e)}")

    def search(self, query, top_k=5, collection_name=None, filter_dict=None):
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
            for i in range(len(docs)):
                output.append({
                    "content": docs[i],
                    "metadata": mds[i] if i < len(mds) else {},
                    "score": float(1 - dists[i]) if i < len(dists) else 0.0,
                })
            return output
        except Exception as e:
            return []

    def get_all_documents(self, collection_name=None, limit=20):
        try:
            collection = self._get_collection(collection_name)
            results = collection.get(limit=limit, include=["documents", "metadatas"])
            output = []
            docs = results.get("documents", [])
            mds = results.get("metadatas", []) if results.get("metadatas") else []
            for i in range(len(docs)):
                output.append({
                    "content": docs[i],
                    "metadata": mds[i] if i < len(mds) else {},
                    "score": 1.0,
                })
            return output
        except Exception:
            return []

    def delete_collection(self, collection_name=None):
        try:
            client = self._get_client()
            name = collection_name or self.collection_name
            client.delete_collection(name=name)
        except Exception:
            pass

    def get_collection_stats(self, collection_name=None):
        try:
            collection = self._get_collection(collection_name)
            count = collection.count()
            return {"collection_name": collection_name or self.collection_name, "document_count": count}
        except Exception:
            return {"collection_name": collection_name or self.collection_name, "document_count": 0}

    def reset_collection(self, collection_name=None):
        """Delete and recreate empty collection."""
        try:
            name = collection_name or self.collection_name
            self.delete_collection(name)
            self._get_collection(name)
        except Exception as e:
            raise VectorStoreError(f"Reset failed: {str(e)}")


vectorstore_service = VectorStoreService()