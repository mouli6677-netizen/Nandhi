# watcher/file_watcher.py
# FIX: file was named fille_watcher.py (typo) — renamed to file_watcher.py

import os
import time
import logging
import threading
import random

import requests
from bs4 import BeautifulSoup

from core.engine import NandhiEngine

# ----------------------------
# CONFIG
# ----------------------------
KNOWLEDGE_DIR = "Knowledge"
WEB_SURF_INTERVAL = 300
AUTO_INGEST_INTERVAL = 60

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def find_files(folder, extensions=(".pdf", ".epub")):
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            if f.lower().endswith(extensions):
                files.append(os.path.join(root, f))
    return files


def get_trending_topics():
    try:
        url = "https://www.bing.com/news/trendingtopics"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        topics = [t.get_text() for t in soup.find_all("a")][:5]
        return topics if topics else ["technology", "science", "finance"]
    except Exception:
        return ["technology", "science", "finance"]


def auto_ingest(engine: NandhiEngine):
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
    while True:
        try:
            topics = get_trending_topics()
            topic = random.choice(topics)
            logging.info(f"Auto web surf: fetching content for topic '{topic}'")

            wiki_url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
            if not engine.vector_store.exists(wiki_url):
                try:
                    r = requests.get(wiki_url, timeout=10)
                    if r.status_code == 200:
                        # FIX: original scraped page content into `content` variable
                        # but then called engine.ingest_web(wiki_url) which re-fetches
                        # the same URL, making the scraping here pointless and doubling
                        # the HTTP request. Use engine.ingest_text() with the already-
                        # fetched content instead to avoid the redundant request.
                        content = BeautifulSoup(r.text, "html.parser").get_text()
                        chunks = engine.ingest_text(
                            content,
                            metadata={"url": wiki_url, "source": wiki_url, "topic": topic}
                        )
                        logging.info(f"Auto web surf: ingested {chunks} chunks from {wiki_url}")
                except Exception as e:
                    logging.error(f"Auto web surf error: {e}")

        except Exception as e:
            logging.error(f"Auto web surf loop error: {e}")

        time.sleep(WEB_SURF_INTERVAL)


def start_watcher(engine: NandhiEngine):
    ingest_thread = threading.Thread(target=auto_ingest, args=(engine,), daemon=True)
    web_thread = threading.Thread(target=auto_web_surf, args=(engine,), daemon=True)
    ingest_thread.start()
    web_thread.start()
    logging.info("Nandhi auto-ingest and web-surf threads started.")