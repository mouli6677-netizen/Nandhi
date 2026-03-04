# memory/retriever.py

class Retriever:

    def __init__(self, embedder, vector_store):
        self.embedder = embedder
        self.vector_store = vector_store

    def query(self, question: str, top_k=5):
        # FIX: was embedding the query here then passing a vector to search(),
        # but vector_store.search() expects a raw string and embeds it internally.
        # Removed double-embedding — pass the string directly.
        results = self.vector_store.search(question, top_k)
        return results
