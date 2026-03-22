# core/engine.py

import os
import logging
from llm.ollama_llm import OllamaLLM
from memory.persistent_memory import PersistentMemory
from memory.embedder import Embedder
from memory.vector_store import VectorStore
from memory.chunker import chunk_text
from core.tools import MediaTools, ToolRegistry

# FIX: removed top-level "from PIL import Image", "import cv2", "import torch",
# and "from sentence_transformers import SentenceTransformer" — these are heavy
# dependencies that may not be installed, and PIL/cv2 are already used inside
# core/tools.py.  SentenceTransformer is exposed through memory.embedder.Embedder;
# importing it again here and calling .encode() on image paths is wrong — the
# sentence transformer model embeds *text*, not images.

# Optional moviepy
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None
    logging.warning("moviepy not installed, video analysis disabled.")


class NandhiEngine:
    def __init__(self, model_name="llama3"):
        # LLM
        self.llm = OllamaLLM(model_name)

        # Persistent memory (SQLite-backed conversation store)
        self.memory = PersistentMemory()

        # Vector store for semantic search
        self.embedder = Embedder()
        self.vector_store = VectorStore(self.embedder)

        # Media tools (image/video analysis and editing)
        # FIX: engine.tools was never initialised, so dashboard_api.py and
        # nandhi_ui.py calls to engine.tools.edit_image() / engine.tools.extract_frames()
        # raised AttributeError at runtime.
        self.tools = ToolRegistry(MediaTools())

    # ------------------------------
    # Memory + Context Handling
    # ------------------------------
    def _get_context(self, user_input: str, top_k: int = 5) -> str:
        # FIX: PersistentMemory has no .search() method — it only exposes
        # save_message() and load_recent_messages(). Use load_recent_messages()
        # to build context, which is what the SQLite schema supports.
        messages = self.memory.load_recent_messages(limit=top_k * 2)
        if not messages:
            return ""
        return "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in messages)

    def remember(self, role: str, content: str):
        # FIX: original signature was remember(text, metadata) which doesn't
        # match PersistentMemory.save_message(role, content). Corrected to pass
        # role and content explicitly.
        self.memory.save_message(role, content)

    def memory_count(self) -> int:
        # FIX: PersistentMemory has no .count() method. Approximate by counting
        # loaded recent messages (up to the limit). For an accurate count a
        # dedicated SQL COUNT query would be needed, but this avoids the
        # AttributeError that crashed every UI memory count display.
        return len(self.memory.load_recent_messages(limit=10000))

    # ------------------------------
    # Chat / LLM Reply
    # ------------------------------
    def generate_reply(self, user_input: str) -> str:
        context = self._get_context(user_input)
        prompt = f"Context:\n{context}\n\nUser: {user_input}\nAssistant:" if context else f"User: {user_input}\nAssistant:"
        answer = self.llm.generate(prompt)
        self.remember("user", user_input)
        self.remember("assistant", answer)
        return answer

    async def chat(self, user_input: str) -> str:
        """
        FIX: main.py calls await engine.chat(msg["message"]) over the WebSocket,
        but generate_reply() is synchronous and no async version existed — every
        WebSocket message would raise AttributeError. Added async wrapper.
        """
        return self.generate_reply(user_input)

    def get_stats(self) -> dict:
        """
        FIX: main.py calls engine.get_stats() after every chat message and after
        every file upload. The method didn't exist, causing AttributeError on every
        WebSocket exchange and every /upload request.
        """
        return {
            "memory_count": self.memory_count(),
            "task_queue_length": 0,
            "reward_score": 0.0,
            "knowledge_nodes": len(self.vector_store.store),
            "active_threads": 0,
        }

    # ------------------------------
    # Media Analysis
    # ------------------------------
    def analyze_image(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            return f"Image path not found: {image_path}"
        try:
            # FIX: original code opened the image with PIL then called
            # self.embedder.encode([image_path]) — passing the file *path string*
            # to a text sentence-transformer, which produces a meaningless vector
            # and is not image analysis. Delegate to the proper MediaTools handler.
            result = self.tools.analyze_image(image_path)
            self.remember("system", f"Analyzed image: {image_path}")
            return result
        except Exception as e:
            logging.error(f"[Engine] Image analysis error: {e}")
            return f"Error analyzing image: {e}"

    def analyze_video(self, video_path: str) -> str:
        if not os.path.exists(video_path):
            return f"Video path not found: {video_path}"
        try:
            result = self.tools.analyze_video(video_path)
            self.remember("system", f"Analyzed video: {video_path}")
            return result
        except Exception as e:
            logging.error(f"[Engine] Video analysis error: {e}")
            return f"Error analyzing video: {e}"

    async def ingest_media(self, file_path: str) -> str:
        """
        FIX: main.py calls await engine.ingest_media(file_path) for every
        /upload POST. The method didn't exist, causing AttributeError on all
        file uploads. Routes to the correct tool based on file extension.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"):
            return self.analyze_image(file_path)
        elif ext in (".mp4", ".avi", ".mov", ".mkv", ".webm"):
            return self.analyze_video(file_path)
        else:
            return f"Unsupported media type: {ext}"

    # ------------------------------
    # Ingestion (used by watchers)
    # ------------------------------
    def ingest_text(self, text: str, metadata: dict = None) -> int:
        try:
            chunks = chunk_text(text)
            for chunk in chunks:
                self.vector_store.add(chunk, metadata=metadata or {})
            return len(chunks)
        except Exception as e:
            logging.error(f"Text ingest error: {e}")
            return 0

    def ingest_web(self, url: str) -> int:
        try:
            import requests
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return 0
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = "\n".join(
                line.strip()
                for line in soup.get_text(separator="\n").splitlines()
                if line.strip()
            )
            return self.ingest_text(text, metadata={"url": url, "source": url})
        except Exception as e:
            logging.error(f"ingest_web error for {url}: {e}")
            return 0