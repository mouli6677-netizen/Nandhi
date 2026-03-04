import requests
from bs4 import BeautifulSoup

def fetch_web_content(query, max_paragraphs=5):
    """
    Searches the web for the query and extracts textual content.
    Returns a clean string suitable for ingestion.
    """
    try:
        # Using DuckDuckGo instant answers for simplicity (no API key)
        url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text() for p in paragraphs[:max_paragraphs]])
        return content.strip()

    except Exception as e:
        print(f"Web fetcher error for query '{query}': {e}")
        return ""