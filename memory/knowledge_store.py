import os
import fitz  # FIX: was PyPDF2 (deprecated) — use PyMuPDF (fitz) like document_loader.py
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from memory.vector_store import VectorStore

class KnowledgeStore:
    def __init__(self, persist_directory="nandhi_knowledge"):
        os.makedirs(persist_directory, exist_ok=True)
        self.vector_store = VectorStore(persist_directory=persist_directory)

    # -------- PDF Ingestion --------
    def ingest_pdf(self, file_path, user_id="default"):
        # FIX: replaced PyPDF2.PdfReader with fitz (PyMuPDF)
        doc = fitz.open(file_path)
        for page in doc:
            text = page.get_text()
            if text:
                self.vector_store.add(text, metadata={"user_id": user_id})

    # -------- EPUB Ingestion --------
    def ingest_epub(self, file_path, user_id="default"):
        book = epub.read_epub(file_path)
        for item in book.get_items():
            # FIX: epub.EpubHtml is a class, not a type constant — use ITEM_DOCUMENT (==9)
            if item.get_type() == ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text = soup.get_text()
                if text:
                    self.vector_store.add(text, metadata={"user_id": user_id})

    # -------- Raw Text Ingestion (Web or manual) --------
    def ingest_text(self, text, user_id="default"):
        self.vector_store.add(text, metadata={"user_id": user_id})

    # -------- Semantic Search --------
    def search(self, query, k=5, user_id="default"):
        return self.vector_store.search(query, k=k)
