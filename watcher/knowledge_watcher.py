# watcher/knowledge_watcher.py

import os
import time
import logging
import threading

from ingestion.pdf_loader import PDFLoader
from ingestion.epub_loader import EPUBLoader


# FIX: This file previously contained a raw GitHub 404 HTML error page instead
# of any Python code. Replaced with a functional knowledge watcher that polls
# the Knowledge directory and ingests new PDF/EPUB files via the engine.

KNOWLEDGE_DIR = "Knowledge"
POLL_INTERVAL = 60  # seconds between scans


class KnowledgeWatcher:
    """
    Polls KNOWLEDGE_DIR for new PDF/EPUB files and ingests them into the
    engine's vector store.  Uses a simple seen-set so files are only
    processed once per process lifetime (the vector_store.exists() check
    provides cross-session deduplication).
    """

    def __init__(self, engine):
        self.engine = engine
        self._seen: set = set()
        self._stop_event = threading.Event()

    def _scan(self):
        knowledge_path = os.path.abspath(KNOWLEDGE_DIR)
        os.makedirs(knowledge_path, exist_ok=True)

        for root, _, files in os.walk(knowledge_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1].lower()

                if ext not in (".pdf", ".epub"):
                    continue
                if fpath in self._seen:
                    continue
                if self.engine.vector_store.exists(fpath):
                    self._seen.add(fpath)
                    continue

                self._seen.add(fpath)
                try:
                    if ext == ".pdf":
                        chunks = self.engine.ingest_pdf(fpath)
                    else:
                        chunks = self.engine.ingest_epub(fpath)
                    logging.info(f"[KnowledgeWatcher] Ingested {chunks} chunks from {fname}")
                except Exception as e:
                    logging.error(f"[KnowledgeWatcher] Error ingesting {fpath}: {e}")

    def _run(self):
        logging.info("[KnowledgeWatcher] Started.")
        while not self._stop_event.is_set():
            try:
                self._scan()
            except Exception as e:
                logging.error(f"[KnowledgeWatcher] Scan error: {e}")
            self._stop_event.wait(POLL_INTERVAL)

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        return t

    def stop(self):
        self._stop_event.set()


def start_knowledge_watcher(engine):
    """Convenience function — start the watcher and return the thread."""
    watcher = KnowledgeWatcher(engine)
    return watcher.start()
