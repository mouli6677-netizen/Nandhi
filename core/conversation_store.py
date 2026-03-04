# core/conversation_store.py

import sqlite3
import uuid
from datetime import datetime


class ConversationStore:
    def __init__(self, db_path="database/nandi.db"):
        self.db_path = db_path
        self._initialize_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        conn = self._connect()
        cursor = conn.cursor()

        # Conversations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            title TEXT
        )
        """)

        # Messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )
        """)

        conn.commit()
        conn.close()

    # Create new conversation
    def create_conversation(self, title="New Session"):
        conversation_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO conversations (id, created_at, title)
        VALUES (?, ?, ?)
        """, (conversation_id, created_at, title))

        conn.commit()
        conn.close()

        return conversation_id

    # Save message
    def save_message(self, conversation_id, role, content):
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO messages (id, conversation_id, role, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """, (message_id, conversation_id, role, content, timestamp))

        conn.commit()
        conn.close()

    # Get conversation history
    def get_messages(self, conversation_id):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT role, content FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
        """, (conversation_id,))

        messages = cursor.fetchall()
        conn.close()

        return messages

    # List all conversations
    def list_conversations(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id, created_at, title FROM conversations
        ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return rows