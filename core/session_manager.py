# core/session_manager.py

import os
import json
import threading
from collections import deque

class SessionManager:
    def __init__(self, session_file="session_history.json", max_messages=50):
        self.session_file = session_file
        self._lock = threading.Lock()
        self.max_messages = max_messages

        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = deque(data, maxlen=self.max_messages)
            except Exception:
                self.history = deque(maxlen=self.max_messages)
        else:
            self.history = deque(maxlen=self.max_messages)

    def save_user_message(self, message: str, topic=None):
        with self._lock:
            self.history.append({"role": "user", "content": message, "topic": topic})
            self._save_to_file()

    def save_ai_message(self, message: str, topic=None):
        with self._lock:
            self.history.append({"role": "assistant", "content": message, "topic": topic})
            self._save_to_file()

    def get_conversation_history(self, topic=None):
        with self._lock:
            if topic:
                return [m for m in self.history if m.get("topic") == topic]
            return list(self.history)

    # FIX: added get_context() as alias so any caller using either name works
    def get_context(self, topic=None):
        return self.get_conversation_history(topic=topic)

    def _save_to_file(self):
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(list(self.history), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Session save error: {e}")
