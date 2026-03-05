# watcher/watcher.py
# FIX: file was named watcher.py.py (double extension) — renamed to watcher.py

import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

INGEST_EXTENSIONS = [".pdf", ".epub"]


class KnowledgeHandler(FileSystemEventHandler):
    def __init__(self, engine):
        self.engine = engine
        self.processed_files = set()

    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        ext = os.path.splitext(filepath)[1].lower()
        if ext in INGEST_EXTENSIONS and filepath not in self.processed_files:
            self.processed_files.add(filepath)
            print(f"\n[Watcher] New file detected: {filepath}")
            try:
                if ext == ".pdf":
                    num_chunks = self.engine.ingest_pdf(filepath)
                    print(f"[Watcher] Indexed {num_chunks} chunks from PDF.")
                elif ext == ".epub":
                    num_chunks = self.engine.ingest_epub(filepath)
                    print(f"[Watcher] Indexed {num_chunks} chunks from EPUB.")
            except Exception as e:
                print(f"[Watcher] Failed to ingest {filepath}: {e}")


def start_watcher(engine, folder="Knowledge"):
    folder = os.path.abspath(folder)
    print(f"[Watcher] Monitoring folder: {folder}")
    event_handler = KnowledgeHandler(engine)
    observer = Observer()
    observer.schedule(event_handler, folder, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
