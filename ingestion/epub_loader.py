# ingestion/epub_loader.py
from memory.chunker import chunk_text
from ebooklib import epub
from bs4 import BeautifulSoup
import os

class EPUBLoader:
    def __init__(self, vector_store=None):
        self.vector_store = vector_store

    def load(self, file_path):
        """
        Returns a list of chapters:
        Each chapter = {"number": n, "title": "Title", "content": "Text"}
        """
        book = epub.read_epub(file_path)
        chapters = []
        chap_num = 1

        for item in book.get_items():
            # New way to detect document items
            if isinstance(item, epub.EpubHtml):
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text = soup.get_text()
                title = item.get_name() or f"Chapter {chap_num}"
                chapters.append({"number": chap_num, "title": title, "content": text})
                chap_num += 1

        return chapters

    def ingest(self, file_path, user_id="default"):
        chapters = self.load(file_path)
        total_chunks = 0
        for chap in chapters:
            chunks = chunk_text(chap["content"])
            for chunk in chunks:
                if self.vector_store:
                    self.vector_store.add(chunk, metadata={
                        "chapter": chap["number"],
                        "title": chap["title"],
                        "file": os.path.basename(file_path)
                    })
                    total_chunks += 1
        return total_chunks