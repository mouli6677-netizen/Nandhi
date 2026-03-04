# watcher/file_watcher.py

import os
import time
import logging
import threading
import random

# Optional: for web scraping / trending topics
import requests
from bs4 import BeautifulSoup

from core.engine import NandhiEngine

# ----------------------------
# CONFIG
# ----------------------------
KNOWLEDGE_DIR = "Knowledge"  # folder for PDFs and EPUBs
WEB_SURF_INTERVAL = 300      # seconds between web surf cycles
AUTO_INGEST_INTERVAL = 60    # seconds between checking new files

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def find_files(folder, extensions=(".pdf", ".epub")):
    """Return list of file paths with given extensions."""
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            if f.lower().endswith(extensions):
                files.append(os.path.join(root, f))
    return files

def get_trending_topics():
    """Fetch trending topics from a public source or generate AI-suggested topics."""
    # Placeholder: we use Bing trending topics
    try:
        url = "https://www.bing.com/news/trendingtopics"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        topics = [t.get_text() for t in soup.find_all("a")][:5]  # top 5
        return topics if topics else ["technology", "science", "finance"]
    except Exception:
        return ["technology", "science", "finance"]

def auto_ingest(engine: NandhiEngine):
    """Automatically ingest new PDFs/EPUBs in Knowledge folder."""
    while True:
        try:
            files = find_files(KNOWLEDGE_DIR)
            for file_path in files:
                if not engine.vector_store.exists(file_path):
                    logging.info(f"Auto-ingest: {file_path}")
                    try:
                        if file_path.endswith(".pdf"):
                            chunks = engine.ingest_pdf(file_path)
                        elif file_path.endswith(".epub"):
                            chunks = engine.ingest_epub(file_path)
                        logging.info(f"Ingested {chunks} chunks from {file_path}")
                    except Exception as e:
                        logging.error(f"Auto-ingest error: {e}")
        except Exception as e:
            logging.error(f"Auto-ingest loop error: {e}")

        time.sleep(AUTO_INGEST_INTERVAL)

def auto_web_surf(engine: NandhiEngine):
    """Automatically fetch content from trending topics."""
    while True:
        try:
            topics = get_trending_topics()
            topic = random.choice(topics)
            logging.info(f"Auto web surf: fetching content for topic '{topic}'")

            # Example: fetch Wikipedia page
            wiki_url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
            if not engine.vector_store.exists(wiki_url):
                try:
                    r = requests.get(wiki_url, timeout=10)
                    if r.status_code == 200:
                        content = BeautifulSoup(r.text, "html.parser").get_text()
                        engine.ingest_web(wiki_url)
                        logging.info(f"Auto web surf: ingested {wiki_url}")
                except Exception as e:
                    logging.error(f"Auto web surf error: {e}")

        except Exception as e:
            logging.error(f"Auto web surf loop error: {e}")

        time.sleep(WEB_SURF_INTERVAL)

# ----------------------------
# START WATCHER
# ----------------------------
def start_watcher(engine: NandhiEngine):
    """Start background threads for auto ingestion and web surfing."""
    ingest_thread = threading.Thread(target=auto_ingest, args=(engine,), daemon=True)
    web_thread = threading.Thread(target=auto_web_surf, args=(engine,), daemon=True)

    ingest_thread.start()
    web_thread.start()

    logging.info("Nandhi auto-ingest and web-surf threads started.")