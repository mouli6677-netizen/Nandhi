# memory/document_loader.py

import fitz  # PyMuPDF
from ebooklib import epub
from bs4 import BeautifulSoup
import os


class DocumentLoader:

    @staticmethod
    def load_pdf(path: str) -> str:
        text = ""
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()
        return text

    @staticmethod
    def load_epub(path: str) -> str:
        book = epub.read_epub(path)
        text = ""
        for item in book.get_items():
            if item.get_type() == 9:  # DOCUMENT
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text += soup.get_text()
        return text

    @staticmethod
    def load_documents(folder_path: str) -> dict:
        documents = {}
        for file in os.listdir(folder_path):
            full_path = os.path.join(folder_path, file)

            if file.endswith(".pdf"):
                documents[file] = DocumentLoader.load_pdf(full_path)

            elif file.endswith(".epub"):
                documents[file] = DocumentLoader.load_epub(full_path)

        return documents