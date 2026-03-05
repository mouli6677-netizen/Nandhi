# memory/vector_store.py

import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:
    def __init__(self, embedding_model=None, store_path="memory_store.json", persist_directory=None):
        """
        FIX 1: Original constructor only accepted (embedding_model, store_path).
        knowledge_store.py calls VectorStore(persist_directory=...) with no
        embedding_model, which crashed with a TypeError.  Made embedding_model
        optional and handle persist_directory as an alias for store_path.

        FIX 2: exists() method was missing entirely even though it is called
        from pdf_loader, epub_loader, auto_pipeline, and file_watcher.
        """
        self.embedding_model = embedding_model

        # Support persist_directory as an alternative path argument
        if persist_directory is not None:
            store_path = os.path.join(persist_directory, "memory_store.json")

        self.store_path = store_path
        self.store = []
        self._load()

    def _load(self):
        if os.path.exists(self.store_path):
            with open(self.store_path, "r", encoding="utf-8") as f:
                self.store = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.store_path) or ".", exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.store, f, ensure_ascii=False, indent=2)

    def add(self, text, metadata=None):
        if self.embedding_model is None:
            raise RuntimeError("VectorStore.add() requires an embedding_model.")
        vector = self.embedding_model.embed([text])[0].tolist()
        self.store.append({
            "text": text,
            "vector": vector,
            "metadata": metadata or {}
        })
        self._save()

    def search(self, query, top_k=5):
        if not self.store:
            return []
        if self.embedding_model is None:
            raise RuntimeError("VectorStore.search() requires an embedding_model.")

        query_vec = self.embedding_model.embed([query])[0]
        vectors = [item["vector"] for item in self.store]
        sims = cosine_similarity([query_vec], vectors)[0]
        top_indices = np.argsort(sims)[-top_k:][::-1]
        return [self.store[i] for i in top_indices]

    def exists(self, source: str) -> bool:
        """
        FIX: This method was completely missing. Called by PDFLoader, EPUBLoader,
        auto_pipeline, and file_watcher to avoid re-ingesting the same file or URL.
        Checks whether any stored entry has a matching 'source' or 'url' in metadata,
        or matches the text field directly (for URL-based entries).
        """
        source_lower = source.lower()
        for item in self.store:
            meta = item.get("metadata", {})
            if (
                meta.get("source", "").lower() == source_lower
                or meta.get("url", "").lower() == source_lower
                or meta.get("file", "").lower() == os.path.basename(source_lower)
            ):
                return True
        return False
