import requests
from bs4 import BeautifulSoup
from memory.chunker import chunk_text
import logging

class WebLoader:
    TOPIC_URLS = {
        "technology": "https://www.techcrunch.com/",
        "AI": "https://blog.google/innovation-and-ai/technology/ai/",
        "science": "https://www.sciencedaily.com/",
        "finance": "https://www.bloomberg.com/asia",
        "health": "https://www.medicalnewstoday.com/"
    }

    def __init__(self, vector_store):
        self.vector_store = vector_store

    def load(self, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch webpage: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def ingest(self, url: str, user_id="default") -> int:
        try:
            text = self.load(url)
            chunks = chunk_text(text)
            for chunk in chunks:
                self.vector_store.add(chunk, metadata={"url": url, "topic": self._get_topic(url)})
            logging.info(f"WebLoader: {len(chunks)} chunks ingested for URL: {url}")
            return len(chunks)
        except Exception as e:
            logging.warning(f"WebLoader blocked/skipped: {url} | Error: {e}")
            return 0

    def _get_topic(self, url):
        for topic, t_url in self.TOPIC_URLS.items():
            if t_url == url:
                return topic
        return "unknown"