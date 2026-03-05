# core/engine.py

import os
import logging
from llm.ollama_llm import OllamaLLM
from core.memory import PersistentMemory
from PIL import Image
import cv2
import torch
from sentence_transformers import SentenceTransformer

# Optional: Video processing
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None
    logging.warning("moviepy not installed, video analysis disabled.")


class NandhiEngine:
    def __init__(self, model_name="llama3"):
        # LLM
        self.llm = OllamaLLM(model_name)

        # Persistent memory
        self.memory = PersistentMemory()

        # Embedding model for image/video analysis
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # ------------------------------
    # Memory + Context Handling
    # ------------------------------
    def _get_context(self, user_input: str, top_k=5):
        docs = self.memory.search(user_input, top_k=top_k)
        return "\n".join(docs) if docs else ""

    def remember(self, text: str, metadata: dict = None):
        self.memory.add(text, metadata=metadata or {})

    # ------------------------------
    # Chat / LLM Reply
    # ------------------------------
    def generate_reply(self, user_input: str) -> str:
        context = self._get_context(user_input)
        prompt = f"Context:\n{context}\n\nUser: {user_input}\nAssistant:"
        answer = self.llm.generate(prompt)
        self.remember(f"User: {user_input}\nAssistant: {answer}")
        return answer

    # ------------------------------
    # Media Analysis
    # ------------------------------
    def analyze_image(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            return f"Image path not found: {image_path}"
        try:
            image = Image.open(image_path)
            # Convert to tensor for embedding
            embedding = self.embedder.encode([image_path])
            self.remember(f"Analyzed image: {image_path}")
            return f"Image analyzed: {image_path}, embedding vector shape: {embedding.shape}"
        except Exception as e:
            logging.error(f"[Engine] Image analysis error: {e}")
            return f"Error analyzing image: {e}"

    def analyze_video(self, video_path: str) -> str:
        if VideoFileClip is None:
            return "Video analysis disabled (moviepy not installed)."
        if not os.path.exists(video_path):
            return f"Video path not found: {video_path}"
        try:
            clip = VideoFileClip(video_path)
            frame_count = int(clip.fps * clip.duration)
            self.remember(f"Analyzed video: {video_path}")
            return f"Video analyzed: {video_path}, frames: {frame_count}, duration: {clip.duration:.2f}s"
        except Exception as e:
            logging.error(f"[Engine] Video analysis error: {e}")
            return f"Error analyzing video: {e}"

    # ------------------------------
    # Utility
    # ------------------------------
    def memory_count(self) -> int:
        return self.memory.count()