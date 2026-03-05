# memory/knowledge_store.py

import os
import fitz  # PyMuPDF
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from memory.embedder import Embedder
from memory.vector_store import VectorStore


class KnowledgeStore:
    def __init__(self, persist_directory="nandhi_knowledge"):
        os.makedirs(persist_directory, exist_ok=True)
        # FIX: VectorStore now requires an embedding_model as first argument.
        # The original code passed only persist_directory which left embedding_model=None,
        # causing a RuntimeError on any add() or search() call.
        embedder = Embedder()
        self.vector_store = VectorStore(embedding_model=embedder, persist_directory=persist_directory)

    # -------- PDF Ingestion --------
    def ingest_pdf(self, file_path, user_id="default"):
        doc = fitz.open(file_path)
        for page in doc:
            text = page.get_text()
            if text:
                self.vector_store.add(text, metadata={"user_id": user_id, "source": file_path})

    # -------- EPUB Ingestion --------
    def ingest_epub(self, file_path, user_id="default"):
        book = epub.read_epub(file_path)
        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text = soup.get_text()
                if text:
                    self.vector_store.add(text, metadata={"user_id": user_id, "source": file_path})

    # -------- Raw Text Ingestion --------
    def ingest_text(self, text, user_id="default"):
        self.vector_store.add(text, metadata={"user_id": user_id})

    # -------- Semantic Search --------
    def search(self, query, k=5, user_id="default"):
        return self.vector_store.search(query, top_k=k)
