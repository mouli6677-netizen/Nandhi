import sqlite3
import os


class Database:
    def __init__(self, db_path="database/nandi.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS structured_memory (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.conn.commit()

    def save_structured(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO structured_memory (key, value)
            VALUES (?, ?)
        """, (key, value))
        self.conn.commit()

    def load_structured(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM structured_memory")
        rows = cursor.fetchall()
        return dict(rows)