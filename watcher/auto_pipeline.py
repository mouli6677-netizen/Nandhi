import os
import time
import logging
import threading
from ingestion.pdf_loader import PDFLoader
from ingestion.epub_loader import EPUBLoader
from ingestion.web_loader import WebLoader

# Map topics to actual URLs
TOPIC_URLS = {
    "technology": "https://www.techcrunch.com/",
    "AI": "https://blog.google/innovation-and-ai/technology/ai/",
    "science": "https://www.sciencedaily.com/",
    "finance": "https://www.bloomberg.com/asia",
    "health": "https://www.medicalnewstoday.com/"
}


def auto_ingest_documents(engine):
    """Automatically ingest PDFs & EPUBs from Knowledge folder."""
    knowledge_path = os.path.join(os.getcwd(), "Knowledge")
    os.makedirs(knowledge_path, exist_ok=True)

    pdf_loader = PDFLoader(engine.vector_store)
    epub_loader = EPUBLoader(engine.vector_store)

    while True:
        try:
            # PDFs
            for fname in os.listdir(knowledge_path):
                if fname.lower().endswith(".pdf"):
                    file_path = os.path.join(knowledge_path, fname)
                    if not engine.vector_store.exists(file_path):
                        chunks = engine.ingest_pdf(file_path)
                        logging.info(f"[PDF] Auto-ingested {chunks} chunks from {fname}")

            # EPUBs
            for fname in os.listdir(knowledge_path):
                if fname.lower().endswith(".epub"):
                    file_path = os.path.join(knowledge_path, fname)
                    if not engine.vector_store.exists(file_path):
                        chunks = engine.ingest_epub(file_path)
                        logging.info(f"[EPUB] Auto-ingested {chunks} chunks from {fname}")

        except Exception as e:
            logging.error(f"Auto-ingest error: {e}")

        time.sleep(60)  # repeat every 1 minute


def auto_web_surf(engine):
    """Automatically ingest web content, skip blocked URLs, log usable ones."""
    web_loader = WebLoader(engine.vector_store)

    while True:
        for topic, url in TOPIC_URLS.items():
            try:
                # Skip if already ingested
                if engine.vector_store.exists(url):
                    continue

                text = web_loader.load(url)
                if not text.strip():
                    logging.info(f"[Web] Skipped empty content for topic: {topic}")
                    continue

                chunks = engine.ingest_text(text, metadata={"topic": topic, "url": url})
                logging.info(f"[Web] Ingested {chunks} chunks for topic: {topic} | URL: {url}")

            except Exception as e:
                logging.warning(f"[Web] Blocked/skipped: {url} | Error: {e}")

        time.sleep(300)  # repeat every 5 minutes


def start_auto_pipeline(engine):
    """Launch both document and web ingestion threads."""
    logging.info("Auto-pipeline started: PDFs/EPUBs and Web Surfing running in background.")

    threading.Thread(target=auto_ingest_documents, args=(engine,), daemon=True).start()
    threading.Thread(target=auto_web_surf, args=(engine,), daemon=True).start()