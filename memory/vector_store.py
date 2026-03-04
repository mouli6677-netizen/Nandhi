import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class VectorStore:
    def __init__(self, embedding_model, store_path="memory_store.json"):
        self.embedding_model = embedding_model
        self.store_path = store_path
        self.store = []
        self._load()

    def _load(self):
        if os.path.exists(self.store_path):
            with open(self.store_path, "r", encoding="utf-8") as f:
                self.store = json.load(f)

    def _save(self):
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.store, f, ensure_ascii=False, indent=2)

    def add(self, text, metadata=None):
        # FIX: was .encode(text) — Embedder exposes .embed(), not .encode()
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

        # FIX: was .encode(query) — use .embed() consistently
        query_vec = self.embedding_model.embed([query])[0]
        vectors = [item["vector"] for item in self.store]

        sims = cosine_similarity([query_vec], vectors)[0]
        top_indices = np.argsort(sims)[-top_k:][::-1]

        return [self.store[i] for i in top_indices]
