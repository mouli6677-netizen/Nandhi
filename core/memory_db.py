import sqlite3
from datetime import datetime


class MemoryDB:
    def __init__(self, db_path="nandhi_memory.db"):
        self.db_path = db_path
        self._create_table()

    # FIX: connect per operation instead of storing a single shared connection
    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save_message(self, conversation_id: str, role: str, content: str):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (conversation_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (conversation_id, role, content, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

    def load_recent(self, conversation_id: str, limit=20):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM conversations
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (conversation_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return list(reversed(rows))
