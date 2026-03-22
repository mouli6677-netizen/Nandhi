# database/db.py

import sqlite3
import os


class Database:
    def __init__(self, db_path="database/nandi.db"):
        self.db_path = db_path
        # FIX 1: the database directory may not exist yet; sqlite3.connect() will
        # raise OperationalError ("unable to open database file") if the parent
        # directory is missing. Create it first.
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # FIX 2: removed shared self.conn = sqlite3.connect(...). A single shared
        # connection is not thread-safe — concurrent writes from background
        # watcher/ingestion threads cause "ProgrammingError: Recursive use of
        # cursors not allowed" and data corruption. Use per-operation connections.
        self._create_tables()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS structured_memory (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_structured(self, key, value):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO structured_memory (key, value)
            VALUES (?, ?)
        """, (key, value))
        conn.commit()
        conn.close()

    def load_structured(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM structured_memory")
        rows = cursor.fetchall()
        conn.close()
        return dict(rows)