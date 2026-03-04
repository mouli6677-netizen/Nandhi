import os
import re
import logging
import PyPDF2
from memory.vector_store import VectorStore
from memory.chunker import chunk_text  # make sure you have a chunker function

class PDFLoader:
    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store

    def load(self, file_path: str):
        """Load PDF and split into chapters."""
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"

        chapters = []
        split_pattern = re.compile(r"(Chapter\s+\d+)", re.IGNORECASE)
        parts = split_pattern.split(text)

        if len(parts) <= 1:
            # No chapters detected
            chapters.append({"number": 1, "title": "Full Text", "content": text})
        else:
            for i in range(1, len(parts), 2):
                title = parts[i].strip()
                content = parts[i + 1].strip() if (i + 1) < len(parts) else ""
                chap_number_match = re.search(r"\d+", title)
                chap_number = int(chap_number_match.group()) if chap_number_match else i // 2 + 1
                chapters.append({"number": chap_number, "title": title, "content": content})

        return chapters

    def ingest(self, file_path: str, user_id="default"):
        """Ingest PDF into vector store, chunking text per chapter."""
        if not self.vector_store:
            return 0
        chapters = self.load(file_path)
        total_chunks = 0

        for chap in chapters:
            chunks = chunk_text(chap["content"])
            for chunk in chunks:
                if not self.vector_store.exists(file_path):
                    self.vector_store.add(
                        text=chunk,
                        metadata={
                            "file": os.path.basename(file_path),
                            "chapter": chap["number"],
                            "title": chap["title"]
                        }
                    )
                    total_chunks += 1

        logging.info(f"[PDFLoader] Ingested {total_chunks} chunks from {os.path.basename(file_path)}")
        return total_chunks