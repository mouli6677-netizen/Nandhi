import re

class MemoryExtractor:
    def __init__(self, db):
        self.db = db

    def extract(self, text):
        text = text.lower()

        name_match = re.search(r"my name is (.+)", text)
        if name_match:
            self.db.save_structured("user_name", name_match.group(1).title())

        location_match = re.search(r"i live in (.+)", text)
        if location_match:
            self.db.save_structured("location", location_match.group(1).title())

        job_match = re.search(r"i am a (.+)", text)
        if job_match:
            self.db.save_structured("profession", job_match.group(1).title())