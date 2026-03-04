import os
import time
import logging
from ingestion.pdf_loader import PDFLoader
from ingestion.epub_loader import EPUBLoader
from memory.chunker import chunk_text

def watch_knowledge_folder(engine, folder="Knowledge", poll_interval=10):
    """
    Continuously monitor the Knowledge folder for new PDFs/EPUBs.
    Only ingest new or modified chunks.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    pdf_loader = PDFLoader(engine.vector_store)
    epub_loader = EPUBLoader(engine.vector_store)

    while True:
        try:
            for fname in os.listdir(folder):
                if not fname.lower().endswith((".pdf", ".epub")):
                    continue

                path = os.path.join(folder, fname)
                # Load chapters
                if fname.lower().endswith(".pdf"):
                    chapters = pdf_loader.load(path)
                else:
                    chapters = epub_loader.load(path)

                total_new_chunks = 0
                for chap in chapters:
                    metadata = {"file": fname, "chapter": chap.get("number"), "title": chap.get("title")}
                    chunks = chunk_text(chap.get("content", ""))
                    for chunk in chunks:
                        if not engine.vector_store.has_chunk(fname, chunk):
                            engine.vector_store.add(chunk, metadata)
                            total_new_chunks += 1

                if total_new_chunks:
                    logging.info(f"Incrementally ingested {total_new_chunks} new chunks from {fname}")

        except Exception as e:
            logging.error(f"Knowledge watcher error: {e}")

        time.sleep(poll_interval)