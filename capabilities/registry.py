# ingestion/pdf_loader.py

import fitz  # PyMuPDF


class PDFLoader:

    def load(self, file_path: str) -> str:
        """
        Returns raw text from PDF.
        Does NOT chunk or store.
        """
        doc = fitz.open(file_path)
        full_text = ""

        for page in doc:
            full_text += page.get_text()

        return full_text