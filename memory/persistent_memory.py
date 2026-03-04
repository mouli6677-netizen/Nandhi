import sqlite3
import uuid
from datetime import datetime


class PersistentMemory:
    def __init__(self, db_path="nandhi.db"):
        self.db_path = db_path
        self._create_tables()
        self.conversation_id = self._create_conversation()

    # FIX: removed shared self.conn/self.cursor — connect per operation (thread-safe)
    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT
        )
        """)
        conn.commit()
        conn.close()

    def _create_conversation(self):
        conversation_id = str(uuid.uuid4())
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (id, created_at) VALUES (?, ?)",
            (conversation_id, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
        return conversation_id

    def save_message(self, role, content):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (self.conversation_id, role, content, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    def load_recent_messages(self, limit=20):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (self.conversation_id, limit))
        rows = cursor.fetchall()
        conn.close()
        rows.reverse()
        return [{"role": r[0], "content": r[1]} for r in rows]
