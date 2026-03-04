class MemoryAgent:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(self, query):
        return self.vector_store.search(query)