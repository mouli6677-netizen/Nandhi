class ShortTermMemory:
    def __init__(self, limit=20):
        self.limit = limit
        self.buffer = []

    def add(self, message):
        self.buffer.append(message)
        if len(self.buffer) > self.limit:
            self.buffer.pop(0)

    def get(self):
        return self.buffer